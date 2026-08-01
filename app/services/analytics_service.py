from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import logging

from app.models.conversation import Conversation, Message
from app.models.customer import Customer
from app.models.order import Order

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Today's stats
        today_conversations = self._count_conversations(today)
        today_messages = self._count_messages(today)
        today_orders = self._count_orders(today)
        
        # Yesterday's stats (for comparison)
        yesterday_conversations = self._count_conversations(yesterday)
        yesterday_messages = self._count_messages(yesterday)
        
        # Overall stats
        total_conversations = self._count_conversations_total()
        total_customers = self._count_customers()
        total_orders = self._count_orders_total()
        
        # Active conversations
        active_conversations = self.db.query(func.count(Conversation.id)).filter(
            Conversation.status == "active"
        ).scalar() or 0
        
        # Average messages per conversation
        avg_messages = self._get_average_messages_per_conversation()
        
        # Growth rates
        conversation_growth = self._calculate_growth_rate(today_conversations, yesterday_conversations)
        message_growth = self._calculate_growth_rate(today_messages, yesterday_messages)
        
        return {
            "today": {
                "conversations": today_conversations,
                "messages": today_messages,
                "orders": today_orders,
                "conversation_growth": conversation_growth,
                "message_growth": message_growth
            },
            "totals": {
                "conversations": total_conversations,
                "customers": total_customers,
                "orders": total_orders
            },
            "active": {
                "conversations": active_conversations
            },
            "averages": {
                "messages_per_conversation": round(avg_messages, 2)
            }
        }
    
    async def get_conversation_analytics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get conversation analytics for a date range."""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Get conversations in date range
        conversations = self.db.query(Conversation).filter(
            func.date(Conversation.started_at) >= start_date,
            func.date(Conversation.started_at) <= end_date
        ).all()
        
        # Calculate metrics
        total = len(conversations)
        statuses = {}
        platforms = {}
        hourly_distribution = {h: 0 for h in range(24)}
        
        for conv in conversations:
            # Status distribution
            status = conv.status
            statuses[status] = statuses.get(status, 0) + 1
            
            # Platform distribution (would need customer data)
            # Hourly distribution
            if conv.started_at:
                hour = conv.started_at.hour
                hourly_distribution[hour] += 1
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_conversations": total,
            "status_distribution": statuses,
            "hourly_distribution": hourly_distribution,
            "average_daily": round(total / max((end_date - start_date).days, 1), 2)
        }
    
    async def get_message_analytics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get message analytics."""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        messages = self.db.query(Message).filter(
            func.date(Message.created_at) >= start_date,
            func.date(Message.created_at) <= end_date
        ).all()
        
        total = len(messages)
        sender_types = {}
        content_types = {}
        
        for msg in messages:
            sender_types[msg.sender_type] = sender_types.get(msg.sender_type, 0) + 1
            content_types[msg.content_type] = content_types.get(msg.content_type, 0) + 1
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_messages": total,
            "sender_distribution": sender_types,
            "content_type_distribution": content_types,
            "average_daily": round(total / max((end_date - start_date).days, 1), 2)
        }
    
    async def get_order_analytics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get order analytics."""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        orders = self.db.query(Order).filter(
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date
        ).all()
        
        total = len(orders)
        statuses = {}
        total_revenue = 0
        
        for order in orders:
            statuses[order.status] = statuses.get(order.status, 0) + 1
            if order.status != "cancelled":
                total_revenue += float(order.total_amount or 0)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_orders": total,
            "status_distribution": statuses,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(total_revenue / max(total, 1), 2)
        }
    
    async def get_peak_hours(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get peak hours for conversations."""
        start_date = date.today() - timedelta(days=days)
        
        conversations = self.db.query(
            func.extract('hour', Conversation.started_at).label('hour'),
            func.count(Conversation.id).label('count')
        ).filter(
            func.date(Conversation.started_at) >= start_date
        ).group_by('hour').order_by('hour').all()
        
        return [
            {"hour": int(c.hour), "count": c.count}
            for c in conversations
        ]
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity feed."""
        recent_conversations = self.db.query(Conversation).order_by(
            desc(Conversation.last_message_at)
        ).limit(limit).all()
        
        activity = []
        for conv in recent_conversations:
            # Get last message
            last_message = self.db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(desc(Message.created_at)).first()
            
            activity.append({
                "conversation_id": str(conv.id),
                "customer_id": str(conv.customer_id),
                "status": conv.status,
                "last_message": last_message.content if last_message else None,
                "last_message_time": conv.last_message_at.isoformat() if conv.last_message_at else None
            })
        
        return activity
    
    def _count_conversations(self, target_date: date) -> int:
        """Count conversations for a specific date."""
        return self.db.query(func.count(Conversation.id)).filter(
            func.date(Conversation.started_at) == target_date
        ).scalar() or 0
    
    def _count_messages(self, target_date: date) -> int:
        """Count messages for a specific date."""
        return self.db.query(func.count(Message.id)).filter(
            func.date(Message.created_at) == target_date
        ).scalar() or 0
    
    def _count_orders(self, target_date: date) -> int:
        """Count orders for a specific date."""
        return self.db.query(func.count(Order.id)).filter(
            func.date(Order.created_at) == target_date
        ).scalar() or 0
    
    def _count_conversations_total(self) -> int:
        """Count total conversations."""
        return self.db.query(func.count(Conversation.id)).scalar() or 0
    
    def _count_customers(self) -> int:
        """Count total customers."""
        return self.db.query(func.count(Customer.id)).scalar() or 0
    
    def _count_orders_total(self) -> int:
        """Count total orders."""
        return self.db.query(func.count(Order.id)).scalar() or 0
    
    def _get_average_messages_per_conversation(self) -> float:
        """Calculate average messages per conversation."""
        total_messages = self.db.query(func.count(Message.id)).scalar() or 0
        total_conversations = self.db.query(func.count(Conversation.id)).scalar() or 0
        
        if total_conversations == 0:
            return 0.0
        
        return total_messages / total_conversations
    
    def _calculate_growth_rate(self, current: int, previous: int) -> float:
        """Calculate growth rate percentage."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)
