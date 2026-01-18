"""Middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security_middleware import SecurityMiddleware
from app.core.observability_middleware import ObservabilityMiddleware


def setup_middleware(app: FastAPI, require_api_key: bool = True) -> None:
    """Configure all middleware for the application.
    
    Args:
        app: FastAPI application
        require_api_key: Whether to require API key authentication
    """
    # Observability Middleware (request tracing, metrics, error tracking)
    # Should be first to capture all requests
    app.add_middleware(ObservabilityMiddleware)
    
    # Security Middleware (API key auth, IP throttling, per-client rate limiting)
    app.add_middleware(
        SecurityMiddleware,
        require_api_key=require_api_key,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limiting (additional layer)
    if settings.RATE_LIMIT_ENABLED:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

