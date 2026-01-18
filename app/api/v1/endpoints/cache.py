"""Cache management endpoints."""

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from typing import Optional

from app.core.config import settings
from app.core.rate_limit import limiter
from app.infrastructure.cache.cache_manager import cache_manager, CacheType

router = APIRouter()


@router.get("/stats", tags=["cache"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_cache_stats(
    request: Request,
    cache_type: Optional[str] = Query(None, description="Cache type filter"),
):
    """Get cache statistics.

    Returns information about cache usage and health.
    """
    try:
        from app.infrastructure.cache.redis_client import redis_client
        
        redis_available = await redis_client.health_check()
        
        stats = {
            "redis_available": redis_available,
            "cache_types": {
                "live_matches": CacheType.LIVE_MATCHES.value,
                "historical_data": CacheType.HISTORICAL_DATA.value,
                "api_response": CacheType.API_RESPONSE.value,
                "general": CacheType.GENERAL.value,
            },
        }

        if cache_type:
            # Get stats for specific cache type
            try:
                cache_type_enum = CacheType(cache_type)
                stats["selected_type"] = cache_type_enum.value
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid cache type: {cache_type}",
                )

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}",
        )


@router.delete("/clear", tags=["cache"])
@limiter.limit("10/minute")
async def clear_cache(
    request: Request,
    cache_type: Optional[str] = Query(None, description="Cache type to clear (all if not specified)"),
):
    """Clear cache.

    Clears all cache or a specific cache type.
    """
    try:
        if cache_type:
            try:
                cache_type_enum = CacheType(cache_type)
                await cache_manager.clear(cache_type=cache_type_enum)
                message = f"Cache cleared for type: {cache_type}"
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid cache type: {cache_type}",
                )
        else:
            await cache_manager.clear()
            message = "All cache cleared"

        return {
            "success": True,
            "message": message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.get("/health", tags=["cache"])
async def cache_health():
    """Check cache health."""
    try:
        from app.infrastructure.cache.redis_client import redis_client
        
        redis_available = await redis_client.health_check()
        
        return {
            "status": "healthy" if redis_available else "degraded",
            "redis": "connected" if redis_available else "disconnected",
            "fallback": "memory_cache" if not redis_available else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }

