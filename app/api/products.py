from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


# Request/Response models
class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    metadata: Optional[dict] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("/")
async def list_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all products."""
    product_service = ProductService(db)
    products = await product_service.get_all_products(limit, offset)
    
    return {
        "products": [
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "price": float(product.price) if product.price else 0,
                "image_url": product.image_url,
                "created_at": product.created_at.isoformat()
            }
            for product in products
        ],
        "count": len(products)
    }


@router.get("/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get product details."""
    product_service = ProductService(db)
    product = await product_service.get_product(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": float(product.price) if product.price else 0,
        "image_url": product.image_url,
        "metadata": product.extra_data,
        "created_at": product.created_at.isoformat()
    }


@router.get("/sku/{sku}")
async def get_product_by_sku(sku: str, db: Session = Depends(get_db)):
    """Get product by SKU."""
    product_service = ProductService(db)
    product = await product_service.get_product_by_sku(sku)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": float(product.price) if product.price else 0,
        "image_url": product.image_url,
        "created_at": product.created_at.isoformat()
    }


@router.post("/")
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    product_service = ProductService(db)
    
    # Check if SKU already exists
    existing = await product_service.get_product_by_sku(product_data.sku)
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product = await product_service.create_product(
        sku=product_data.sku,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        image_url=product_data.image_url,
        metadata=product_data.metadata
    )
    
    return {
        "id": str(product.id),
        "sku": product.sku,
        "message": "Product created successfully"
    }


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update product details."""
    product_service = ProductService(db)
    
    updated = await product_service.update_product(
        product_id=product_id,
        name=update_data.name,
        description=update_data.description,
        price=update_data.price,
        image_url=update_data.image_url,
        metadata=update_data.metadata
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product updated successfully", "product_id": product_id}


@router.delete("/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete a product."""
    product_service = ProductService(db)
    
    deleted = await product_service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully", "product_id": product_id}


@router.get("/search/{query}")
async def search_products(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name or description."""
    product_service = ProductService(db)
    products = await product_service.search_products(query, limit)
    
    return {
        "products": [
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "price": float(product.price) if product.price else 0,
                "image_url": product.image_url
            }
            for product in products
        ],
        "count": len(products)
    }


@router.get("/price-range/")
async def get_products_by_price(
    min_price: float = Query(0, ge=0),
    max_price: float = Query(10000, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products within a price range."""
    product_service = ProductService(db)
    products = await product_service.get_products_by_price_range(min_price, max_price, limit)
    
    return {
        "products": [
            {
                "id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "price": float(product.price) if product.price else 0,
                "image_url": product.image_url
            }
            for product in products
        ],
        "count": len(products)
    }
