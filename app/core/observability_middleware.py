"""Observability middleware for request tracing and metrics."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import logging

from app.infrastructure.observability.metrics import metrics_collector
from app.infrastructure.observability.error_tracker import error_tracker

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing, metrics, and error tracking."""

    def __init__(self, app):
        """Initialize observability middleware."""
        super().__init__(app)
        self.excluded_paths = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        }

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through observability middleware."""
        # Skip observability for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Generate request ID (correlation ID)
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get client information
        client_id = getattr(request.state, "client_id", None)
        ip_address = getattr(request.state, "client_ip", None)

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "endpoint": request.url.path,
                "client_id": client_id,
                "ip_address": ip_address,
                "query_params": dict(request.query_params),
            },
        )

        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Record metrics
            await metrics_collector.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                client_id=client_id,
                ip_address=ip_address,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-MS"] = f"{response_time_ms:.2f}"

            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "client_id": client_id,
                    "ip_address": ip_address,
                },
            )

            # Log errors for 5xx status codes
            if response.status_code >= 500:
                logger.error(
                    f"Server error: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "endpoint": request.url.path,
                        "status_code": response.status_code,
                        "response_time_ms": response_time_ms,
                        "client_id": client_id,
                        "ip_address": ip_address,
                    },
                )

            return response

        except Exception as e:
            # Calculate response time even on error
            response_time_ms = (time.time() - start_time) * 1000

            # Record error
            await error_tracker.record_error(
                error=e,
                endpoint=request.url.path,
                method=request.method,
                request_id=request_id,
                client_id=client_id,
                ip_address=ip_address,
                context={
                    "query_params": dict(request.query_params),
                    "path_params": dict(request.path_params) if hasattr(request, "path_params") else {},
                },
            )

            # Log error
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_ms": response_time_ms,
                    "client_id": client_id,
                    "ip_address": ip_address,
                },
            )

            # Re-raise to let FastAPI handle it
            raise

