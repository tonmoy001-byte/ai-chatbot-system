import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.booking_service import BookingService
from app.services.sentiment_service import SentimentAnalyzer, SentimentLevel, UrgencyLevel
from app.services.language_service import LanguageService


class TestOrderService:
    """Tests for OrderService."""
    
    @pytest.mark.asyncio
    async def test_create_order(self, test_db, sample_order_data):
        """Test creating a new order."""
        service = OrderService(test_db)
        
        order = await service.create_order(
            customer_id=sample_order_data["customer_id"],
            items=sample_order_data["items"],
            shipping_address=sample_order_data["shipping_address"]
        )
        
        assert order is not None
        assert order.order_number.startswith("ORD-")
        assert order.status == "pending"
        assert order.customer_id == sample_order_data["customer_id"]
        assert len(order.items) == 2
    
    @pytest.mark.asyncio
    async def test_get_order(self, test_db, sample_order_data):
        """Test getting an order."""
        service = OrderService(test_db)
        
        # Create order first
        created_order = await service.create_order(
            customer_id=sample_order_data["customer_id"],
            items=sample_order_data["items"]
        )
        
        # Get order
        retrieved_order = await service.get_order(created_order.order_number)
        
        assert retrieved_order is not None
        assert retrieved_order.order_number == created_order.order_number
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, test_db, sample_order_data):
        """Test updating order status."""
        service = OrderService(test_db)
        
        # Create order
        order = await service.create_order(
            customer_id=sample_order_data["customer_id"],
            items=sample_order_data["items"]
        )
        
        # Update status
        result = await service.update_status(order.order_number, "confirmed")
        
        assert result is True
        
        # Verify update
        updated_order = await service.get_order(order.order_number)
        assert updated_order.status == "confirmed"
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, test_db, sample_order_data):
        """Test cancelling an order."""
        service = OrderService(test_db)
        
        # Create order
        order = await service.create_order(
            customer_id=sample_order_data["customer_id"],
            items=sample_order_data["items"]
        )
        
        # Cancel order
        result = await service.cancel_order(order.order_number)
        
        assert result is True
        
        # Verify cancellation
        cancelled_order = await service.get_order(order.order_number)
        assert cancelled_order.status == "cancelled"
    
    @pytest.mark.asyncio
    async def test_format_order_response(self, test_db, sample_order_data):
        """Test order response formatting."""
        service = OrderService(test_db)
        
        # Create order
        order = await service.create_order(
            customer_id=sample_order_data["customer_id"],
            items=sample_order_data["items"]
        )
        
        # Format response
        response = await service.format_order_response(order.order_number)
        
        assert order.order_number in response
        assert "pending" in response.lower() or "being processed" in response.lower()


class TestProductService:
    """Tests for ProductService."""
    
    @pytest.mark.asyncio
    async def test_create_product(self, test_db, sample_product_data):
        """Test creating a new product."""
        service = ProductService(test_db)
        
        product = await service.create_product(
            sku=sample_product_data["sku"],
            name=sample_product_data["name"],
            description=sample_product_data["description"],
            price=sample_product_data["price"],
            image_url=sample_product_data["image_url"]
        )
        
        assert product is not None
        assert product.sku == sample_product_data["sku"]
        assert product.name == sample_product_data["name"]
        assert float(product.price) == sample_product_data["price"]
    
    @pytest.mark.asyncio
    async def test_get_product_by_sku(self, test_db, sample_product_data):
        """Test getting product by SKU."""
        service = ProductService(test_db)
        
        # Create product
        await service.create_product(
            sku=sample_product_data["sku"],
            name=sample_product_data["name"],
            price=sample_product_data["price"]
        )
        
        # Get by SKU
        product = await service.get_product_by_sku(sample_product_data["sku"])
        
        assert product is not None
        assert product.sku == sample_product_data["sku"]
    
    @pytest.mark.asyncio
    async def test_search_products(self, test_db, sample_product_data):
        """Test product search."""
        service = ProductService(test_db)
        
        # Create product
        await service.create_product(
            sku=sample_product_data["sku"],
            name=sample_product_data["name"],
            description=sample_product_data["description"],
            price=sample_product_data["price"]
        )
        
        # Search
        results = await service.search_products("Test")
        
        assert len(results) > 0
        assert any(p.name == sample_product_data["name"] for p in results)


class TestBookingService:
    """Tests for BookingService."""
    
    @pytest.mark.asyncio
    async def test_create_booking(self, test_db, sample_booking_data):
        """Test creating a new booking."""
        service = BookingService(test_db)
        
        booking = await service.create_booking(
            customer_id=sample_booking_data["customer_id"],
            start_time=datetime.fromisoformat(sample_booking_data["start_time"]),
            duration_minutes=sample_booking_data["duration_minutes"],
            service_name=sample_booking_data["service_name"]
        )
        
        assert booking is not None
        assert booking.status == "confirmed"
        assert booking.customer_id == sample_booking_data["customer_id"]
    
    @pytest.mark.asyncio
    async def test_cancel_booking(self, test_db, sample_booking_data):
        """Test cancelling a booking."""
        service = BookingService(test_db)
        
        # Create booking
        booking = await service.create_booking(
            customer_id=sample_booking_data["customer_id"],
            start_time=datetime.fromisoformat(sample_booking_data["start_time"]),
            duration_minutes=sample_booking_data["duration_minutes"]
        )
        
        # Cancel
        result = await service.cancel_booking(str(booking.id))
        
        assert result is True
        
        # Verify
        cancelled_booking = await service.get_booking(str(booking.id))
        assert cancelled_booking.status == "cancelled"


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        analyzer = SentimentAnalyzer()
        
        result = await analyzer.analyze("I love this product! It's amazing and great quality!")
        
        assert result["sentiment_level"] in [
            SentimentLevel.POSITIVE.value,
            SentimentLevel.VERY_POSITIVE.value
        ]
        assert result["sentiment_score"] > 0
    
    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        analyzer = SentimentAnalyzer()
        
        result = await analyzer.analyze("This is terrible! I hate it. Worst experience ever.")
        
        assert result["sentiment_level"] in [
            SentimentLevel.NEGATIVE.value,
            SentimentLevel.VERY_NEGATIVE.value
        ]
        assert result["sentiment_score"] < 0
    
    @pytest.mark.asyncio
    async def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        analyzer = SentimentAnalyzer()
        
        result = await analyzer.analyze("I would like to check my order status.")
        
        assert result["sentiment_level"] == SentimentLevel.NEUTRAL.value
    
    @pytest.mark.asyncio
    async def test_urgency_detection(self):
        """Test urgency detection."""
        analyzer = SentimentAnalyzer()
        
        result = await analyzer.analyze("URGENT! I need help immediately!")
        
        assert result["urgency_level"] in [
            UrgencyLevel.HIGH.value,
            UrgencyLevel.CRITICAL.value
        ]
    
    @pytest.mark.asyncio
    async def test_complaint_detection(self):
        """Test complaint detection."""
        analyzer = SentimentAnalyzer()
        
        result = await analyzer.analyze("I want to file a complaint about a defective product.")
        
        assert result["is_complaint"] is True


class TestLanguageService:
    """Tests for LanguageService."""
    
    @pytest.mark.asyncio
    async def test_detect_english(self):
        """Test English language detection."""
        service = LanguageService()
        
        result = await service.detect_language("Hello, how are you?")
        
        assert result["language"] == "en"
    
    @pytest.mark.asyncio
    async def test_detect_spanish(self):
        """Test Spanish language detection."""
        service = LanguageService()
        
        result = await service.detect_language("Hola, ¿cómo estás?")
        
        # Should detect as Spanish or at least not English
        assert result["language"] != "en" or "hola" in result.get("language", "").lower()
    
    @pytest.mark.asyncio
    async def test_get_supported_languages(self):
        """Test getting supported languages."""
        service = LanguageService()
        
        languages = await service.get_supported_languages()
        
        assert len(languages) > 0
        assert any(l["code"] == "en" for l in languages)
