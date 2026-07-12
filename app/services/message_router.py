import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from enum import Enum

from app.services.facebook import FacebookService
from app.services.instagram import InstagramService
from app.services.ai_engine import AIEngine
from app.services.order_service import OrderService
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    POSTBACK = "postback"
    QUICK_REPLY = "quick_reply"


class IntentType(Enum):
    GREETING = "greeting"
    ORDER_STATUS = "order_status"
    PRODUCT_INFO = "product_info"
    BOOKING = "booking"
    COMPLAINT = "complaint"
    QUESTION = "question"
    OTHER = "other"


class MessageRouter:
    def __init__(self, db: Session):
        self.db = db
        self.ai_engine = AIEngine()
        self.conversation_service = ConversationService(db)
    
    async def route_message(
        self,
        platform: str,
        sender_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Route incoming message to appropriate handler."""
        
        # Get or create conversation
        conversation = await self.conversation_service.get_or_create_conversation(
            platform=platform,
            platform_user_id=sender_id
        )
        
        # Store incoming message
        await self.conversation_service.add_message(
            conversation_id=str(conversation.id),
            sender_type="customer",
            content_type=message_type,
            content=content,
            db=self.db,
            metadata=metadata
        )
        
        # Analyze intent for text messages
        intent = IntentType.OTHER
        if message_type == MessageType.TEXT.value:
            intent = await self.analyze_intent(content)
        
        # Route based on message type and intent
        response = await self.handle_message(
            platform=platform,
            conversation_id=str(conversation.id),
            sender_id=sender_id,
            message_type=message_type,
            content=content,
            intent=intent,
            metadata=metadata
        )
        
        # Store bot response
        if response:
            await self.conversation_service.add_message(
                conversation_id=str(conversation.id),
                sender_type="bot",
                content_type="text",
                content=response,
                db=self.db
            )
        
        return response
    
    async def analyze_intent(self, message: str) -> IntentType:
        """Analyze customer intent from message."""
        try:
            intent_str = await self.ai_engine.analyze_intent(message)
            
            # Map string to IntentType
            intent_map = {
                "greeting": IntentType.GREETING,
                "order_status": IntentType.ORDER_STATUS,
                "product_info": IntentType.PRODUCT_INFO,
                "booking": IntentType.BOOKING,
                "complaint": IntentType.COMPLAINT,
                "question": IntentType.QUESTION,
            }
            
            return intent_map.get(intent_str, IntentType.OTHER)
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return IntentType.OTHER
    
    async def handle_message(
        self,
        platform: str,
        conversation_id: str,
        sender_id: str,
        message_type: str,
        content: str,
        intent: IntentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Handle message based on type and intent."""
        
        # Handle different message types
        if message_type == MessageType.IMAGE.value:
            return await self.handle_image_message(content, sender_id)
        
        if message_type == MessageType.AUDIO.value:
            return await self.handle_audio_message(content, sender_id)
        
        if message_type == MessageType.POSTBACK.value:
            return await self.handle_postback(content, sender_id)
        
        # Handle text messages based on intent
        if message_type == MessageType.TEXT.value:
            return await self.handle_text_message(
                content=content,
                intent=intent,
                sender_id=sender_id,
                conversation_id=conversation_id
            )
        
        return "I received your message. How can I help you?"
    
    async def handle_text_message(
        self,
        content: str,
        intent: IntentType,
        sender_id: str,
        conversation_id: str
    ) -> str:
        """Handle text messages based on intent."""
        
        if intent == IntentType.GREETING:
            return await self.ai_engine.generate_response(
                message=content,
                context={"intent": "greeting"},
                system_prompt="You are a friendly customer service assistant. Greet the customer warmly and ask how you can help."
            )
        
        elif intent == IntentType.ORDER_STATUS:
            # Extract order number and check status
            entities = await self.ai_engine.extract_entities(content)
            order_numbers = entities.get("order_numbers", [])
            
            if order_numbers:
                order_service = OrderService(self.db)
                return await order_service.format_order_response(order_numbers[0])
            else:
                return "I can help you check your order status. Could you please provide your order number? It usually starts with 'ORD-'."
        
        elif intent == IntentType.PRODUCT_INFO:
            return await self.ai_engine.generate_response(
                message=content,
                context={"intent": "product_info"},
                system_prompt="You are a helpful product assistant. Help the customer with product information. If you don't have specific product details, offer to connect them with a human agent."
            )
        
        elif intent == IntentType.BOOKING:
            return "I can help you book an appointment. Please tell me:\n1. What service you need\n2. Your preferred date and time\n\nI'll check availability for you."
        
        elif intent == IntentType.COMPLAINT:
            return await self.ai_engine.generate_response(
                message=content,
                context={"intent": "complaint"},
                system_prompt="You are an empathetic customer service agent. Acknowledge the customer's concern, apologize for any inconvenience, and offer to help resolve the issue. If needed, offer to connect them with a human agent."
            )
        
        else:
            # General AI response
            return await self.ai_engine.generate_response(
                message=content,
                context={
                    "conversation_id": conversation_id,
                    "customer_id": sender_id
                }
            )
    
    async def handle_image_message(self, image_url: str, sender_id: str) -> str:
        """Handle incoming image messages."""
        # For now, just acknowledge receipt
        # In future, could use image recognition for product matching
        return "Thank you for sharing the image. I've received it. How can I help you with this?"
    
    async def handle_audio_message(self, audio_url: str, sender_id: str) -> str:
        """Handle incoming audio/voice messages."""
        # Will be processed by voice processor
        return "I've received your voice message. Processing your request..."
    
    async def handle_postback(self, payload: str, sender_id: str) -> str:
        """Handle postback button clicks."""
        if payload.startswith("ORDER_"):
            order_number = payload.replace("ORDER_", "")
            order_service = OrderService(self.db)
            return await order_service.format_order_response(order_number)
        
        elif payload.startswith("BOOK_"):
            return "To book an appointment, please tell me the date and time you'd prefer."
        
        elif payload == "HELP":
            return (
                "I can help you with:\n"
                "- Order status (provide your order number)\n"
                "- Product information\n"
                "- Booking appointments\n"
                "- General questions\n\n"
                "What would you like help with?"
            )
        
        elif payload == "TALK_TO_HUMAN":
            return "I'll connect you with a human agent. Please hold on for a moment."
        
        else:
            return "I'm not sure how to help with that. Could you please rephrase?"
