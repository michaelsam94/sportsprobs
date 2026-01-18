"""Security middleware for API key authentication and rate limiting."""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.infrastructure.security.api_key_service import api_key_service
from app.infrastructure.security.ip_throttle import ip_throttle_service
from app.infrastructure.cache.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and rate limiting."""

    def __init__(self, app, require_api_key: bool = True):
        """Initialize security middleware.

        Args:
            app: FastAPI application
            require_api_key: Whether to require API key (default: True)
        """
        super().__init__(app)
        self.require_api_key = require_api_key
        self.excluded_paths = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through security middleware."""
        # Skip security for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)
        request.state.client_ip = client_ip

        # IP throttling check
        ip_allowed, ip_reason = await ip_throttle_service.check_ip(client_ip)
        if not ip_allowed:
            logger.warning(f"IP blocked: {client_ip} - {ip_reason}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": ip_reason,
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # API key authentication
        api_key = self._extract_api_key(request)
        
        if self.require_api_key and not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "API key required",
                },
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if api_key:
            # Validate API key
            key_info = api_key_service.validate_key(api_key)
            if not key_info:
                logger.warning(f"Invalid API key from IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid API key",
                    },
                    headers={"WWW-Authenticate": "ApiKey"},
                )

            # Store key info in request state for rate limiting
            request.state.api_key = key_info
            request.state.client_id = key_info.client_id
            request.state.rate_limit_per_minute = key_info.rate_limit_per_minute
            request.state.rate_limit_per_hour = key_info.rate_limit_per_hour

            # Per-client rate limiting
            rate_limit_ok = await self._check_client_rate_limit(
                client_id=key_info.client_id,
                per_minute=key_info.rate_limit_per_minute,
                per_hour=key_info.rate_limit_per_hour,
            )

            if not rate_limit_ok:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Client rate limit exceeded",
                        "retry_after": 60,
                    },
                    headers={"Retry-After": "60"},
                )
        else:
            # No API key - use default rate limits
            request.state.client_id = f"anonymous_{client_ip}"
            request.state.rate_limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
            request.state.rate_limit_per_hour = settings.RATE_LIMIT_PER_HOUR

        # Process request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request."""
        # Check Authorization header
        authorization = request.headers.get("Authorization")
        if authorization:
            # Support "ApiKey <key>" or "Bearer <key>" format
            parts = authorization.split()
            if len(parts) == 2:
                scheme = parts[0].lower()
                if scheme in ["apikey", "bearer"]:
                    return parts[1]

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        return None

    async def _check_client_rate_limit(
        self,
        client_id: str,
        per_minute: int,
        per_hour: int,
    ) -> bool:
        """Check per-client rate limits using Redis or memory.

        Args:
            client_id: Client identifier
            per_minute: Rate limit per minute
            per_hour: Rate limit per hour

        Returns:
            True if within limits, False otherwise
        """
        from datetime import datetime, timedelta
        import asyncio

        now = datetime.utcnow()

        # Try Redis first
        redis_client_instance = await redis_client.get_client()
        if redis_client_instance:
            try:
                # Check per-minute limit
                minute_key = f"rate_limit:client:{client_id}:minute"
                minute_count = await redis_client_instance.get(minute_key)
                if minute_count and int(minute_count) >= per_minute:
                    return False

                # Check per-hour limit
                hour_key = f"rate_limit:client:{client_id}:hour"
                hour_count = await redis_client_instance.get(hour_key)
                if hour_count and int(hour_count) >= per_hour:
                    return False

                # Increment counters
                pipe = redis_client_instance.pipeline()
                pipe.incr(minute_key)
                pipe.expire(minute_key, 60)
                pipe.incr(hour_key)
                pipe.expire(hour_key, 3600)
                await pipe.execute()

                return True
            except Exception as e:
                logger.error(f"Redis rate limit check error: {e}")

        # Fallback to in-memory (simplified)
        # In production, use a proper in-memory store with TTL
        return True  # Allow for now if Redis unavailable

