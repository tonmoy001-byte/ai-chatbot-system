from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Callable
import re

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries
        current_time = time.time()
        self.requests = {
            ip: [t for t in times if current_time - t < self.window_seconds]
            for ip, times in self.requests.items()
        }
        
        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json"
                )
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        response = await call_next(request)
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Input sanitization middleware."""
    
    # Patterns to detect potential attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
        r"(--|;|'|\"|\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(UNION\s+SELECT)",
        r"(DROP\s+TABLE)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore")
            
            # Check for SQL injection
            for pattern in self.sql_patterns:
                if pattern.search(body_str):
                    logger.warning(f"Potential SQL injection detected from {request.client.host}")
                    return Response(
                        content='{"error": "Invalid input detected"}',
                        status_code=400,
                        media_type="application/json"
                    )
            
            # Check for XSS
            for pattern in self.xss_patterns:
                if pattern.search(body_str):
                    logger.warning(f"Potential XSS attack detected from {request.client.host}")
                    return Response(
                        content='{"error": "Invalid input detected"}',
                        status_code=400,
                        media_type="application/json"
                    )
        
        response = await call_next(request)
        return response


def setup_security_middleware(app: FastAPI):
    """Setup all security middleware."""
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    app.add_middleware(SecurityMiddleware)
    
    logger.info("Security middleware configured")
