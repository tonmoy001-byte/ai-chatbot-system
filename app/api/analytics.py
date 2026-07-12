from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics."""
    analytics = AnalyticsService(db)
    stats = await analytics.get_dashboard_stats()
    return stats


@router.get("/conversations")
async def get_conversation_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get conversation analytics for a date range."""
    analytics = AnalyticsService(db)
    
    # Parse dates
    start = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=30)
    end = date.fromisoformat(end_date) if end_date else date.today()
    
    stats = await analytics.get_conversation_analytics(start, end)
    return stats


@router.get("/messages")
async def get_message_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get message analytics."""
    analytics = AnalyticsService(db)
    
    start = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=30)
    end = date.fromisoformat(end_date) if end_date else date.today()
    
    stats = await analytics.get_message_analytics(start, end)
    return stats


@router.get("/orders")
async def get_order_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get order analytics."""
    analytics = AnalyticsService(db)
    
    start = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=30)
    end = date.fromisoformat(end_date) if end_date else date.today()
    
    stats = await analytics.get_order_analytics(start, end)
    return stats


@router.get("/peak-hours")
async def get_peak_hours(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get peak hours for conversations."""
    analytics = AnalyticsService(db)
    peak_hours = await analytics.get_peak_hours(days)
    return {"peak_hours": peak_hours}


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(10, description="Number of items to return"),
    db: Session = Depends(get_db)
):
    """Get recent activity feed."""
    analytics = AnalyticsService(db)
    activity = await analytics.get_recent_activity(limit)
    return {"activity": activity}
