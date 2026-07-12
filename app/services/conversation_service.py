from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.models.customer import Customer
from app.models.conversation import Conversation, Message


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_or_create_conversation(
        self,
        platform: str,
        platform_user_id: str
    ) -> Conversation:
        """Get or create conversation for customer."""
        # Get or create customer
        customer = self.db.query(Customer).filter(
            Customer.platform == platform,
            Customer.platform_user_id == platform_user_id
        ).first()
        
        if not customer:
            customer = Customer(
                id=uuid.uuid4(),
                platform=platform,
                platform_user_id=platform_user_id
            )
            self.db.add(customer)
            self.db.commit()
        
        # Get or create conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.customer_id == customer.id,
            Conversation.status == "active"
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=uuid.uuid4(),
                customer_id=customer.id,
                status="active"
            )
            self.db.add(conversation)
            self.db.commit()
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        sender_type: str,
        content_type: str,
        content: str,
        db: Session,
        media_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add message to conversation."""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            sender_type=sender_type,
            content_type=content_type,
            content=content,
            media_url=media_url,
            metadata=metadata or {}
        )
        db.add(message)
        
        # Update conversation last message time
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.last_message_at = datetime.utcnow()
        
        db.commit()
        return message
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with messages."""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        return {
            "id": str(conversation.id),
            "status": conversation.status,
            "started_at": conversation.started_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat(),
            "messages": [
                {
                    "id": str(msg.id),
                    "sender_type": msg.sender_type,
                    "content_type": msg.content_type,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    
    async def list_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations with optional filtering."""
        query = self.db.query(Conversation)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        conversations = query.order_by(
            Conversation.last_message_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            {
                "id": str(conv.id),
                "customer_id": str(conv.customer_id),
                "status": conv.status,
                "started_at": conv.started_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat()
            }
            for conv in conversations
        ]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        total = self.db.query(Conversation).count()
        active = self.db.query(Conversation).filter(
            Conversation.status == "active"
        ).count()
        
        return {
            "total_conversations": total,
            "active_conversations": active,
            "inactive_conversations": total - active
        }
