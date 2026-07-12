from sqlalchemy import text, Index
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


# Common indexes for performance optimization
INDEXES = [
    # Conversations
    Index("ix_conversations_customer_id", "conversations", "customer_id"),
    Index("ix_conversations_status", "conversations", "status"),
    Index("ix_conversations_last_message_at", "conversations", "last_message_at"),
    
    # Messages
    Index("ix_messages_conversation_id", "messages", "conversation_id"),
    Index("ix_messages_created_at", "messages", "created_at"),
    Index("ix_messages_sender_type", "messages", "sender_type"),
    
    # Orders
    Index("ix_orders_customer_id", "orders", "customer_id"),
    Index("ix_orders_status", "orders", "status"),
    Index("ix_orders_order_number", "orders", "order_number"),
    Index("ix_orders_created_at", "orders", "created_at"),
    
    # Products
    Index("ix_products_sku", "products", "sku"),
    Index("ix_products_name", "products", "name"),
    Index("ix_products_price", "products", "price"),
    
    # Bookings
    Index("ix_bookings_customer_id", "bookings", "customer_id"),
    Index("ix_bookings_start_time", "bookings", "start_time"),
    Index("ix_bookings_status", "bookings", "status"),
    
    # Customers
    Index("ix_customers_platform_user_id", "customers", "platform_user_id"),
    Index("ix_customers_platform", "customers", "platform"),
]


def create_indexes(db: Session):
    """Create all performance indexes."""
    try:
        for index in INDEXES:
            try:
                index.create(db.bind, checkfirst=True)
                logger.info(f"Created index: {index.name}")
            except Exception as e:
                logger.warning(f"Index {index.name} may already exist: {e}")
        
        db.commit()
        logger.info("All indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        db.rollback()
        raise


def analyze_query_performance(db: Session, query: str):
    """Analyze query performance using EXPLAIN."""
    try:
        result = db.execute(text(f"EXPLAIN ANALYZE {query}"))
        return result.fetchall()
    except Exception as e:
        logger.error(f"Query analysis error: {e}")
        return None


def get_table_stats(db: Session):
    """Get table statistics for monitoring."""
    try:
        stats = {}
        
        tables = ["customers", "conversations", "messages", "orders", "products", "bookings"]
        
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            stats[table] = count
        
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {}


def optimize_queries(db: Session):
    """Run VACUUM and ANALYZE for query optimization."""
    try:
        db.execute(text("VACUUM"))
        db.execute(text("ANALYZE"))
        db.commit()
        logger.info("Database optimized")
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        db.rollback()
