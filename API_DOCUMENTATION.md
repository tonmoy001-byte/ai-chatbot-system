# AI Chatbot System - API Documentation

## Overview

This is the API documentation for the AI Chatbot System, an automated customer service platform for Facebook and Instagram.

**Base URL:** `http://localhost:8000`

**Authentication:** API Key (in development, auth is disabled)

---

## Endpoints

### Health & Monitoring

#### Health Check
```
GET /health
```

Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "cache_status": "connected"
}
```

#### Metrics (Prometheus)
```
GET /metrics
```

Returns Prometheus metrics for monitoring.

---

### Webhooks

#### Facebook Webhook Verification
```
GET /webhooks/facebook
```

**Parameters:**
- `hub.mode` (string): Must be "subscribe"
- `hub.verify_token` (string): Your verification token
- `hub.challenge` (string): Challenge string

#### Facebook Webhook
```
POST /webhooks/facebook
```

Receives Facebook messages and events.

**Headers:**
- `X-Hub-Signature`: HMAC signature for verification

**Body:** Facebook webhook payload

#### Instagram Webhook
```
POST /webhooks/instagram
```

Receives Instagram messages and events.

---

### Orders

#### List Orders
```
GET /api/orders
```

**Query Parameters:**
- `limit` (int): Max orders to return (default: 50)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "orders": [
    {
      "id": "uuid",
      "order_number": "ORD-123456",
      "status": "pending",
      "customer_id": "uuid",
      "total": 99.99,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

#### Create Order
```
POST /api/orders
```

**Body:**
```json
{
  "customer_id": "uuid",
  "items": [
    {
      "name": "Product Name",
      "price": 29.99,
      "quantity": 2
    }
  ],
  "shipping_address": {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001"
  }
}
```

**Response:** `201 Created`
```json
{
  "order_number": "ORD-123456",
  "message": "Order created successfully"
}
```

#### Get Order
```
GET /api/orders/{order_number}
```

#### Update Order Status
```
PATCH /api/orders/{order_number}/status
```

**Body:**
```json
{
  "status": "confirmed"
}
```

**Valid statuses:** `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled`

#### Cancel Order
```
DELETE /api/orders/{order_number}
```

---

### Products

#### List Products
```
GET /api/products
```

**Query Parameters:**
- `limit` (int): Max products (default: 50)
- `offset` (int): Pagination offset

#### Create Product
```
POST /api/products
```

**Body:**
```json
{
  "sku": "PROD-001",
  "name": "Product Name",
  "description": "Product description",
  "price": 29.99,
  "image_url": "https://example.com/image.jpg",
  "metadata": {
    "category": "electronics"
  }
}
```

#### Get Product
```
GET /api/products/{product_id}
```

#### Get Product by SKU
```
GET /api/products/sku/{sku}
```

#### Update Product
```
PUT /api/products/{product_id}
```

#### Delete Product
```
DELETE /api/products/{product_id}
```

#### Search Products
```
GET /api/products/search/{query}
```

#### Get Products by Price Range
```
GET /api/products/price-range/
```

**Query Parameters:**
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price

---

### Bookings

#### List Bookings
```
GET /api/bookings
```

#### Create Booking
```
POST /api/bookings
```

**Body:**
```json
{
  "customer_id": "uuid",
  "start_time": "2024-01-15T10:00:00Z",
  "duration_minutes": 30,
  "service_name": "Consultation"
}
```

#### Get Booking
```
GET /api/bookings/{booking_id}
```

#### Cancel Booking
```
DELETE /api/bookings/{booking_id}
```

---

### Calendar

#### Get Google OAuth URL
```
GET /calendar/auth/url
```

#### OAuth Callback
```
GET /calendar/callback
```

#### Get Available Slots
```
GET /calendar/availability
```

**Query Parameters:**
- `date` (string): Date in YYYY-MM-DD format
- `duration` (int): Duration in minutes

#### List Events
```
GET /calendar/events
```

---

### Analytics

#### Dashboard Stats
```
GET /analytics/dashboard
```

**Response:**
```json
{
  "total_conversations": 1234,
  "active_conversations": 56,
  "total_orders": 789,
  "total_revenue": 12345.67,
  "conversations_today": 45,
  "orders_today": 12,
  "revenue_today": 1234.56
}
```

#### Conversation Analytics
```
GET /analytics/conversations
```

#### Message Analytics
```
GET /analytics/messages
```

#### Order Analytics
```
GET /analytics/orders
```

#### Peak Hours
```
GET /analytics/peak-hours
```

#### Recent Activity
```
GET /analytics/activity
```

---

### Admin Dashboard

#### Dashboard
```
GET /admin/
```

Renders the admin dashboard HTML page.

#### Conversations List
```
GET /admin/conversations
```

#### Conversation Detail
```
GET /admin/conversations/{conversation_id}
```

---

## WebSocket

### Real-time Conversation Updates
```
ws://localhost:8000/ws/conversations/{conversation_id}
```

Connect to receive real-time updates for a specific conversation.

**Events:**
```json
{
  "type": "new_message",
  "data": {
    "id": "uuid",
    "content": "Hello!",
    "sender_type": "customer",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## Error Handling

All errors return a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Error Codes:**
- `CONVERSATION_NOT_FOUND` (404)
- `ORDER_NOT_FOUND` (404)
- `PRODUCT_NOT_FOUND` (404)
- `BOOKING_NOT_FOUND` (404)
- `WEBHOOK_VERIFICATION_FAILED` (403)
- `VALIDATION_ERROR` (422)
- `RATE_LIMIT_EXCEEDED` (429)
- `INTERNAL_SERVER_ERROR` (500)

---

## Rate Limiting

API endpoints are rate-limited to 100 requests per minute per IP address.

When rate limited, you'll receive a `429 Too Many Requests` response.

---

## Pagination

Most list endpoints support pagination via `limit` and `offset` query parameters:

```
GET /api/orders?limit=20&offset=40
```

This returns orders 41-60.

---

## Webhooks

### Facebook Setup

1. Go to Facebook Developers Portal
2. Create a new app or use existing
3. Add Facebook Login product
4. Set webhook URL: `https://your-domain.com/webhooks/facebook`
5. Subscribe to: `messages`, `messaging_postbacks`, `messaging_optins`
6. Verify token: Your `FACEBOOK_VERIFY_TOKEN` env var

### Instagram Setup

1. Go to Facebook Developers Portal (Instagram uses Facebook's API)
2. Add Instagram Graph API product
3. Set webhook URL: `https://your-domain.com/webhooks/instagram`
4. Subscribe to: `messages`

---

## Environment Variables

See `.env.example` for all required configuration variables.
