import httpx
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.ai_engine import AIEngine
from app.services.conversation_service import ConversationService

settings = get_settings()
logger = logging.getLogger(__name__)


class InstagramService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.ai_engine = AIEngine()
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Instagram webhook signature."""
        if not signature or not self.app_secret:
            return False
        
        expected = "sha256=" + hmac.new(
            self.app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    async def send_message(self, recipient_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Instagram user."""
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
                logger.error(f"Instagram API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to send Instagram message: {str(e)}")
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
        """Extract message data from Instagram event."""
        sender_id = event.get("sender", {}).get("id")
        message = event.get("message", {})
        
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
        
        # Handle story mentions
        if event.get("story"):
            return {
                "sender_id": sender_id,
                "type": "story_mention",
                "content": event.get("story", {}).get("url", ""),
                "message_id": None,
                "timestamp": event.get("timestamp")
            }
        
        return None
    
    async def process_event(self, event: Dict[str, Any], db: Session) -> Optional[str]:
        """Process incoming Instagram event and return response."""
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
            platform="instagram",
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
                    "platform": "instagram",
                    "conversation_id": str(conversation.id),
                    "customer_id": sender_id
                }
            )
        elif message_type == "image":
            # Handle image messages
            response_text = "Thank you for sharing the image. I've received it."
        elif message_type == "audio":
            # Handle voice messages
            response_text = "I've received your voice message. Processing..."
        elif message_type == "story_mention":
            # Handle story mentions
            response_text = "Thanks for mentioning us in your story!"
        
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
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get Instagram user profile information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{user_id}",
                    params={
                        "fields": "username,name,profile_picture_url",
                        "access_token": self.access_token
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get Instagram user profile: {str(e)}")
                return None
