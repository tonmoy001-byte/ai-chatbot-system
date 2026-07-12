from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


# Request/Response models
class BookingCreate(BaseModel):
    customer_id: str
    start_time: datetime
    duration_minutes: int = 30
    service_name: str = "Appointment"
    description: str = ""


class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    service_name: Optional[str] = None


class BookingReschedule(BaseModel):
    new_start_time: datetime
    duration_minutes: Optional[int] = None


@router.get("/")
async def list_bookings(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all bookings."""
    booking_service = BookingService(db)
    
    # Get upcoming bookings
    bookings = await booking_service.get_upcoming_bookings(days=30)
    
    # Filter by status if provided
    if status:
        bookings = [b for b in bookings if b.status == status]
    
    return {
        "bookings": [
            {
                "id": str(booking.id),
                "customer_id": str(booking.customer_id),
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "status": booking.status,
                "reminder_sent": booking.reminder_sent,
                "created_at": booking.created_at.isoformat()
            }
            for booking in bookings[offset:offset + limit]
        ],
        "count": len(bookings)
    }


@router.get("/{booking_id}")
async def get_booking(booking_id: str, db: Session = Depends(get_db)):
    """Get booking details."""
    booking_service = BookingService(db)
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "id": str(booking.id),
        "customer_id": str(booking.customer_id),
        "calendar_id": booking.calendar_id,
        "event_id": booking.event_id,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "status": booking.status,
        "reminder_sent": booking.reminder_sent,
        "created_at": booking.created_at.isoformat()
    }


@router.post("/")
async def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    """Create a new booking."""
    booking_service = BookingService(db)
    
    try:
        booking = await booking_service.create_booking(
            customer_id=booking_data.customer_id,
            start_time=booking_data.start_time,
            duration_minutes=booking_data.duration_minutes,
            service_name=booking_data.service_name,
            description=booking_data.description
        )
        
        if not booking:
            raise HTTPException(status_code=400, detail="Failed to create booking")
        
        return {
            "id": str(booking.id),
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "status": booking.status,
            "message": "Booking created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{booking_id}")
async def update_booking(
    booking_id: str,
    update_data: BookingUpdate,
    db: Session = Depends(get_db)
):
    """Update booking details."""
    booking_service = BookingService(db)
    
    try:
        updated = await booking_service.update_booking(
            booking_id=booking_id,
            start_time=update_data.start_time,
            duration_minutes=update_data.duration_minutes,
            service_name=update_data.service_name
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {"message": "Booking updated successfully", "booking_id": booking_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cancel a booking."""
    booking_service = BookingService(db)
    
    try:
        cancelled = await booking_service.cancel_booking(booking_id, reason)
        
        if not cancelled:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {"message": "Booking cancelled successfully", "booking_id": booking_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: str,
    reschedule_data: BookingReschedule,
    db: Session = Depends(get_db)
):
    """Reschedule a booking."""
    booking_service = BookingService(db)
    
    try:
        booking = await booking_service.reschedule_booking(
            booking_id=booking_id,
            new_start_time=reschedule_data.new_start_time,
            duration_minutes=reschedule_data.duration_minutes
        )
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {
            "id": str(booking.id),
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "message": "Booking rescheduled successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customer/{customer_id}")
async def get_customer_bookings(
    customer_id: str,
    include_past: bool = Query(False, description="Include past bookings"),
    db: Session = Depends(get_db)
):
    """Get all bookings for a customer."""
    booking_service = BookingService(db)
    bookings = await booking_service.get_customer_bookings(customer_id, include_past)
    
    return {
        "bookings": [
            {
                "id": str(booking.id),
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "status": booking.status,
                "reminder_sent": booking.reminder_sent
            }
            for booking in bookings
        ],
        "count": len(bookings)
    }
