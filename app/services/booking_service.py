from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import uuid
import logging

from app.models.booking import Booking
from app.models.customer import Customer
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        return self.db.query(Booking).filter(
            Booking.id == booking_id
        ).first()
    
    async def get_booking_by_event_id(self, event_id: str) -> Optional[Booking]:
        """Get booking by calendar event ID."""
        return self.db.query(Booking).filter(
            Booking.event_id == event_id
        ).first()
    
    async def get_customer_bookings(
        self,
        customer_id: str,
        include_past: bool = False
    ) -> List[Booking]:
        """Get all bookings for a customer."""
        query = self.db.query(Booking).filter(
            Booking.customer_id == customer_id
        )
        
        if not include_past:
            query = query.filter(Booking.start_time > datetime.utcnow())
        
        return query.order_by(Booking.start_time).all()
    
    async def get_upcoming_bookings(
        self,
        days: int = 7
    ) -> List[Booking]:
        """Get all upcoming bookings."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        
        return self.db.query(Booking).filter(
            Booking.start_time >= start_date,
            Booking.start_time <= end_date,
            Booking.status == "confirmed"
        ).order_by(Booking.start_time).all()
    
    async def create_booking(
        self,
        customer_id: str,
        start_time: datetime,
        duration_minutes: int = 30,
        service_name: str = "Appointment",
        description: str = "",
        calendar_service: Optional[CalendarService] = None
    ) -> Optional[Booking]:
        """Create a new booking."""
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Create calendar event if calendar service is available
        event_id = None
        calendar_id = None
        
        if calendar_service:
            try:
                # Get customer info for the event
                customer = self.db.query(Customer).filter(
                    Customer.id == customer_id
                ).first()
                
                attendee_email = customer.email if customer else None
                
                event = await calendar_service.create_event(
                    summary=f"{service_name} - Customer {str(customer_id)[:8]}",
                    start_time=start_time,
                    duration_minutes=duration_minutes,
                    description=description,
                    attendee_email=attendee_email
                )
                
                if event:
                    event_id = event.get('id')
                    calendar_id = 'primary'
                    
                    # Add reminder to the event
                    await calendar_service.add_reminder(event_id, minutes_before=30)
            except Exception as e:
                logger.error(f"Failed to create calendar event: {str(e)}")
        
        # Create booking record
        booking = Booking(
            id=uuid.uuid4(),
            customer_id=customer_id,
            calendar_id=calendar_id,
            event_id=event_id,
            start_time=start_time,
            end_time=end_time,
            status="confirmed"
        )
        
        self.db.add(booking)
        self.db.commit()
        
        logger.info(f"Created booking {booking.id} for customer {customer_id}")
        return booking
    
    async def update_booking(
        self,
        booking_id: str,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        service_name: Optional[str] = None,
        calendar_service: Optional[CalendarService] = None
    ) -> bool:
        """Update an existing booking."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return False
        
        if booking.status == "cancelled":
            raise ValueError("Cannot update cancelled booking")
        
        # Update calendar event if available
        if calendar_service and booking.event_id:
            try:
                update_kwargs = {}
                if start_time:
                    update_kwargs['start_time'] = start_time
                if duration_minutes:
                    update_kwargs['duration_minutes'] = duration_minutes
                if service_name:
                    update_kwargs['summary'] = f"{service_name} - Customer {str(booking.customer_id)[:8]}"
                
                if update_kwargs:
                    await calendar_service.update_event(
                        event_id=booking.event_id,
                        **update_kwargs
                    )
            except Exception as e:
                logger.error(f"Failed to update calendar event: {str(e)}")
        
        # Update booking record
        if start_time:
            booking.start_time = start_time
            if duration_minutes:
                booking.end_time = start_time + timedelta(minutes=duration_minutes)
        elif duration_minutes:
            booking.end_time = booking.start_time + timedelta(minutes=duration_minutes)
        
        self.db.commit()
        
        logger.info(f"Updated booking {booking_id}")
        return True
    
    async def cancel_booking(
        self,
        booking_id: str,
        reason: Optional[str] = None,
        calendar_service: Optional[CalendarService] = None
    ) -> bool:
        """Cancel a booking."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return False
        
        if booking.status == "cancelled":
            raise ValueError("Booking is already cancelled")
        
        # Delete calendar event if available
        if calendar_service and booking.event_id:
            try:
                await calendar_service.delete_event(booking.event_id)
            except Exception as e:
                logger.error(f"Failed to delete calendar event: {str(e)}")
        
        # Update booking status
        booking.status = "cancelled"
        self.db.commit()
        
        logger.info(f"Cancelled booking {booking_id}: {reason}")
        return True
    
    async def reschedule_booking(
        self,
        booking_id: str,
        new_start_time: datetime,
        duration_minutes: Optional[int] = None,
        calendar_service: Optional[CalendarService] = None
    ) -> Optional[Booking]:
        """Reschedule a booking to a new time."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return None
        
        if booking.status == "cancelled":
            raise ValueError("Cannot reschedule cancelled booking")
        
        # Calculate new end time
        if duration_minutes:
            new_end_time = new_start_time + timedelta(minutes=duration_minutes)
        else:
            # Use original duration
            original_duration = (booking.end_time - booking.start_time).total_seconds() / 60
            new_end_time = new_start_time + timedelta(minutes=original_duration)
        
        # Update calendar event
        if calendar_service and booking.event_id:
            try:
                await calendar_service.update_event(
                    event_id=booking.event_id,
                    start_time=new_start_time,
                    duration_minutes=int((new_end_time - new_start_time).total_seconds() / 60)
                )
            except Exception as e:
                logger.error(f"Failed to update calendar event: {str(e)}")
        
        # Update booking
        booking.start_time = new_start_time
        booking.end_time = new_end_time
        self.db.commit()
        
        logger.info(f"Rescheduled booking {booking_id} to {new_start_time}")
        return booking
    
    async def mark_reminder_sent(self, booking_id: str) -> bool:
        """Mark booking reminder as sent."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return False
        
        booking.reminder_sent = True
        self.db.commit()
        
        return True
    
    async def get_bookings_needing_reminder(self) -> List[Booking]:
        """Get bookings that need reminders sent."""
        # Get bookings in the next 24 hours that haven't had reminders sent
        now = datetime.utcnow()
        reminder_window = now + timedelta(hours=24)
        
        return self.db.query(Booking).filter(
            Booking.start_time > now,
            Booking.start_time <= reminder_window,
            Booking.status == "confirmed",
            Booking.reminder_sent == False
        ).all()
    
    async def format_booking_confirmation(self, booking: Booking) -> str:
        """Generate customer-friendly booking confirmation."""
        start_time_str = booking.start_time.strftime("%A, %B %d at %I:%M %p")
        
        return (
            f"Booking Confirmed! 📅\n\n"
            f"Date: {start_time_str}\n"
            f"Duration: {(booking.end_time - booking.start_time).seconds // 60} minutes\n"
            f"Booking ID: {str(booking.id)[:8]}\n\n"
            f"You'll receive a reminder 30 minutes before your appointment.\n"
            f"To reschedule or cancel, please provide your booking ID."
        )
    
    async def format_booking_details(self, booking: Booking) -> str:
        """Generate detailed booking information."""
        start_time_str = booking.start_time.strftime("%A, %B %d at %I:%M %p")
        end_time_str = booking.end_time.strftime("%I:%M %p")
        
        return (
            f"Booking Details\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Booking ID: {str(booking.id)[:8]}\n"
            f"Status: {booking.status.capitalize()}\n"
            f"Date: {start_time_str}\n"
            f"Time: {start_time_str} - {end_time_str}\n"
            f"Duration: {(booking.end_time - booking.start_time).seconds // 60} minutes\n"
        )
