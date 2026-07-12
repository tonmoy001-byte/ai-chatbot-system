import time
import logging
from functools import wraps
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

CONVERSATION_COUNT = Counter(
    'conversations_total',
    'Total conversations',
    ['platform', 'status']
)

MESSAGE_COUNT = Counter(
    'messages_total',
    'Total messages processed',
    ['platform', 'message_type']
)

AI_RESPONSE_TIME = Histogram(
    'ai_response_time_seconds',
    'AI response generation time',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

ORDER_COUNT = Counter(
    'orders_total',
    'Total orders created',
    ['status']
)

BOOKING_COUNT = Counter(
    'bookings_total',
    'Total bookings created',
    ['status']
)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request performance."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        start_time = time.time()
        ACTIVE_CONNECTIONS.inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            process_time = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(process_time)
            
            return response
        except Exception as e:
            # Record error
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            raise
        finally:
            ACTIVE_CONNECTIONS.dec()


def track_conversation(platform: str, status: str = "started"):
    """Track conversation metrics."""
    CONVERSATION_COUNT.labels(platform=platform, status=status).inc()


def track_message(platform: str, message_type: str = "text"):
    """Track message metrics."""
    MESSAGE_COUNT.labels(platform=platform, message_type=message_type).inc()


def track_order(status: str = "created"):
    """Track order metrics."""
    ORDER_COUNT.labels(status=status).inc()


def track_booking(status: str = "created"):
    """Track booking metrics."""
    BOOKING_COUNT.labels(status=status).inc()


def time_ai_response(func: Callable) -> Callable:
    """Decorator to track AI response time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            AI_RESPONSE_TIME.observe(duration)
    return wrapper


def get_metrics() -> str:
    """Get Prometheus metrics."""
    return generate_latest().decode("utf-8")


class PerformanceMonitor:
    """Performance monitoring utility."""
    
    @staticmethod
    def log_slow_requests(threshold_seconds: float = 1.0):
        """Log requests that exceed the threshold."""
        # This would be integrated with the performance middleware
        pass
    
    @staticmethod
    def get_performance_summary() -> dict:
        """Get performance summary."""
        return {
            "total_requests": REQUEST_COUNT._value.get(),
            "average_latency": REQUEST_LATENCY._sum.get() / max(REQUEST_LATENCY._count.get(), 1),
            "active_connections": ACTIVE_CONNECTIONS._value.get()
        }
