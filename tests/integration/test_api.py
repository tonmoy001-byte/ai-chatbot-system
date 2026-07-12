import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


class TestWebhookEndpoints:
    """Tests for webhook endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_webhook_verification(self, client):
        """Test Facebook webhook verification."""
        response = client.get(
            "/webhooks/facebook",
            params={"hub.mode": "subscribe", "hub.verify_token": "test_token", "hub.challenge": "test_challenge"}
        )
        # Should return challenge or error based on token validation
        assert response.status_code in [200, 403]


class TestOrdersEndpoints:
    """Tests for orders endpoints."""
    
    def test_get_orders(self, client):
        """Test getting all orders."""
        response = client.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_order(self, client, sample_order_data):
        """Test creating a new order."""
        response = client.post("/api/orders", json=sample_order_data)
        assert response.status_code == 201
        assert "order_number" in response.json()
    
    def test_get_order_by_number(self, client, sample_order_data):
        """Test getting order by order number."""
        # Create order first
        create_response = client.post("/api/orders", json=sample_order_data)
        order_number = create_response.json()["order_number"]
        
        # Get order
        response = client.get(f"/api/orders/{order_number}")
        assert response.status_code == 200
        assert response.json()["order_number"] == order_number
    
    def test_update_order_status(self, client, sample_order_data):
        """Test updating order status."""
        # Create order
        create_response = client.post("/api/orders", json=sample_order_data)
        order_number = create_response.json()["order_number"]
        
        # Update status
        response = client.patch(
            f"/api/orders/{order_number}/status",
            json={"status": "confirmed"}
        )
        assert response.status_code == 200
    
    def test_cancel_order(self, client, sample_order_data):
        """Test cancelling an order."""
        # Create order
        create_response = client.post("/api/orders", json=sample_order_data)
        order_number = create_response.json()["order_number"]
        
        # Cancel order
        response = client.delete(f"/api/orders/{order_number}")
        assert response.status_code == 200


class TestProductsEndpoints:
    """Tests for products endpoints."""
    
    def test_get_products(self, client):
        """Test getting all products."""
        response = client.get("/api/products")
        assert response.status_code == 200
    
    def test_create_product(self, client, sample_product_data):
        """Test creating a new product."""
        response = client.post("/api/products", json=sample_product_data)
        assert response.status_code == 201
    
    def test_search_products(self, client, sample_product_data):
        """Test searching products."""
        # Create product
        client.post("/api/products", json=sample_product_data)
        
        # Search
        response = client.get("/api/products/search", params={"q": "Test"})
        assert response.status_code == 200
    
    def test_get_product_by_sku(self, client, sample_product_data):
        """Test getting product by SKU."""
        # Create product
        client.post("/api/products", json=sample_product_data)
        
        # Get by SKU
        response = client.get(f"/api/products/sku/{sample_product_data['sku']}")
        assert response.status_code == 200


class TestBookingsEndpoints:
    """Tests for bookings endpoints."""
    
    def test_get_bookings(self, client):
        """Test getting all bookings."""
        response = client.get("/api/bookings")
        assert response.status_code == 200
    
    def test_create_booking(self, client, sample_booking_data):
        """Test creating a new booking."""
        response = client.post("/api/bookings", json=sample_booking_data)
        assert response.status_code == 201
    
    def test_get_booking_by_id(self, client, sample_booking_data):
        """Test getting booking by ID."""
        # Create booking
        create_response = client.post("/api/bookings", json=sample_booking_data)
        booking_id = create_response.json()["id"]
        
        # Get booking
        response = client.get(f"/api/bookings/{booking_id}")
        assert response.status_code == 200
    
    def test_cancel_booking(self, client, sample_booking_data):
        """Test cancelling a booking."""
        # Create booking
        create_response = client.post("/api/bookings", json=sample_booking_data)
        booking_id = create_response.json()["id"]
        
        # Cancel booking
        response = client.delete(f"/api/bookings/{booking_id}")
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""
    
    def test_get_dashboard_stats(self, client):
        """Test getting dashboard statistics."""
        response = client.get("/analytics/dashboard")
        assert response.status_code == 200
        assert "total_conversations" in response.json()
        assert "total_orders" in response.json()
    
    def test_get_conversation_analytics(self, client):
        """Test getting conversation analytics."""
        response = client.get("/analytics/conversations")
        assert response.status_code == 200
    
    def test_get_message_analytics(self, client):
        """Test getting message analytics."""
        response = client.get("/analytics/messages")
        assert response.status_code == 200
    
    def test_get_order_analytics(self, client):
        """Test getting order analytics."""
        response = client.get("/analytics/orders")
        assert response.status_code == 200
    
    def test_get_peak_hours(self, client):
        """Test getting peak hours."""
        response = client.get("/analytics/peak-hours")
        assert response.status_code == 200


class TestAdminEndpoints:
    """Tests for admin endpoints."""
    
    def test_admin_dashboard(self, client):
        """Test admin dashboard loads."""
        response = client.get("/admin/")
        assert response.status_code == 200
    
    def test_admin_conversations(self, client):
        """Test admin conversations page loads."""
        response = client.get("/admin/conversations")
        assert response.status_code == 200
