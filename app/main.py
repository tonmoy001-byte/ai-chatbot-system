from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import json
from typing import Dict, Set

from app.config import get_settings
from app.database import engine, Base
from app.logging_config import setup_logging
from app.errors import setup_error_handlers
from app.cache import cache
from app.api.webhooks import router as webhooks_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.bookings import router as bookings_router
from app.api.calendar import router as calendar_router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.monitoring import router as monitoring_router
from app.api.analytics import router as analytics_router
from app.middleware.security import setup_security_middleware
from app.monitoring.performance import PerformanceMiddleware, get_metrics

settings = get_settings()

# Setup logging
setup_logging()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        self.active_connections[conversation_id].add(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def send_message(self, message: dict, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered chatbot system for automated customer service across Facebook and Instagram",
    lifespan=lifespan
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
setup_security_middleware(app)

# Performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

# Error handlers
setup_error_handlers(app)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(orders_router)
app.include_router(products_router)
app.include_router(bookings_router)
app.include_router(calendar_router)
app.include_router(admin_router)
app.include_router(monitoring_router)
app.include_router(analytics_router)


# WebSocket endpoint
@app.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "cache_status": "connected" if cache.enabled else "disabled"
    }


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "AI Chatbot System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(get_metrics())
