# AI Chatbot System

An automated AI chatbot system for businesses to handle customer messages across Facebook and Instagram, with order management, calendar booking, voice processing, and advanced analytics.

## Features

- **Multi-platform messaging** - Facebook and Instagram integration
- **AI-powered responses** - GPT-4 for natural conversations
- **Voice message processing** - Whisper API transcription
- **Multi-language support** - 13+ languages with auto-detection
- **Order management** - Full order lifecycle tracking
- **Product catalog** - Search, price ranges, images
- **Booking system** - Google Calendar integration
- **Sentiment analysis** - Real-time mood detection
- **Auto-escalation** - Negative sentiment triggers human handoff
- **Analytics dashboard** - Conversations, orders, revenue
- **Admin dashboard** - Real-time conversation monitoring

## Tech Stack

- **Backend:** Python 3.11+, FastAPI
- **Database:** PostgreSQL 15+
- **Cache:** Redis 7+
- **Task Queue:** Celery
- **AI:** OpenAI GPT-4, Whisper
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Web Server:** Nginx

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)
- Facebook Developer Account
- Instagram Developer Account
- OpenAI API Key
- Google Cloud Project (for Calendar API)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd chatbot-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
copy .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Application
APP_NAME=AI Chatbot System
DEBUG=true
ENVIRONMENT=development

# Database (Supabase only)
# Direct connection: postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
# Session pooler:    postgres://postgres.[PROJECT-REF]:[PASSWORD]@aws-[REGION].pooler.supabase.com:5432/postgres
DATABASE_URL=your_supabase_connection_string

# Redis
REDIS_URL=redis://localhost:6379

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_VERIFY_TOKEN=your_verify_token
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token

# Instagram
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Google Calendar
GOOGLE_CALENDAR_CLIENT_ID=your_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_client_secret

# Security (generate new values for production)
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

### 5. Set Up Database

```bash
# Create PostgreSQL database
createdb chatbot

# Run migrations
alembic upgrade head
```

### 6. Start the Application

```bash
# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in separate terminal)
celery -A app.tasks worker --loglevel=info

# Start Celery beat for scheduled tasks (in separate terminal)
celery -A app.tasks beat --loglevel=info
```

### 7. Access the Application

- **API:** http://localhost:8000
- **Admin Dashboard:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Docker Setup

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Facebook Setup

1. Go to [Facebook Developers Portal](https://developers.facebook.com/)
2. Create a new app or use existing
3. Add **Facebook Login** product
4. Go to **Webhooks** section
5. Set callback URL: `https://your-domain.com/webhooks/facebook`
6. Enter your `FACEBOOK_VERIFY_TOKEN`
7. Subscribe to events: `messages`, `messaging_postbacks`, `messaging_optins`
8. Generate a Page Access Token

## Instagram Setup

1. Go to [Facebook Developers Portal](https://developers.facebook.com/)
2. Add **Instagram Graph API** product
3. Go to **Webhooks** section
4. Set callback URL: `https://your-domain.com/webhooks/instagram`
5. Subscribe to events: `messages`

## Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Set redirect URI: `https://your-domain.com/calendar/callback`
6. Copy Client ID and Client Secret to `.env`

## API Endpoints

### Health & Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Webhooks
- `GET /webhooks/facebook` - Facebook verification
- `POST /webhooks/facebook` - Facebook messages
- `POST /webhooks/instagram` - Instagram messages

### Orders
- `GET /api/orders` - List orders
- `POST /api/orders` - Create order
- `GET /api/orders/{number}` - Get order
- `PATCH /api/orders/{number}/status` - Update status
- `DELETE /api/orders/{number}` - Cancel order

### Products
- `GET /api/products` - List products
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `GET /api/products/search/{q}` - Search products

### Bookings
- `GET /api/bookings` - List bookings
- `POST /api/bookings` - Create booking
- `GET /api/bookings/{id}` - Get booking
- `DELETE /api/bookings/{id}` - Cancel booking

### Analytics
- `GET /analytics/dashboard` - Dashboard stats
- `GET /analytics/conversations` - Conversation analytics
- `GET /analytics/messages` - Message analytics
- `GET /analytics/orders` - Order analytics
- `GET /analytics/peak-hours` - Peak hours

### Admin
- `GET /admin/` - Admin dashboard

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage
python -m pytest tests/ --cov=app
```

## Project Structure

```
chatbot-system/
├── app/
│   ├── api/               # API endpoints
│   ├── middleware/         # Request middleware
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── templates/         # HTML templates
│   ├── tasks/             # Celery tasks
│   └── monitoring/        # Metrics & monitoring
├── tests/                 # Test suite
├── alembic/               # Database migrations
├── .github/workflows/     # CI/CD
├── docker-compose.yml     # Development
├── docker-compose.prod.yml # Production
├── Dockerfile
├── nginx.conf
└── requirements.txt
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | AI Chatbot System |
| `DEBUG` | Debug mode | true |
| `ENVIRONMENT` | Environment | development |
| `DATABASE_URL` | PostgreSQL URL | - |
| `REDIS_URL` | Redis URL | redis://localhost:6379 |
| `FACEBOOK_APP_ID` | Facebook App ID | - |
| `FACEBOOK_APP_SECRET` | Facebook App Secret | - |
| `FACEBOOK_VERIFY_TOKEN` | Webhook verify token | - |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Page access token | - |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram token | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GOOGLE_CALENDAR_CLIENT_ID` | Google OAuth client ID | - |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | Google OAuth secret | - |
| `SECRET_KEY` | JWT secret key | - |
| `ENCRYPTION_KEY` | Data encryption key | - |
| `LOG_LEVEL` | Logging level | INFO |

## License

MIT License

## Support

For issues and questions, please open an issue on the repository.
