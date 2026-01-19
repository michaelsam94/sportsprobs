"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import players, teams, matches, proxy, cache, probability_config, security, protected_example, observability, sofascore

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(probability_config.router, prefix="/admin/probability-config", tags=["admin"])
api_router.include_router(security.router, prefix="/admin", tags=["admin"])
api_router.include_router(protected_example.router, prefix="/example", tags=["example"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(sofascore.router, prefix="/sofascore", tags=["sofascore", "scraping"])

