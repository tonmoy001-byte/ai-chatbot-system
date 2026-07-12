from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


class EscalationReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    COMPLAINT = "complaint"
    COMPLEX_ISSUE = "complex_issue"
    REPEATED_FAILURE = "repeated_failure"
    HIGH_URGENCY = "high_urgency"
    VIP_CUSTOMER = "vip_customer"


class EscalationStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_escalation(
        self,
        conversation_id: str,
        reason: EscalationReason,
        priority: int = 1,
        notes: Optional[str] = None,
        customer_sentiment: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a new escalation for a conversation.
        
        Args:
            conversation_id: ID of the conversation to escalate
            reason: Reason for escalation
            priority: Priority level (1=low, 5=critical)
            notes: Additional notes
            customer_sentiment: Customer sentiment score
        
        Returns:
            Escalation details
        """
        # Get conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Update conversation status
        conversation.status = "escalated"
        conversation.extra_data = conversation.extra_data or {}
        conversation.extra_data["escalation"] = {
            "reason": reason.value,
            "priority": priority,
            "notes": notes,
            "customer_sentiment": customer_sentiment,
            "escalated_at": datetime.utcnow().isoformat(),
            "status": EscalationStatus.PENDING.value
        }
        
        self.db.commit()
        
        logger.info(f"Escalation created for conversation {conversation_id}: {reason.value}")
        
        return {
            "conversation_id": conversation_id,
            "reason": reason.value,
            "priority": priority,
            "status": EscalationStatus.PENDING.value,
            "escalated_at": conversation.extra_data["escalation"]["escalated_at"]
        }
    
    async def assign_agent(
        self,
        conversation_id: str,
        agent_id: str
    ) -> bool:
        """
        Assign an agent to an escalated conversation.
        
        Args:
            conversation_id: Conversation ID
            agent_id: Agent ID to assign
        
        Returns:
            Success status
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        if conversation.status != "escalated":
            raise ValueError("Conversation is not escalated")
        
        # Update extra_data
        conversation.extra_data["escalation"]["agent_id"] = agent_id
        conversation.extra_data["escalation"]["status"] = EscalationStatus.ASSIGNED.value
        conversation.extra_data["escalation"]["assigned_at"] = datetime.utcnow().isoformat()
        
        self.db.commit()
        
        logger.info(f"Agent {agent_id} assigned to conversation {conversation_id}")
        return True
    
    async def resolve_escalation(
        self,
        conversation_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Mark an escalation as resolved.
        
        Args:
            conversation_id: Conversation ID
            resolution_notes: Notes about the resolution
        
        Returns:
            Success status
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        if conversation.status != "escalated":
            raise ValueError("Conversation is not escalated")
        
        # Update extra_data
        conversation.extra_data["escalation"]["status"] = EscalationStatus.RESOLVED.value
        conversation.extra_data["escalation"]["resolved_at"] = datetime.utcnow().isoformat()
        conversation.extra_data["escalation"]["resolution_notes"] = resolution_notes
        
        # Update conversation status
        conversation.status = "resolved"
        
        self.db.commit()
        
        logger.info(f"Escalation resolved for conversation {conversation_id}")
        return True
    
    async def get_pending_escalations(self) -> List[Dict[str, Any]]:
        """Get all pending escalations."""
        conversations = self.db.query(Conversation).filter(
            Conversation.status == "escalated"
        ).order_by(Conversation.last_message_at.desc()).all()
        
        escalations = []
        for conv in conversations:
            escalation_data = conv.extra_data.get("escalation", {})
            if escalation_data.get("status") in [
                EscalationStatus.PENDING.value,
                EscalationStatus.ASSIGNED.value,
                EscalationStatus.IN_PROGRESS.value
            ]:
                escalations.append({
                    "conversation_id": str(conv.id),
                    "customer_id": str(conv.customer_id),
                    "reason": escalation_data.get("reason"),
                    "priority": escalation_data.get("priority", 1),
                    "status": escalation_data.get("status"),
                    "agent_id": escalation_data.get("agent_id"),
                    "escalated_at": escalation_data.get("escalated_at"),
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
                })
        
        return escalations
    
    async def get_escalation_history(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get escalation history for a conversation."""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        return conversation.extra_data.get("escalation", None)
    
    async def should_auto_escalate(
        self,
        sentiment_score: float,
        is_complaint: bool,
        escalation_count: int = 0,
        customer_value: str = "normal"
    ) -> Dict[str, Any]:
        """
        Determine if a conversation should be auto-escalated.
        
        Args:
            sentiment_score: Customer sentiment score (-1 to 1)
            is_complaint: Whether the message is a complaint
            escalation_count: Number of previous escalations
            customer_value: Customer value tier (normal, vip)
        
        Returns:
            Decision with reasoning
        """
        should_escalate = False
        reason = None
        priority = 1
        
        # Check for very negative sentiment
        if sentiment_score < -0.5:
            should_escalate = True
            reason = EscalationReason.NEGATIVE_SENTIMENT
            priority = 4
        
        # Check for complaints
        elif is_complaint:
            should_escalate = True
            reason = EscalationReason.COMPLAINT
            priority = 3
        
        # Check for VIP customers with any issues
        elif customer_value == "vip" and sentiment_score < 0:
            should_escalate = True
            reason = EscalationReason.VIP_CUSTOMER
            priority = 2
        
        # Check for repeated issues
        elif escalation_count >= 3:
            should_escalate = True
            reason = EscalationReason.REPEATED_FAILURE
            priority = 3
        
        return {
            "should_escalate": should_escalate,
            "reason": reason.value if reason else None,
            "priority": priority,
            "sentiment_score": sentiment_score,
            "is_complaint": is_complaint,
            "escalation_count": escalation_count,
            "customer_value": customer_value
        }
    
    def format_escalation_message(self) -> str:
        """Format a message to send when escalating."""
        return (
            "I understand you're having an issue that requires special attention. "
            "I'm connecting you with a human agent who can better assist you. "
            "Please hold on for a moment."
        )
    
    def format_resolution_message(self, resolution_notes: Optional[str] = None) -> str:
        """Format a message when resolving an escalation."""
        message = "Your issue has been resolved. "
        
        if resolution_notes:
            message += f"\n\nResolution: {resolution_notes}\n\n"
        
        message += "Is there anything else I can help you with?"
        
        return message
