from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.services.facebook import FacebookService
from app.services.instagram import InstagramService
from app.services.image_service import ImageService
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.facebook_service = FacebookService()
        self.instagram_service = InstagramService()
        self.image_service = ImageService()
        self.conversation_service = ConversationService(db)
    
    async def send_order_confirmation(
        self,
        platform: str,
        user_id: str,
        order: Dict[str, Any]
    ) -> bool:
        """Send order confirmation message."""
        try:
            # Send text confirmation
            confirmation_text = self._format_order_confirmation(order)
            
            if platform == "facebook":
                await self.facebook_service.send_text(user_id, confirmation_text)
            elif platform == "instagram":
                await self.instagram_service.send_text(user_id, confirmation_text)
            else:
                return False
            
            # Send receipt card if image service is available
            if order.get("items"):
                await self.image_service.send_order_confirmation(
                    recipient_id=user_id,
                    order=order,
                    platform=platform
                )
            
            logger.info(f"Order confirmation sent to {user_id} on {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation: {str(e)}")
            return False
    
    async def send_order_update(
        self,
        platform: str,
        user_id: str,
        order_number: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send order status update."""
        try:
            update_text = self._format_order_update(order_number, status, details)
            
            if platform == "facebook":
                await self.facebook_service.send_text(user_id, update_text)
            elif platform == "instagram":
                await self.instagram_service.send_text(user_id, update_text)
            else:
                return False
            
            # Send shipping update with tracking if available
            if status == "shipped" and details and details.get("tracking_url"):
                await self.image_service.send_shipping_update(
                    recipient_id=user_id,
                    order_number=order_number,
                    tracking_url=details.get("tracking_url"),
                    platform=platform
                )
            
            logger.info(f"Order update sent to {user_id}: {order_number} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order update: {str(e)}")
            return False
    
    async def send_product_recommendation(
        self,
        platform: str,
        user_id: str,
        products: list
    ) -> bool:
        """Send product recommendations."""
        try:
            if not products:
                return False
            
            # Send product gallery
            product_data = [
                {
                    "name": p.get("name", ""),
                    "price": p.get("price", 0),
                    "image_url": p.get("image_url", ""),
                    "sku": p.get("sku", "")
                }
                for p in products
            ]
            
            await self.image_service.send_product_gallery(
                recipient_id=user_id,
                products=product_data,
                platform=platform
            )
            
            logger.info(f"Product recommendations sent to {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send product recommendations: {str(e)}")
            return False
    
    async def send_delivery_confirmation(
        self,
        platform: str,
        user_id: str,
        order_number: str
    ) -> bool:
        """Send delivery confirmation."""
        try:
            message = (
                f"Great news! Your order {order_number} has been delivered.\n\n"
                f"Thank you for your purchase! We hope you love your items.\n\n"
                f"If you have any questions or need to make a return, "
                f"just let us know."
            )
            
            if platform == "facebook":
                await self.facebook_service.send_text(user_id, message)
            elif platform == "instagram":
                await self.instagram_service.send_text(user_id, message)
            else:
                return False
            
            logger.info(f"Delivery confirmation sent to {user_id}: {order_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send delivery confirmation: {str(e)}")
            return False
    
    async def send_cancellation_confirmation(
        self,
        platform: str,
        user_id: str,
        order_number: str,
        reason: Optional[str] = None
    ) -> bool:
        """Send order cancellation confirmation."""
        try:
            message = (
                f"Your order {order_number} has been cancelled.\n\n"
                f"If a payment was made, a refund will be processed within 5-10 business days.\n\n"
            )
            
            if reason:
                message += f"Reason: {reason}\n\n"
            
            message += "If you didn't request this cancellation, please contact us immediately."
            
            if platform == "facebook":
                await self.facebook_service.send_text(user_id, message)
            elif platform == "instagram":
                await self.instagram_service.send_text(user_id, message)
            else:
                return False
            
            logger.info(f"Cancellation confirmation sent to {user_id}: {order_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send cancellation confirmation: {str(e)}")
            return False
    
    def _format_order_confirmation(self, order: Dict[str, Any]) -> str:
        """Format order confirmation message."""
        items = order.get("items", [])
        item_count = sum(item.get("quantity", 1) for item in items)
        
        message = f"Order Confirmed! 🎉\n\n"
        message += f"Order Number: {order.get('order_number', 'N/A')}\n"
        message += f"Items: {item_count}\n"
        message += f"Total: ${order.get('total', 0):.2f} {order.get('currency', 'USD')}\n\n"
        message += "You'll receive updates as your order is processed and shipped."
        
        return message
    
    def _format_order_update(
        self,
        order_number: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format order update message."""
        status_messages = {
            "confirmed": "has been confirmed",
            "processing": "is being prepared",
            "shipped": "has been shipped",
            "delivered": "has been delivered",
            "cancelled": "has been cancelled",
            "refunded": "has been refunded"
        }
        
        message = f"Order Update\n\n"
        message += f"Your order {order_number} {status_messages.get(status, 'has been updated')}.\n\n"
        
        if details:
            if details.get("tracking_number"):
                message += f"Tracking Number: {details['tracking_number']}\n"
            if details.get("estimated_delivery"):
                message += f"Estimated Delivery: {details['estimated_delivery']}\n"
        
        return message
