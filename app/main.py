"""Main application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.core.middleware import setup_middleware
from app.infrastructure.cache.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    # Setup structured logging
    setup_logging(
        level="INFO" if not settings.DEBUG else "DEBUG",
        json_format=True,
    )
    
    await redis_client.get_client()
    yield
    # Shutdown
    await redis_client.close()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    # Production configuration
    app_config = {
        "title": settings.API_TITLE,
        "description": settings.API_DESCRIPTION,
        "version": settings.APP_VERSION,
        "lifespan": lifespan,
    }
    
    # Only set debug in development
    if settings.DEBUG:
        app_config["debug"] = True
    
    # Production optimizations
    if settings.ENVIRONMENT == "production":
        app_config.update({
            "docs_url": None,  # Disable docs in production
            "redoc_url": None,  # Disable redoc in production
            "openapi_url": None,  # Disable OpenAPI schema in production
        })
    
    app = FastAPI(**app_config)

    # Setup middleware (require_api_key=True for production, False for development)
    require_api_key = not settings.DEBUG  # Don't require API key in debug mode
    setup_middleware(app, require_api_key=require_api_key)

    # Include API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Sports Analytics API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        redis_healthy = await redis_client.health_check()
        return {
            "status": "healthy",
            "redis": "connected" if redis_healthy else "disconnected",
        }

    return app


app = create_application()

