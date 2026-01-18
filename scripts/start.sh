#!/bin/bash
# Production startup script

set -e

echo "Starting Sports Analytics API..."

# Extract database connection details from DATABASE_URL if needed
if [ -z "$POSTGRES_HOST" ] && [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql+asyncpg://user:pass@host:port/db
    POSTGRES_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    POSTGRES_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p' || echo "5432")
    POSTGRES_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
fi

# Wait for database to be ready (if POSTGRES_HOST is set)
if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-sports_user}" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is ready!"
fi

# Extract Redis connection details from REDIS_URL if needed
if [ -z "$REDIS_HOST" ] && [ -n "$REDIS_URL" ]; then
    # Parse REDIS_URL: redis://host:port/db
    REDIS_HOST=$(echo $REDIS_URL | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
    REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p' || echo "6379")
fi

# Wait for Redis to be ready (if REDIS_HOST is set)
if [ -n "$REDIS_HOST" ]; then
    echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
    until redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ping 2>/dev/null; do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
    echo "Redis is ready!"
fi

# Run database migrations
if [ -n "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "Migration failed or already up to date"
fi

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${WORKERS:-4} \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --no-use-colors
