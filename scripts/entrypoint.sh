#!/bin/bash
# Docker entrypoint script

set -e

# Execute startup script if it exists
if [ -f /app/scripts/start.sh ]; then
    exec /app/scripts/start.sh
else
    # Default: run uvicorn directly with workers
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info} \
        --access-log \
        --no-use-colors
fi
