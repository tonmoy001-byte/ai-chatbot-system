from app.celery import celery_app
from app.config import get_settings
from app.database import SessionLocal

settings = get_settings()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_message_task(self, message_data: dict):
    """Process incoming message from platform."""
    db = SessionLocal()
    try:
        from app.services.message_router import MessageRouter
        
        router = MessageRouter(db)
        
        # Process message synchronously for now
        # In production, this would be async with proper error handling
        import asyncio
        response = asyncio.run(
            router.route_message(
                platform=message_data.get("platform"),
                sender_id=message_data.get("sender_id"),
                message_type=message_data.get("message_type", "text"),
                content=message_data.get("content", ""),
                metadata=message_data.get("metadata")
            )
        )
        
        return {"status": "processed", "response": response}
    except Exception as exc:
        self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_reply_task(self, recipient_id: str, message: dict, platform: str):
    """Send reply message to platform."""
    try:
        if platform == "facebook":
            from app.services.facebook import FacebookService
            service = FacebookService()
        elif platform == "instagram":
            from app.services.instagram import InstagramService
            service = InstagramService()
        else:
            raise ValueError(f"Unknown platform: {platform}")
        
        import asyncio
        result = asyncio.run(service.send_message(recipient_id, message))
        
        return {"status": "sent", "recipient_id": recipient_id, "result": result}
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def process_order_update(order_id: str, status: str):
    """Process order status update and notify customer."""
    db = SessionLocal()
    try:
        from app.services.order_service import OrderService
        from app.services.facebook import FacebookService
        
        order_service = OrderService(db)
        order = order_service.get_order(order_id)
        
        if not order:
            return {"status": "error", "message": "Order not found"}
        
        # Update order status
        order_service.update_status(order.order_number, status)
        
        # TODO: Send notification to customer
        # This would require knowing the customer's platform and ID
        
        return {"status": "processed", "order_id": order_id, "new_status": status}
    except Exception as exc:
        self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_booking_reminder(booking_id: str):
    """Send booking reminder to customer."""
    db = SessionLocal()
    try:
        from app.services.booking_service import BookingService
        
        booking_service = BookingService(db)
        booking = booking_service.get_booking(booking_id)
        
        if not booking:
            return {"status": "error", "message": "Booking not found"}
        
        # Mark reminder as sent
        booking_service.send_reminder(booking_id)
        
        # TODO: Send reminder message to customer
        
        return {"status": "sent", "booking_id": booking_id}
    except Exception as exc:
        self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task
def cleanup_old_conversations(days_old: int = 30):
    """Clean up conversations older than specified days."""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import delete
        from app.models.conversation import Conversation, Message
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Delete old messages
        db.execute(
            delete(Message).where(Message.created_at < cutoff_date)
        )
        
        # Delete old conversations
        db.execute(
            delete(Conversation).where(Conversation.started_at < cutoff_date)
        )
        
        db.commit()
        
        return {"status": "completed", "cutoff_date": cutoff_date.isoformat()}
    except Exception as exc:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task
def sync_product_catalog():
    """Sync product catalog from external source."""
    # TODO: Implement product catalog sync
    # This would sync products from an e-commerce platform
    return {"status": "not_implemented"}


@celery_app.task
def generate_daily_report():
    """Generate daily analytics report."""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from app.models.conversation import Conversation, Message
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Get conversation stats
        total_conversations = db.query(Conversation).filter(
            func.date(Conversation.started_at) == yesterday
        ).count()
        
        total_messages = db.query(Message).filter(
            func.date(Message.created_at) == yesterday
        ).count()
        
        return {
            "date": yesterday.isoformat(),
            "total_conversations": total_conversations,
            "total_messages": total_messages
        }
    finally:
        db.close()
