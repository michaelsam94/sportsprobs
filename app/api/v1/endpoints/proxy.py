"""API proxy endpoints for external services."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status

from app.core.dependencies import get_proxy_service
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.services.proxy_service import ProxyService

router = APIRouter()


@router.get("/players", tags=["proxy"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def proxy_get_players(
    request: Request,
    sport: str = Query(..., description="Sport name (e.g., nfl, nba, mlb)"),
    team: Optional[str] = Query(None, description="Optional team filter"),
    season: Optional[int] = Query(None, description="Optional season year"),
    use_cache: bool = Query(True, description="Whether to use cache"),
    cache_ttl: int = Query(300, ge=60, le=3600, description="Cache TTL in seconds"),
    proxy_service: ProxyService = Depends(get_proxy_service),
):
    """Proxy endpoint to get players from external API.

    This endpoint:
    - Hides the third-party API key
    - Normalizes the response format
    - Caches responses for performance
    - Handles rate limits and retries
    - Falls back to cached data on errors

    Example:
        GET /api/v1/proxy/players?sport=nfl&season=2023
    """
    try:
        result = await proxy_service.get_players(
            sport=sport,
            team=team,
            season=season,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch players from external API: {str(e)}",
        )


@router.get("/teams", tags=["proxy"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def proxy_get_teams(
    request: Request,
    sport: str = Query(..., description="Sport name (e.g., nfl, nba, mlb)"),
    season: Optional[int] = Query(None, description="Optional season year"),
    use_cache: bool = Query(True, description="Whether to use cache"),
    cache_ttl: int = Query(600, ge=60, le=3600, description="Cache TTL in seconds"),
    proxy_service: ProxyService = Depends(get_proxy_service),
):
    """Proxy endpoint to get teams from external API.

    This endpoint:
    - Hides the third-party API key
    - Normalizes the response format
    - Caches responses for performance
    - Handles rate limits and retries
    - Falls back to cached data on errors

    Example:
        GET /api/v1/proxy/teams?sport=nfl&season=2023
    """
    try:
        result = await proxy_service.get_teams(
            sport=sport,
            season=season,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch teams from external API: {str(e)}",
        )


@router.get("/schedules", tags=["proxy"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def proxy_get_schedules(
    request: Request,
    sport: str = Query(..., description="Sport name (e.g., nfl, nba, mlb)"),
    season: Optional[int] = Query(None, description="Optional season year"),
    week: Optional[int] = Query(None, description="Optional week number"),
    use_cache: bool = Query(True, description="Whether to use cache"),
    cache_ttl: int = Query(300, ge=60, le=3600, description="Cache TTL in seconds"),
    proxy_service: ProxyService = Depends(get_proxy_service),
):
    """Proxy endpoint to get schedules/matches from external API.

    This endpoint:
    - Hides the third-party API key
    - Normalizes the response format
    - Caches responses for performance
    - Handles rate limits and retries
    - Falls back to cached data on errors

    Example:
        GET /api/v1/proxy/schedules?sport=nfl&season=2023&week=1
    """
    try:
        result = await proxy_service.get_schedules(
            sport=sport,
            season=season,
            week=week,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch schedules from external API: {str(e)}",
        )


@router.delete("/cache", tags=["proxy"])
@limiter.limit("10/minute")
async def clear_proxy_cache(
    request: Request,
):
    """Clear all cached proxy responses.

    This endpoint clears the cache for all proxy endpoints.
    Useful for forcing fresh data from external APIs.
    """
    from app.infrastructure.cache.cache_service import cache_service

    try:
        await cache_service.clear()
        return {
            "success": True,
            "message": "Cache cleared successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )

