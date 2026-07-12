from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ChatbotException(Exception):
    """Base exception for chatbot system."""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status_code: int = 500, details: Any = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ConversationNotFoundError(ChatbotException):
    """Conversation not found."""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation {conversation_id} not found",
            code="CONVERSATION_NOT_FOUND",
            status_code=404
        )


class OrderNotFoundError(ChatbotException):
    """Order not found."""
    
    def __init__(self, order_number: str):
        super().__init__(
            message=f"Order {order_number} not found",
            code="ORDER_NOT_FOUND",
            status_code=404
        )


class ProductNotFoundError(ChatbotException):
    """Product not found."""
    
    def __init__(self, product_id: str):
        super().__init__(
            message=f"Product {product_id} not found",
            code="PRODUCT_NOT_FOUND",
            status_code=404
        )


class BookingNotFoundError(ChatbotException):
    """Booking not found."""
    
    def __init__(self, booking_id: str):
        super().__init__(
            message=f"Booking {booking_id} not found",
            code="BOOKING_NOT_FOUND",
            status_code=404
        )


class WebhookVerificationError(ChatbotException):
    """Webhook verification failed."""
    
    def __init__(self, platform: str):
        super().__init__(
            message=f"Webhook verification failed for {platform}",
            code="WEBHOOK_VERIFICATION_FAILED",
            status_code=403
        )


class AIEngineError(ChatbotException):
    """AI engine error."""
    
    def __init__(self, message: str = "AI engine error"):
        super().__init__(
            message=message,
            code="AI_ENGINE_ERROR",
            status_code=503
        )


class ExternalServiceError(ChatbotException):
    """External service error."""
    
    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"Error communicating with {service}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details={"service": service}
        )


class RateLimitError(ChatbotException):
    """Rate limit exceeded."""
    
    def __init__(self):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )


class ValidationError(ChatbotException):
    """Validation error."""
    
    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


def setup_error_handlers(app: FastAPI):
    """Setup error handlers for the FastAPI app."""
    
    @app.exception_handler(ChatbotException)
    async def chatbot_exception_handler(request: Request, exc: ChatbotException):
        logger.error(f"ChatbotException: {exc.code} - {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors}
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred"
                }
            }
        )
