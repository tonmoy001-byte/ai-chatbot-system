import httpx
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import get_settings
from app.services.ai_engine import AIEngine
from app.services.conversation_service import ConversationService

settings = get_settings()
logger = logging.getLogger(__name__)


class FacebookService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.ai_engine = AIEngine()
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Facebook webhook signature."""
        if not signature or not self.app_secret:
            return False
        
        expected = "sha256=" + hmac.new(
            self.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    async def send_message(self, recipient_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Facebook user."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/me/messages",
                    params={"access_token": self.access_token},
                    json={
                        "recipient": {"id": recipient_id},
                        "message": message
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Facebook API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to send message: {str(e)}")
                raise
    
    async def send_text(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Send text message."""
        return await self.send_message(recipient_id, {"text": text})
    
    async def send_image(self, recipient_id: str, image_url: str) -> Dict[str, Any]:
        """Send image message."""
        return await self.send_message(recipient_id, {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url}
            }
        })
    
    async def send_quick_reply(
        self,
        recipient_id: str,
        text: str,
        quick_replies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send message with quick replies."""
        return await self.send_message(recipient_id, {
            "text": text,
            "quick_replies": quick_replies
        })
    
    async def send_typing_indicator(self, recipient_id: str) -> Dict[str, Any]:
        """Send typing indicator."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/messages",
                params={"access_token": self.access_token},
                json={
                    "recipient": {"id": recipient_id},
                    "sender_action": "typing_on"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def mark_seen(self, recipient_id: str) -> Dict[str, Any]:
        """Mark message as seen."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/messages",
                params={"access_token": self.access_token},
                json={
                    "recipient": {"id": recipient_id},
                    "sender_action": "mark_seen"
                }
            )
            response.raise_for_status()
            return response.json()
    
    def extract_message_data(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract message data from Facebook event."""
        sender_id = event.get("sender", {}).get("id")
        message = event.get("message", {})
        postback = event.get("postback", {})
        
        if not sender_id:
            return None
        
        # Handle text messages
        if message.get("text"):
            return {
                "sender_id": sender_id,
                "type": "text",
                "content": message.get("text", ""),
                "message_id": message.get("mid"),
                "timestamp": event.get("timestamp")
            }
        
        # Handle attachments (images, audio, etc.)
        if message.get("attachments"):
            attachment = message["attachments"][0]
            return {
                "sender_id": sender_id,
                "type": attachment.get("type", "unknown"),
                "content": attachment.get("payload", {}).get("url", ""),
                "message_id": message.get("mid"),
                "timestamp": event.get("timestamp")
            }
        
        # Handle postbacks (button clicks)
        if postback:
            return {
                "sender_id": sender_id,
                "type": "postback",
                "content": postback.get("payload", ""),
                "title": postback.get("title"),
                "message_id": None,
                "timestamp": event.get("timestamp")
            }
        
        return None
    
    async def process_event(self, event: Dict[str, Any], db: Session) -> Optional[str]:
        """Process incoming Facebook event and return response."""
        message_data = self.extract_message_data(event)
        
        if not message_data:
            logger.warning(f"Could not extract message data from event: {event}")
            return None
        
        sender_id = message_data["sender_id"]
        message_type = message_data["type"]
        content = message_data["content"]
        
        # Send typing indicator
        await self.send_typing_indicator(sender_id)
        
        # Get or create conversation
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_or_create_conversation(
            platform="facebook",
            platform_user_id=sender_id
        )
        
        # Store incoming message
        await conversation_service.add_message(
            conversation_id=str(conversation.id),
            sender_type="customer",
            content_type=message_type,
            content=content,
            db=db,
            metadata={"message_id": message_data.get("message_id")}
        )
        
        # Handle different message types
        response_text = None
        
        if message_type == "text":
            # Generate AI response for text messages
            response_text = await self.ai_engine.generate_response(
                message=content,
                context={
                    "platform": "facebook",
                    "conversation_id": str(conversation.id),
                    "customer_id": sender_id
                }
            )
        elif message_type == "image":
            # Handle image messages
            response_text = "Thank you for sharing the image. I've received it."
        elif message_type == "audio":
            # Handle voice messages - will be processed by voice processor
            response_text = "I've received your voice message. Processing..."
        elif message_type == "postback":
            # Handle postback button clicks
            response_text = await self.handle_postback(content, sender_id, db)
        
        # Send response
        if response_text:
            await self.send_text(sender_id, response_text)
            
            # Store bot response
            await conversation_service.add_message(
                conversation_id=str(conversation.id),
                sender_type="bot",
                content_type="text",
                content=response_text,
                db=db
            )
        
        return response_text
    
    async def handle_postback(self, payload: str, sender_id: str, db: Session) -> str:
        """Handle postback button clicks."""
        if payload.startswith("ORDER_"):
            order_number = payload.replace("ORDER_", "")
            from app.services.order_service import OrderService
            order_service = OrderService(db)
            return await order_service.format_order_response(order_number)
        elif payload.startswith("BOOK_"):
            return "To book an appointment, please tell me the date and time you'd prefer."
        elif payload == "HELP":
            return "I can help you with:\n- Order status\n- Product information\n- Booking appointments\n\nWhat would you like help with?"
        else:
            return "I'm not sure how to help with that. Could you please rephrase?"
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{user_id}",
                    params={
                        "fields": "first_name,last_name,profile_pic",
                        "access_token": self.access_token
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get user profile: {str(e)}")
                return None
