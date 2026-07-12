from app.api.webhooks import router as webhooks_router
from app.api.orders import router as orders_router
from app.api.bookings import router as bookings_router
from app.api.admin import router as admin_router

__all__ = ["webhooks_router", "orders_router", "bookings_router", "admin_router"]
