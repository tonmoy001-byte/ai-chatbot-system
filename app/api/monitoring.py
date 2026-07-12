from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import psutil
import os

from app.database import get_db
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with component status."""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "components": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # System metrics
    health["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else 0
    }
    
    return health


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get application metrics."""
    from sqlalchemy import func
    from app.models.conversation import Conversation, Message
    from app.models.customer import Customer
    
    # Get counts
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    
    # Get active conversations
    active_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.status == "active"
    ).scalar() or 0
    
    # Get today's stats
    today = datetime.utcnow().date()
    today_messages = db.query(func.count(Message.id)).filter(
        func.date(Message.created_at) == today
    ).scalar() or 0
    
    today_conversations = db.query(func.count(Conversation.id)).filter(
        func.date(Conversation.started_at) == today
    ).scalar() or 0
    
    return {
        "customers": {"total": total_customers},
        "conversations": {
            "total": total_conversations,
            "active": active_conversations,
            "today": today_conversations
        },
        "messages": {
            "total": total_messages,
            "today": today_messages
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
