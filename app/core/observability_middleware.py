"""Observability middleware for request tracing and metrics."""

import time
import uuid
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import logging

from app.infrastructure.observability.metrics import metrics_collector
from app.infrastructure.observability.error_tracker import error_tracker
from app.core.config import settings

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

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers by masking sensitive information."""
        sensitive_headers = {
            "authorization", "x-api-key", "cookie", "set-cookie",
            "x-auth-token", "api-key", "apikey"
        }
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_headers):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    async def _read_request_body(self, request: Request) -> str:
        """Read request body without consuming it."""
        body = b""
        async for chunk in request.stream():
            body += chunk
        return body.decode("utf-8", errors="replace")

    async def _read_response_body(self, response: Response) -> str:
        """Read response body."""
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        return body.decode("utf-8", errors="replace")

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

        # Prepare request logging data
        request_log_data = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "client_id": client_id,
            "ip_address": ip_address,
            "query_params": dict(request.query_params),
        }

        # Add detailed request logging if enabled
        if settings.LOG_REQUEST_RESPONSE:
            # Log request headers (sanitized)
            request_headers = dict(request.headers)
            request_log_data["headers"] = self._sanitize_headers(request_headers)

            # Log request body for POST/PUT/PATCH requests
            # We need to cache the body so it can be read again by the endpoint
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # Cache the body by reading it and storing it
                    body_bytes = await request.body()
                    if body_bytes:
                        body_str = body_bytes.decode("utf-8", errors="replace")
                        # Truncate if too large for logging
                        log_body_str = body_str
                        if len(log_body_str) > settings.LOG_REQUEST_BODY_MAX_SIZE:
                            log_body_str = log_body_str[:settings.LOG_REQUEST_BODY_MAX_SIZE] + "... (truncated)"
                        # Try to parse as JSON for better formatting
                        try:
                            body_json = json.loads(log_body_str)
                            request_log_data["body"] = body_json
                        except json.JSONDecodeError:
                            request_log_data["body"] = log_body_str
                        
                        # Restore the body so the endpoint can read it
                        async def receive():
                            return {"type": "http.request", "body": body_bytes}
                        request._receive = receive
                except Exception as e:
                    request_log_data["body"] = f"Error reading body: {str(e)}"

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra=request_log_data,
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

            # Prepare response logging data
            response_log_data = {
                "request_id": request_id,
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "client_id": client_id,
                "ip_address": ip_address,
            }

            # Add detailed response logging if enabled
            if settings.LOG_REQUEST_RESPONSE:
                # Log response headers (sanitized)
                response_headers = dict(response.headers)
                response_log_data["response_headers"] = self._sanitize_headers(response_headers)

                # Log response body (need to read it)
                try:
                    # Read the response body
                    response_body = b""
                    async for chunk in response.body_iterator:
                        response_body += chunk
                    
                    if response_body:
                        body_str = response_body.decode("utf-8", errors="replace")
                        # Truncate if too large
                        if len(body_str) > settings.LOG_RESPONSE_BODY_MAX_SIZE:
                            body_str = body_str[:settings.LOG_RESPONSE_BODY_MAX_SIZE] + "... (truncated)"
                        # Try to parse as JSON for better formatting
                        try:
                            body_json = json.loads(body_str)
                            response_log_data["response_body"] = body_json
                        except json.JSONDecodeError:
                            response_log_data["response_body"] = body_str
                    
                    # Recreate response with the body, preserving all properties
                    from starlette.responses import Response as StarletteResponse
                    new_response = StarletteResponse(
                        content=response_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=getattr(response, "media_type", None),
                    )
                    response = new_response
                except Exception as e:
                    response_log_data["response_body"] = f"Error reading response body: {str(e)}"

            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra=response_log_data,
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

