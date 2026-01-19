"""Match endpoints."""

from typing import List, Optional
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
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
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


@router.get("/finished", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_finished_matches(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get finished matches."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    return await service.get_finished_matches(limit=limit)


@router.get("/historical", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_historical_matches(
    request: Request,
    page: int = Query(0, ge=0, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    season: Optional[int] = Query(None, description="Filter by season"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical matches with pagination."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    skip = page * page_size
    matches = await service.get_all_matches(skip=skip, limit=page_size)
    # TODO: Add filtering by team_id, league_id, season
    return matches


@router.get("/team/{team_id}/history", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_team_history(
    request: Request,
    team_id: int,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit results"),
    db: AsyncSession = Depends(get_db),
):
    """Get team match history."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    matches = await service.get_matches_by_team(team_id)
    if limit:
        matches = matches[:limit]
    return matches


@router.get("/h2h/{team1_id}/{team2_id}", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_head_to_head(
    request: Request,
    team1_id: int,
    team2_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get head-to-head matches between two teams."""
    repository = get_match_repository(db)
    service = MatchService(repository)
    # Get matches for both teams and filter for matches between them
    team1_matches = await service.get_matches_by_team(team1_id)
    team2_matches = await service.get_matches_by_team(team2_id)
    
    # Find matches where both teams played
    h2h_matches = []
    team1_match_ids = {m.id for m in team1_matches}
    for match in team2_matches:
        if match.id in team1_match_ids:
            # Check if this match is between the two teams
            if (match.home_team_id == team1_id and match.away_team_id == team2_id) or \
               (match.home_team_id == team2_id and match.away_team_id == team1_id):
                h2h_matches.append(match)
    
    return h2h_matches


@router.get("/{match_id}/analytics", response_model=dict)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_match_analytics(
    request: Request,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get match analytics and probabilities."""
    from app.application.services.probability_service import ProbabilityService
    
    repository = get_match_repository(db)
    match = await repository.get_by_id(match_id)
    
    if not match:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found"
        )
    
    # Calculate probabilities
    probability_service = ProbabilityService()
    probabilities = await probability_service.calculate_match_probabilities(match)
    
    return {
        "match_id": match_id,
        "probabilities": {
            "home_win": probabilities.get("home_win_probability", 0.0),
            "draw": probabilities.get("draw_probability", 0.0),
            "away_win": probabilities.get("away_win_probability", 0.0),
        },
        "expected_goals": {
            "home": probabilities.get("home_expected_goals", 0.0),
            "away": probabilities.get("away_expected_goals", 0.0),
        },
        "confidence": probabilities.get("confidence", 0.0),
        "calculated_at": probabilities.get("calculated_at"),
    }
