# Deployment Guide

## Overview

Complete deployment setup for the Sports Analytics FastAPI backend with Docker, docker-compose, and production-ready configuration.

## Quick Start

### Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f api

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Production

```bash
# Build and start production services
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Docker Setup

### Dockerfile

**Production Dockerfile** (`Dockerfile`):
- Multi-stage build for smaller image size
- Python 3.11 slim base image
- Non-root user for security
- Health checks included
- Optimized for production

**Development Dockerfile** (`Dockerfile.dev`):
- Single-stage build
- Hot reload enabled
- Development tools included

### Building Images

```bash
# Build production image
docker build -t sports-api:latest .

# Build development image
docker build -f Dockerfile.dev -t sports-api:dev .
```

## Docker Compose

### Services

1. **api** - FastAPI backend
2. **postgres** - PostgreSQL database
3. **redis** - Redis cache
4. **nginx** - Reverse proxy (optional)

### Development Setup

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Access API
curl http://localhost:8000/health
```

### Production Setup

```bash
# Copy and configure environment file
cp .env.production.example .env.production
# Edit .env.production with your values

# Start production services
docker-compose up -d --build

# Run migrations
docker-compose exec api alembic upgrade head

# Check service health
docker-compose ps
```

## Environment Variables

### Required Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Security (MUST CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-min-32-chars
ADMIN_TOKEN=your-admin-token

# Redis
REDIS_URL=redis://host:6379/0
```

### Optional Variables

```env
# Application
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60

# CORS
CORS_ORIGINS=["https://yourdomain.com"]
```

### Generating Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ADMIN_TOKEN
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Production Configuration

### FastAPI Settings

Production mode automatically:
- Disables debug mode
- Disables API documentation endpoints
- Enables structured JSON logging
- Sets appropriate log levels
- Configures worker processes

### Worker Configuration

```bash
# Run with multiple workers
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker
```

**Recommended workers**: `(2 × CPU cores) + 1`

### Database Connection Pooling

The application uses async SQLAlchemy with connection pooling:
- Automatic connection management
- Connection reuse
- Async operations

### Redis Configuration

- Connection pooling enabled
- Automatic reconnection
- Health checks

## Nginx Configuration

### Basic Setup

Nginx is included in docker-compose for reverse proxy:

```bash
# Start with nginx
docker-compose up -d

# Access via nginx
curl http://localhost/api/v1/health
```

### SSL/HTTPS Setup

1. Place SSL certificates in `nginx/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

2. Uncomment HTTPS server block in `nginx/nginx.conf`

3. Update server_name with your domain

4. Restart nginx:
```bash
docker-compose restart nginx
```

## Database Migrations

### Running Migrations

```bash
# Development
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Production
docker-compose exec api alembic upgrade head
```

### Creating New Migrations

```bash
# Development
docker-compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "description"

# Review and edit migration file
# Then apply
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

## Health Checks

### Application Health

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/api/v1/observability/health/detailed
```

### Docker Health Checks

All services include health checks:
- API: HTTP health endpoint
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Metrics

```bash
# Get metrics
curl http://localhost:8000/api/v1/observability/metrics

# Get errors (admin)
curl -H "Authorization: Bearer <admin-token>" \
     http://localhost:8000/api/v1/observability/errors
```

## Backup and Restore

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U sports_user sports_analytics > backup.sql

# Restore database
docker-compose exec -T postgres psql -U sports_user sports_analytics < backup.sql
```

### Redis Backup

```bash
# Backup Redis
docker-compose exec redis redis-cli SAVE
docker-compose exec redis cp /data/dump.rdb /backup/dump.rdb
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
    # ... other config
```

### Load Balancing

Use nginx or a load balancer to distribute traffic across multiple API instances.

## Security Checklist

- [ ] Change `SECRET_KEY`] in production
- [ ] Change `ADMIN_TOKEN` in production
- [ ] Use strong database passwords
- [ ] Use strong Redis password
- [ ] Configure CORS origins properly
- [ ] Enable HTTPS/SSL
- [ ] Disable debug mode
- [ ] Disable API docs in production
- [ ] Use non-root user in containers
- [ ] Keep dependencies updated
- [ ] Use secrets management (not .env files in production)

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U sports_user -d sports_analytics
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Application Issues

```bash
# Check application logs
docker-compose logs api

# Check application health
curl http://localhost:8000/health

# Restart application
docker-compose restart api
```

## Deployment to Cloud

### AWS ECS/Fargate

1. Build and push image to ECR
2. Create ECS task definition
3. Configure environment variables
4. Set up RDS for PostgreSQL
5. Set up ElastiCache for Redis
6. Configure load balancer

### Google Cloud Run

1. Build and push to GCR
2. Deploy to Cloud Run
3. Configure Cloud SQL for PostgreSQL
4. Configure Memorystore for Redis
5. Set environment variables

### Azure Container Instances

1. Build and push to ACR
2. Deploy container group
3. Configure Azure Database for PostgreSQL
4. Configure Azure Cache for Redis
5. Set environment variables

### Kubernetes

See `k8s/` directory for Kubernetes manifests (if created).

## Maintenance

### Updating Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Run migrations if needed
docker-compose exec api alembic upgrade head
```

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild image
docker-compose build --no-cache api

# Restart
docker-compose up -d
```

## Performance Tuning

### Database

- Use connection pooling
- Add appropriate indexes
- Regular VACUUM and ANALYZE
- Monitor query performance

### Redis

- Configure memory limits
- Use appropriate eviction policies
- Monitor memory usage

### Application

- Adjust worker count based on CPU
- Monitor response times
- Use caching effectively
- Optimize database queries

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Check health: `curl http://localhost:8000/health`
3. Review documentation
4. Check GitHub issues

