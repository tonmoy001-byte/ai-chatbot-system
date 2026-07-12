from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from app.models.product import Product

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self.db.query(Product).filter(
            Product.id == product_id
        ).first()
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.db.query(Product).filter(
            Product.sku == sku
        ).first()
    
    async def create_product(
        self,
        sku: str,
        name: str,
        description: Optional[str] = None,
        price: float = 0.0,
        image_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Product:
        """Create a new product."""
        product = Product(
            id=uuid.uuid4(),
            sku=sku,
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            extra_data=metadata or {}
        )
        
        self.db.add(product)
        self.db.commit()
        
        logger.info(f"Created product {sku}: {name}")
        return product
    
    async def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        image_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update product details."""
        product = self.db.query(Product).filter(
            Product.id == product_id
        ).first()
        
        if not product:
            return False
        
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if image_url is not None:
            product.image_url = image_url
        if metadata is not None:
            product.extra_data = metadata
        
        self.db.commit()
        return True
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        product = self.db.query(Product).filter(
            Product.id == product_id
        ).first()
        
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
        
        logger.info(f"Deleted product {product.sku}")
        return True
    
    async def search_products(
        self,
        query: str,
        limit: int = 20
    ) -> List[Product]:
        """Search products by name or description."""
        search_term = f"%{query}%"
        return self.db.query(Product).filter(
            Product.name.ilike(search_term) |
            Product.description.ilike(search_term)
        ).limit(limit).all()
    
    async def get_all_products(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """Get all products with pagination."""
        return self.db.query(Product).order_by(
            Product.name
        ).offset(offset).limit(limit).all()
    
    async def get_products_by_price_range(
        self,
        min_price: float,
        max_price: float,
        limit: int = 50
    ) -> List[Product]:
        """Get products within a price range."""
        return self.db.query(Product).filter(
            Product.price >= min_price,
            Product.price <= max_price
        ).order_by(Product.price).limit(limit).all()
    
    async def format_product_response(self, product: Product) -> str:
        """Format product as customer-friendly message."""
        response = f"Product: {product.name}\n"
        response += f"SKU: {product.sku}\n"
        
        if product.price:
            response += f"Price: ${product.price:.2f}\n"
        
        if product.description:
            # Truncate long descriptions
            desc = product.description[:200]
            if len(product.description) > 200:
                desc += "..."
            response += f"Description: {desc}\n"
        
        return response
    
    async def format_product_list_response(self, products: List[Product]) -> str:
        """Format multiple products as customer-friendly message."""
        if not products:
            return "No products found matching your search."
        
        response = f"Found {len(products)} product(s):\n\n"
        
        for i, product in enumerate(products[:5], 1):  # Limit to 5 products
            response += f"{i}. {product.name} - ${product.price:.2f}\n"
            response += f"   SKU: {product.sku}\n"
        
        if len(products) > 5:
            response += f"\n... and {len(products) - 5} more products."
        
        return response
    
    async def handle_product_inquiry(self, message: str) -> str:
        """Handle product-related customer inquiries."""
        # Search for products matching the message
        products = await self.search_products(message, limit=5)
        
        if not products:
            return "I couldn't find any products matching your search. Could you be more specific?"
        
        return await self.format_product_list_response(products)
