from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import secrets

from app.database import get_db
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CalendarAuthResponse(BaseModel):
    authorization_url: str
    state: str


class CalendarCallbackResponse(BaseModel):
    success: bool
    message: str


@router.get("/auth/url", response_model=CalendarAuthResponse)
async def get_calendar_auth_url():
    """Get Google Calendar OAuth authorization URL."""
    state = secrets.token_urlsafe(32)
    authorization_url = CalendarService.get_authorization_url(state)
    
    return {
        "authorization_url": authorization_url,
        "state": state
    }


@router.get("/callback")
async def calendar_callback(code: str, state: str):
    """Handle Google Calendar OAuth callback."""
    credentials = CalendarService.exchange_code(code)
    
    if not credentials:
        raise HTTPException(status_code=400, detail="Failed to authenticate with Google Calendar")
    
    # In a real app, you would store these credentials associated with the user
    # For now, we'll return a success message
    
    return {
        "success": True,
        "message": "Successfully authenticated with Google Calendar",
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
    }


@router.get("/availability")
async def get_calendar_availability(
    date: str,
    duration_minutes: int = 30,
    start_hour: int = 9,
    end_hour: int = 17
):
    """Get available time slots for a given date."""
    from datetime import date as date_type
    
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # In a real app, you would load the user's credentials
    # For now, we'll return mock data
    from datetime import datetime, timedelta
    
    available_slots = []
    current_hour = start_hour
    
    while current_hour < end_hour:
        slot_time = datetime.combine(target_date, datetime.min.time().replace(hour=current_hour))
        available_slots.append({
            "start_time": slot_time.isoformat(),
            "end_time": (slot_time + timedelta(minutes=duration_minutes)).isoformat(),
            "duration_minutes": duration_minutes
        })
        current_hour += 1
    
    return {
        "date": date,
        "available_slots": available_slots,
        "duration_minutes": duration_minutes
    }


@router.get("/events")
async def list_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """List calendar events."""
    from datetime import date as date_type, timedelta
    
    # Default to next 30 days
    if not start_date:
        start_date = date_type.today().isoformat()
    if not end_date:
        end_date = (date_type.today() + timedelta(days=30)).isoformat()
    
    try:
        start = date_type.fromisoformat(start_date)
        end = date_type.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # In a real app, you would load the user's credentials and fetch events
    # For now, we'll return mock data
    
    return {
        "events": [],
        "start_date": start_date,
        "end_date": end_date
    }
