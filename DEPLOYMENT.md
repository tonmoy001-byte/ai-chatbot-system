# Deployment Checklist

## Pre-Deployment

### Environment Variables
- [ ] `SECRET_KEY` - Generate a strong random secret
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `REDIS_URL` - Redis connection string
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `FACEBOOK_PAGE_ACCESS_TOKEN` - Facebook page token
- [ ] `FACEBOOK_VERIFY_TOKEN` - Webhook verification token
- [ ] `INSTAGRAM_ACCESS_TOKEN` - Instagram API token
- [ ] `GOOGLE_CLIENT_ID` - Google OAuth client ID
- [ ] `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- [ ] `ENVIRONMENT` - Set to "production"

### Security
- [ ] Generate new SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Verify HTTPS is enabled
- [ ] Check CORS origins are restricted
- [ ] Verify rate limiting is configured
- [ ] Test input validation

### Database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify database connections
- [ ] Check connection pool settings

### Docker
- [ ] Build production images: `docker-compose -f docker-compose.prod.yml build`
- [ ] Verify all services start correctly
- [ ] Check logs for errors

## Deployment Steps

### 1. Build and Deploy
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 2. Verify Services
```bash
# Check API health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### 3. Test Endpoints
- [ ] Health check: `GET /health`
- [ ] Admin dashboard: `GET /admin/`
- [ ] Webhook verification: `GET /webhooks/facebook`
- [ ] Orders API: `GET /api/orders`
- [ ] Products API: `GET /api/products`
- [ ] Bookings API: `GET /api/bookings`
- [ ] Analytics: `GET /analytics/dashboard`

### 4. Monitor
- [ ] Check Prometheus metrics
- [ ] Monitor error rates
- [ ] Verify response times
- [ ] Check resource usage

## Post-Deployment

### Verification
- [ ] Test Facebook webhook with sample message
- [ ] Test Instagram webhook
- [ ] Test order creation flow
- [ ] Test booking creation flow
- [ ] Verify AI responses
- [ ] Test sentiment analysis
- [ ] Test analytics dashboard

### Monitoring
- [ ] Set up alerting rules
- [ ] Configure log aggregation
- [ ] Monitor API response times
- [ ] Track error rates
- [ ] Monitor database performance

### Backup
- [ ] Schedule database backups
- [ ] Test backup restoration
- [ ] Document backup procedures

## Rollback Plan

### If issues occur:
1. Stop current deployment
2. Rollback to previous version
3. Restore database if needed
4. Verify services are running

### Commands:
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Rollback to previous image
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Security Checklist

### Network
- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Port 80/443 open
- [ ] Internal services not exposed

### Application
- [ ] Debug mode disabled
- [ ] Error messages don't expose internals
- [ ] Input validation enabled
- [ ] Rate limiting active
- [ ] CORS properly configured

### Database
- [ ] Strong password used
- [ ] Limited database user privileges
- [ ] Database not publicly accessible
- [ ] Connection pooling configured

### Secrets
- [ ] All secrets in environment variables
- [ ] No secrets in code
- [ ] No secrets in logs
- [ ] Regular secret rotation

## Performance

### Optimization
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching enabled (Redis)
- [ ] Static files served via CDN
- [ ] Gzip compression enabled

### Monitoring
- [ ] Response time monitoring
- [ ] Error rate monitoring
- [ ] Resource usage monitoring
- [ ] Database performance monitoring

## Troubleshooting

### Common Issues

**Service won't start:**
- Check environment variables
- Check database connection
- Check Redis connection
- Review logs

**Webhook not receiving messages:**
- Verify webhook URL is correct
- Check SSL certificate
- Verify tokens
- Check Facebook/Instagram app settings

**AI not responding:**
- Verify OpenAI API key
- Check API quota
- Review AI engine logs

**Database errors:**
- Check connection pool
- Verify migrations
- Check for deadlocks

### Log Locations
- API logs: `docker-compose -f docker-compose.prod.yml logs api`
- Worker logs: `docker-compose -f docker-compose.prod.yml logs worker`
- Database logs: `docker-compose -f docker-compose.prod.yml logs db`
- Redis logs: `docker-compose -f docker-compose.prod.yml logs redis`
