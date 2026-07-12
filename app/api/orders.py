from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


# Request/Response models
class OrderCreate(BaseModel):
    customer_id: str
    items: List[dict]
    shipping_address: Optional[dict] = None
    currency: str = "USD"


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    shipping_address: Optional[dict] = None


class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int = 1
    sku: Optional[str] = None


@router.get("/")
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all orders with optional filtering."""
    order_service = OrderService(db)
    
    if status:
        orders = await order_service.get_orders_by_status(status, limit, offset)
    else:
        orders = order_service.db.query(order_service.db.query().with_entities).limit(limit).offset(offset).all()
    
    return {
        "orders": [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "customer_id": str(order.customer_id),
                "status": order.status,
                "total_amount": float(order.total_amount),
                "currency": order.currency,
                "items": order.items,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat() if order.updated_at else None
            }
            for order in orders
        ],
        "count": len(orders)
    }


@router.get("/{order_number}")
async def get_order(order_number: str, db: Session = Depends(get_db)):
    """Get order details by order number."""
    order_service = OrderService(db)
    order = await order_service.get_order(order_number)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "customer_id": str(order.customer_id),
        "status": order.status,
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "items": order.items,
        "shipping_address": order.shipping_address,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None
    }


@router.post("/")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order."""
    order_service = OrderService(db)
    
    try:
        order = await order_service.create_order(
            customer_id=order_data.customer_id,
            items=order_data.items,
            shipping_address=order_data.shipping_address,
            currency=order_data.currency
        )
        
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "message": "Order created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_number}")
async def update_order(
    order_number: str,
    update_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update order status or shipping address."""
    order_service = OrderService(db)
    
    try:
        if update_data.status:
            await order_service.update_status(order_number, update_data.status)
        
        if update_data.shipping_address:
            await order_service.update_shipping_address(order_number, update_data.shipping_address)
        
        return {"message": "Order updated successfully", "order_number": order_number}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail="Order not found")


@router.delete("/{order_number}")
async def cancel_order(order_number: str, db: Session = Depends(get_db)):
    """Cancel an order."""
    order_service = OrderService(db)
    
    try:
        await order_service.cancel_order(order_number)
        return {"message": "Order cancelled successfully", "order_number": order_number}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail="Order not found")


@router.get("/{order_number}/status")
async def get_order_status(order_number: str, db: Session = Depends(get_db)):
    """Get order status."""
    order_service = OrderService(db)
    status = await order_service.get_order_status(order_number)
    
    if not status:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"order_number": order_number, "status": status}


@router.post("/{order_number}/status")
async def update_order_status(
    order_number: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Update order status."""
    order_service = OrderService(db)
    
    try:
        await order_service.update_status(order_number, status)
        return {"message": "Status updated", "order_number": order_number, "status": status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customer/{customer_id}")
async def get_customer_orders(
    customer_id: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all orders for a customer."""
    order_service = OrderService(db)
    orders = await order_service.get_customer_orders(customer_id, limit, offset)
    
    return {
        "orders": [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": float(order.total_amount),
                "items": order.items,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ],
        "count": len(orders)
    }


@router.get("/search/{query}")
async def search_orders(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search orders by order number."""
    order_service = OrderService(db)
    orders = await order_service.search_orders(query, limit)
    
    return {
        "orders": [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ],
        "count": len(orders)
    }
