"""Match endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_match_repository,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.dto.match_dto import (
    MatchCreateDTO,
    MatchUpdateDTO,
    MatchResponseDTO,
)
from app.application.services.match_service import MatchService

router = APIRouter()


@router.post("", response_model=MatchResponseDTO, status_code=201)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def create_match(
    request: Request,
    match_data: MatchCreateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Create a new match."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.create_match(match_data)


@router.get("/{match_id}", response_model=MatchResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_match(
    request: Request,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get match by ID."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.get_match_by_id(match_id)


@router.get("", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_all_matches(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all matches with pagination."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.get_all_matches(skip=skip, limit=limit)


@router.put("/{match_id}", response_model=MatchResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def update_match(
    request: Request,
    match_id: int,
    match_data: MatchUpdateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Update a match."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.update_match(match_id, match_data)


@router.delete("/{match_id}", status_code=204)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def delete_match(
    request: Request,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a match."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    await service.delete_match(match_id)
    return None


@router.get("/team/{team_id}", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_matches_by_team(
    request: Request,
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all matches for a team."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.get_matches_by_team(team_id)


@router.get("/upcoming", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_upcoming_matches(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming matches."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.get_upcoming_matches(limit=limit)


@router.get("/live", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_live_matches(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get currently live matches (cached for 60 seconds)."""
    from app.infrastructure.cache.live_matches_cache import LiveMatchesCache
    from app.infrastructure.cache.decorators import cache_live_matches
    
    # Check cache first
    cached = await LiveMatchesCache.get_live_matches()
    if cached:
        return cached
    
    # Cache miss - fetch from database
    repository = get_match_repository(db)
    service = MatchService(repository)
    matches = await service.get_live_matches()
    
    # Cache the result
    await LiveMatchesCache.set_live_matches(matches, ttl=60)
    
    return matches

