import redis
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
from app.config import get_settings
import hashlib

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """Redis-based caching service."""
    
    def __init__(self):
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis.ping()
            self.enabled = True
            logger.info("Redis cache connected")
        except redis.ConnectionError:
            logger.warning("Redis not available, caching disabled")
            self.redis = None
            self.enabled = False
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            self.redis = None
            self.enabled = False
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]
        
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}={v}")
        
        key = ":".join(key_parts)
        
        # Hash long keys
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:hash:{key_hash}"
        
        return key
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        if not self.enabled:
            return None
        
        try:
            return self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a key."""
        if not self.enabled:
            return False
        
        try:
            return self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False


# Global cache instance
cache = CacheService()


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                await cache.set(key, result, ttl)
                logger.debug(f"Cache set: {key}")
            
            return result
        
        return wrapper
    return decorator


class CacheKeys:
    """Cache key constants."""
    
    # Conversation keys
    CONVERSATION = "conversation:{conversation_id}"
    CONVERSATION_MESSAGES = "conversation:{conversation_id}:messages"
    
    # Order keys
    ORDER = "order:{order_number}"
    ORDERS_BY_CUSTOMER = "orders:customer:{customer_id}"
    
    # Product keys
    PRODUCT = "product:{product_id}"
    PRODUCT_BY_SKU = "product:sku:{sku}"
    PRODUCTS_SEARCH = "products:search:{query}"
    
    # Booking keys
    BOOKING = "booking:{booking_id}"
    BOOKINGS_BY_CUSTOMER = "bookings:customer:{customer_id}"
    
    # Analytics keys
    DASHBOARD_STATS = "analytics:dashboard"
    CONVERSATION_ANALYTICS = "analytics:conversations"
    ORDER_ANALYTICS = "analytics:orders"
    
    # Rate limiting
    RATE_LIMIT = "ratelimit:{identifier}"
