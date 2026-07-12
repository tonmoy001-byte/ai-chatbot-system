from celery import shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_booking_reminders(self):
    """Send reminders for upcoming bookings."""
    from app.database import SessionLocal
    from app.services.booking_service import BookingService
    
    db = SessionLocal()
    try:
        booking_service = BookingService(db)
        
        # Get bookings needing reminders
        bookings = booking_service.get_bookings_needing_reminder()
        
        for booking in bookings:
            try:
                # Send reminder (would use notification service in production)
                logger.info(f"Sending reminder for booking {booking.id}")
                
                # Mark reminder as sent
                booking_service.mark_reminder_sent(str(booking.id))
                
            except Exception as e:
                logger.error(f"Failed to send reminder for booking {booking.id}: {str(e)}")
                self.retry(exc=exc, countdown=60)
        
        return {"status": "completed", "reminders_sent": len(bookings)}
    finally:
        db.close()


@shared_task
def cleanup_old_bookings(days_old: int = 90):
    """Clean up old bookings."""
    from app.database import SessionLocal
    from sqlalchemy import delete
    from app.models.booking import Booking
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Delete old cancelled bookings
        result = db.execute(
            delete(Booking).where(
                Booking.created_at < cutoff_date,
                Booking.status == "cancelled"
            )
        )
        
        db.commit()
        
        logger.info(f"Cleaned up {result.rowcount} old bookings")
        return {"status": "completed", "deleted": result.rowcount}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cleanup old bookings: {str(e)}")
        raise
    finally:
        db.close()


@shared_task
def check_overdue_bookings():
    """Check for and handle overdue bookings."""
    from app.database import SessionLocal
    from app.services.booking_service import BookingService
    
    db = SessionLocal()
    try:
        booking_service = BookingService(db)
        
        # Get bookings that are past their end time but still marked as confirmed
        now = datetime.utcnow()
        overdue_bookings = db.query(Booking).filter(
            Booking.end_time < now,
            Booking.status == "confirmed"
        ).all()
        
        for booking in overdue_bookings:
            # Mark as completed
            booking.status = "completed"
            logger.info(f"Marked booking {booking.id} as completed (overdue)")
        
        db.commit()
        
        return {"status": "completed", "overdue_bookings": len(overdue_bookings)}
    finally:
        db.close()


@shared_task
def generate_booking_report():
    """Generate daily booking statistics."""
    from app.database import SessionLocal
    from sqlalchemy import func
    from app.models.booking import Booking
    
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        
        # Get today's bookings
        today_bookings = db.query(func.count(Booking.id)).filter(
            func.date(Booking.start_time) == today
        ).scalar() or 0
        
        # Get upcoming bookings
        upcoming = db.query(func.count(Booking.id)).filter(
            Booking.start_time > datetime.utcnow(),
            Booking.status == "confirmed"
        ).scalar() or 0
        
        # Get completed bookings
        completed = db.query(func.count(Booking.id)).filter(
            func.date(Booking.end_time) == today,
            Booking.status == "completed"
        ).scalar() or 0
        
        return {
            "date": today.isoformat(),
            "today_bookings": today_bookings,
            "upcoming_bookings": upcoming,
            "completed_today": completed
        }
    finally:
        db.close()
