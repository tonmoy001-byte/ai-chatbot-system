from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from app.models.order import Order
from app.models.customer import Customer

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_order_status(self, order_number: str) -> Optional[str]:
        """Retrieve order status by order number."""
        order = self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
        return order.status if order else None
    
    async def get_order(self, order_number: str) -> Optional[Order]:
        """Retrieve full order by order number."""
        return self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
    
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieve order by ID."""
        return self.db.query(Order).filter(
            Order.id == order_id
        ).first()
    
    async def get_customer_orders(
        self,
        customer_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Order]:
        """Get all orders for a customer."""
        return self.db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(
            Order.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    async def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: Optional[Dict[str, Any]] = None,
        currency: str = "USD"
    ) -> Order:
        """Create a new order."""
        # Generate order number
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total amount
        total_amount = sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in items
        )
        
        order = Order(
            id=uuid.uuid4(),
            customer_id=customer_id,
            order_number=order_number,
            status="pending",
            total_amount=total_amount,
            currency=currency,
            items=items,
            shipping_address=shipping_address or {}
        )
        
        self.db.add(order)
        self.db.commit()
        
        logger.info(f"Created order {order_number} for customer {customer_id}")
        return order
    
    async def update_status(self, order_number: str, status: str) -> bool:
        """Update order status."""
        order = self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
        
        if not order:
            return False
        
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        old_status = order.status
        order.status = status
        order.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Order {order_number} status updated: {old_status} -> {status}")
        return True
    
    async def cancel_order(self, order_number: str) -> bool:
        """Cancel an order."""
        order = self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
        
        if not order:
            return False
        
        if order.status in ["shipped", "delivered"]:
            raise ValueError(f"Cannot cancel order in {order.status} status")
        
        order.status = "cancelled"
        order.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Order {order_number} cancelled")
        return True
    
    async def add_items(
        self,
        order_number: str,
        items: List[Dict[str, Any]]
    ) -> bool:
        """Add items to an existing order."""
        order = self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
        
        if not order:
            return False
        
        if order.status not in ["pending", "confirmed"]:
            raise ValueError(f"Cannot add items to order in {order.status} status")
        
        # Add new items
        existing_items = order.items or []
        existing_items.extend(items)
        order.items = existing_items
        
        # Recalculate total
        order.total_amount = sum(
            item.get("price", 0) * item.get("quantity", 1)
            for item in existing_items
        )
        order.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    async def update_shipping_address(
        self,
        order_number: str,
        shipping_address: Dict[str, Any]
    ) -> bool:
        """Update shipping address."""
        order = self.db.query(Order).filter(
            Order.order_number == order_number
        ).first()
        
        if not order:
            return False
        
        if order.status in ["shipped", "delivered"]:
            raise ValueError(f"Cannot update address for order in {order.status} status")
        
        order.shipping_address = shipping_address
        order.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    async def get_orders_by_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get orders by status."""
        return self.db.query(Order).filter(
            Order.status == status
        ).order_by(
            Order.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    async def search_orders(
        self,
        query: str,
        limit: int = 20
    ) -> List[Order]:
        """Search orders by order number or customer ID."""
        return self.db.query(Order).filter(
            Order.order_number.ilike(f"%{query}%")
        ).limit(limit).all()
    
    async def format_order_response(self, order_number: str) -> str:
        """Generate customer-friendly order status message."""
        order = await self.get_order(order_number)
        
        if not order:
            return f"Order {order_number} not found. Please check the number and try again."
        
        status_messages = {
            "pending": "Your order is being processed.",
            "confirmed": "Your order has been confirmed!",
            "processing": "Your order is being prepared.",
            "shipped": "Your order is on its way!",
            "delivered": "Your order has been delivered.",
            "cancelled": "Your order has been cancelled.",
            "refunded": "Your order has been refunded."
        }
        
        response = f"Order {order_number}: {status_messages.get(order.status, 'Status unknown.')}"
        
        # Add item summary
        if order.items:
            item_count = sum(item.get("quantity", 1) for item in order.items)
            response += f"\nItems: {item_count}"
        
        # Add total
        if order.total_amount:
            response += f"\nTotal: ${order.total_amount:.2f} {order.currency}"
        
        return response
    
    async def format_detailed_order_response(self, order_number: str) -> str:
        """Generate detailed customer-friendly order response."""
        order = await self.get_order(order_number)
        
        if not order:
            return f"Order {order_number} not found."
        
        status_messages = {
            "pending": "Your order is being processed.",
            "confirmed": "Your order has been confirmed!",
            "processing": "Your order is being prepared.",
            "shipped": "Your order is on its way!",
            "delivered": "Your order has been delivered.",
            "cancelled": "Your order has been cancelled.",
            "refunded": "Your order has been refunded."
        }
        
        response = f"Order Details: {order_number}\n"
        response += f"Status: {status_messages.get(order.status, 'Unknown')}\n"
        
        if order.items:
            response += "\nItems:\n"
            for i, item in enumerate(order.items, 1):
                name = item.get("name", "Unknown item")
                qty = item.get("quantity", 1)
                price = item.get("price", 0)
                response += f"{i}. {name} x{qty} - ${price:.2f}\n"
        
        if order.total_amount:
            response += f"\nTotal: ${order.total_amount:.2f} {order.currency}"
        
        if order.shipping_address:
            addr = order.shipping_address
            response += f"\n\nShipping to:\n{addr.get('name', '')}\n{addr.get('address', '')}\n{addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}"
        
        return response
