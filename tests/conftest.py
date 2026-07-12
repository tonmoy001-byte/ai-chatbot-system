import pytest
from unittest.mock import MagicMock, AsyncMock
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_facebook_service():
    """Mock Facebook service."""
    with MagicMock() as mock:
        mock.send_text = AsyncMock(return_value={"message_id": "test_msg_123"})
        mock.send_image = AsyncMock(return_value=True)
        mock.process_event = AsyncMock(return_value="Test response")
        yield mock


@pytest.fixture
def mock_instagram_service():
    """Mock Instagram service."""
    with MagicMock() as mock:
        mock.send_text = AsyncMock(return_value={"message_id": "test_msg_123"})
        mock.send_image = AsyncMock(return_value=True)
        mock.process_event = AsyncMock(return_value="Test response")
        yield mock


@pytest.fixture
def mock_ai_engine():
    """Mock AI engine."""
    with MagicMock() as mock:
        mock.generate_response = AsyncMock(return_value="AI generated response")
        mock.analyze_intent = AsyncMock(return_value="question")
        mock.extract_entities = AsyncMock(return_value={"order_numbers": [], "products": []})
        yield mock


@pytest.fixture
def mock_calendar_service():
    """Mock Calendar service."""
    with MagicMock() as mock:
        mock.create_event = AsyncMock(return_value={"id": "event_123"})
        mock.update_event = AsyncMock(return_value={"id": "event_123"})
        mock.delete_event = AsyncMock(return_value=True)
        mock.get_available_slots = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def sample_customer_data():
    """Sample customer data for tests."""
    return {
        "platform": "facebook",
        "platform_user_id": "test_user_123",
        "name": "Test Customer",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for tests."""
    return {
        "customer_id": "test_customer_123",
        "items": [
            {"name": "Product 1", "price": 29.99, "quantity": 2},
            {"name": "Product 2", "price": 49.99, "quantity": 1}
        ],
        "shipping_address": {
            "name": "Test Customer",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "zip": "12345"
        }
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for tests."""
    return {
        "sku": "TEST-001",
        "name": "Test Product",
        "description": "A test product for testing purposes",
        "price": 29.99,
        "image_url": "https://example.com/image.jpg"
    }


@pytest.fixture
def sample_booking_data():
    """Sample booking data for tests."""
    from datetime import datetime, timedelta
    return {
        "customer_id": "test_customer_123",
        "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "duration_minutes": 30,
        "service_name": "Test Appointment"
    }
