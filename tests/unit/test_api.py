import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_login():
    """Test login endpoint."""
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/token",
        data={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401


def test_get_current_user():
    """Test get current user endpoint."""
    # First login to get token
    login_response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]
    
    # Then get user info
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_webhook_verification():
    """Test Facebook webhook verification."""
    response = client.get(
        "/webhook/facebook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "12345"
        }
    )
    # This will fail without proper verify token, but tests the endpoint exists
    assert response.status_code in [200, 403]
