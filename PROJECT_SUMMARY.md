# AI Chatbot System - Project Summary

## Overview

The AI Chatbot System is a production-ready SaaS platform that automates customer service for businesses across Facebook and Instagram. It uses AI (GPT-4) to handle conversations, process orders, manage bookings, and provide analytics.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer (Nginx)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                          FastAPI App                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Webhooks │ │ REST API │ │ WebSocket│ │ Admin Dashboard  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         Services Layer                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ AI Engine│ │ Orders   │ │ Bookings │ │ Voice/Language   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Sentiment│ │Analytics │ │ Calendar │ │ Notifications    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │PostgreSQL│ │  Redis   │ │ Celery   │ │ OpenAI API       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI |
| **Database** | PostgreSQL 15+ |
| **Cache** | Redis 7+ |
| **Task Queue** | Celery |
| **AI** | OpenAI GPT-4, Whisper |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Web Server** | Nginx |
| **Social Platforms** | Facebook Graph API v18.0, Instagram Graph API |
| **Calendar** | Google Calendar API v3 |

---

## Features

### Core Features
- **Multi-platform messaging** - Facebook and Instagram
- **AI-powered responses** - GPT-4 for natural conversations
- **Voice message processing** - Whisper API transcription
- **Multi-language support** - 13+ languages with auto-detection

### Order Management
- **Order tracking** - Full order lifecycle
- **Product catalog** - Search, price ranges, images
- **Order notifications** - Confirmation, shipping, delivery

### Booking System
- **Google Calendar integration** - OAuth 2.0 flow
- **Appointment scheduling** - Available slots, booking management
- **Automated reminders** - Email and SMS via Celery

### Analytics & Intelligence
- **Sentiment analysis** - Real-time mood detection
- **Auto-escalation** - Negative sentiment triggers human handoff
- **Dashboard analytics** - Conversations, orders, revenue
- **Peak hours analysis** - Traffic patterns

### Security & Performance
- **Rate limiting** - IP-based request throttling
- **Input sanitization** - SQL injection, XSS protection
- **Security headers** - CSP, HSTS, X-Frame-Options
- **Redis caching** - Performance optimization
- **GZip compression** - Reduced payload size

---

## Project Structure

```
chatbot-system/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── admin.py           # Admin dashboard routes
│   │   ├── analytics.py       # Analytics endpoints
│   │   ├── auth.py            # Authentication
│   │   ├── bookings.py        # Booking CRUD
│   │   ├── calendar.py        # Google Calendar
│   │   ├── monitoring.py      # Health, metrics
│   │   ├── orders.py          # Order CRUD
│   │   ├── products.py        # Product CRUD
│   │   └── webhooks.py        # Facebook/Instagram webhooks
│   ├── middleware/             # Request middleware
│   │   ├── __init__.py
│   │   └── security.py        # Security middleware
│   ├── models/                 # Database models
│   │   ├── booking.py
│   │   ├── conversation.py
│   │   ├── customer.py
│   │   ├── order.py
│   │   └── product.py
│   ├── services/               # Business logic
│   │   ├── ai_engine.py       # OpenAI GPT-4 integration
│   │   ├── analytics_service.py
│   │   ├── booking_service.py
│   │   ├── calendar_service.py
│   │   ├── conversation_service.py
│   │   ├── escalation_service.py
│   │   ├── facebook.py        # Facebook Graph API
│   │   ├── image_service.py
│   │   ├── instagram.py       # Instagram Graph API
│   │   ├── language_service.py
│   │   ├── message_router.py
│   │   ├── notification_service.py
│   │   ├── order_service.py
│   │   ├── product_service.py
│   │   ├── sentiment_service.py
│   │   └── voice_processor.py
│   ├── templates/              # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── conversation_detail.html
│   │   └── conversations.html
│   ├── tasks/                  # Celery tasks
│   │   ├── booking_tasks.py
│   │   └── message_tasks.py
│   ├── cache.py               # Redis caching
│   ├── config.py              # Settings
│   ├── database.py            # DB connection
│   ├── database_optimization.py
│   ├── errors.py              # Error handlers
│   ├── logging_config.py      # Structured logging
│   ├── main.py                # App entry point
│   └── monitoring/
│       └── performance.py     # Prometheus metrics
├── tests/                     # Test suite
│   ├── integration/
│   │   └── test_api.py
│   ├── unit/
│   │   └── test_services.py
│   ├── conftest.py
│   └── test_basic.py
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
├── alembic/                   # Database migrations
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
├── Dockerfile
├── Dockerfile.worker
├── nginx.conf
├── requirements.txt
├── .env.example
├── API_DOCUMENTATION.md
├── DEPLOYMENT.md
└── README.md
```

---

## Database Schema

### Customers
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| platform | String | facebook/instagram |
| platform_user_id | String | Platform user ID |
| name | String | Customer name |
| email | String | Email address |
| phone | String | Phone number |
| created_at | Timestamp | Creation time |

### Conversations
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| customer_id | UUID | FK to customers |
| status | String | active/escalated/resolved |
| started_at | Timestamp | Start time |
| last_message_at | Timestamp | Last activity |
| extra_data | JSON | Additional data |

### Messages
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| conversation_id | UUID | FK to conversations |
| sender_type | String | customer/bot/agent |
| content_type | String | text/image/voice |
| content | Text | Message content |
| media_url | String | Media attachment |
| created_at | Timestamp | Send time |

### Orders
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| order_number | String | ORD-XXXXXX |
| customer_id | UUID | FK to customers |
| status | String | pending/confirmed/shipped |
| items | JSON | Order items |
| total | Decimal | Order total |
| created_at | Timestamp | Order time |

### Products
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sku | String | Unique SKU |
| name | String | Product name |
| description | Text | Description |
| price | Decimal | Price |
| image_url | String | Product image |

### Bookings
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| customer_id | UUID | FK to customers |
| start_time | Timestamp | Appointment time |
| duration_minutes | Integer | Duration |
| status | String | confirmed/cancelled |
| google_event_id | String | Google Calendar event |

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/` | API root |
| POST | `/webhooks/facebook` | Facebook webhook |
| POST | `/webhooks/instagram` | Instagram webhook |
| GET/POST | `/api/orders` | List/Create orders |
| GET | `/api/orders/{number}` | Get order |
| PATCH | `/api/orders/{number}/status` | Update status |
| DELETE | `/api/orders/{number}` | Cancel order |
| GET/POST | `/api/products` | List/Create products |
| GET | `/api/products/{id}` | Get product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |
| GET | `/api/products/sku/{sku}` | Get by SKU |
| GET | `/api/products/search/{q}` | Search products |
| GET/POST | `/api/bookings` | List/Create bookings |
| GET | `/api/bookings/{id}` | Get booking |
| DELETE | `/api/bookings/{id}` | Cancel booking |
| GET | `/calendar/auth/url` | OAuth URL |
| GET | `/calendar/availability` | Available slots |
| GET | `/analytics/dashboard` | Dashboard stats |
| GET | `/analytics/conversations` | Conversation analytics |
| GET | `/analytics/messages` | Message analytics |
| GET | `/analytics/orders` | Order analytics |
| GET | `/analytics/peak-hours` | Peak hours |
| GET | `/analytics/activity` | Recent activity |
| GET | `/admin/` | Admin dashboard |
| WS | `/ws/conversations/{id}` | Real-time updates |

---

## Development Phases Completed

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (structure, DB, auth) | ✅ |
| 2 | Core Integration (webhooks, AI) | ✅ |
| 3 | MVP (dashboard, CI/CD, monitoring) | ✅ |
| 4 | Order Management (orders, products) | ✅ |
| 5 | Calendar (bookings, reminders) | ✅ |
| 6 | Advanced (voice, sentiment, analytics) | ✅ |
| 7 | Testing (tests, security, deployment) | ✅ |
| 8 | Polish (logging, errors, caching, docs) | ✅ |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Files | 70+ |
| API Endpoints | 50+ |
| Services | 20+ |
| Database Models | 6 |
| Tests | 14 (all passing) |
| Middleware | 5 |
| Templates | 4 |
| Celery Tasks | 10+ |
