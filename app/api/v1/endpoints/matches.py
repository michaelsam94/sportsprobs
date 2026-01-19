"""Match endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

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

logger = logging.getLogger(__name__)

router = APIRouter()


# POST endpoint - create match
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


# GET endpoints - specific routes must come BEFORE parameterized routes
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


@router.get("/live", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_live_matches(
    request: Request,
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get currently live matches from external APIs (API-Football, TheSportsDB).
    
    This endpoint fetches live matches from free sports APIs:
    - API-Football (primary)
    - TheSportsDB (fallback)
    
    Features:
    - Short cache TTL (30 seconds default)
    - Automatic fallback to alternative APIs
    - Normalized response format
    """
    from app.application.services.events_service import EventsService
    
    try:
        events_service = EventsService()
        matches = await events_service.get_live_events(
            league_id=league_id,
            use_cache=True,
            cache_ttl=30,
        )
        return matches
    except Exception as e:
        logger.error(f"Error fetching live matches: {e}", exc_info=True)
        # Fallback to database if external APIs fail
        from app.infrastructure.cache.live_matches_cache import LiveMatchesCache
        cached = await LiveMatchesCache.get_live_matches()
        if cached:
            return cached
        
        repository = get_match_repository(db)
        service = MatchService(repository)
        matches = await service.get_live_matches()
        return matches


@router.get("/upcoming", response_model=List[MatchResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_upcoming_matches(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming matches from external APIs (API-Football, TheSportsDB).
    
    This endpoint fetches upcoming matches from free sports APIs:
    - API-Football (primary)
    - TheSportsDB (fallback)
    
    Features:
    - Caching (1 hour default TTL)
    - Automatic fallback to alternative APIs
    - Normalized response format
    - Pagination support
    """
    from app.application.services.events_service import EventsService
    
    try:
        events_service = EventsService()
        matches = await events_service.get_upcoming_events(
            league_id=league_id,
            date=date,
            limit=limit,
            use_cache=True,
            cache_ttl=3600,
        )
        return matches
    except Exception as e:
        logger.error(f"Error fetching upcoming matches: {e}", exc_info=True)
        # Fallback to database if external APIs fail
        repository = get_match_repository(db)
        service = MatchService(repository)
        return await service.get_upcoming_matches(limit=limit)


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


# Parameterized routes must come AFTER specific routes
@router.get("/{match_id}/analytics", response_model=dict)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_match_analytics(
    request: Request,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get match analytics and probabilities. Checks database, cache, and external APIs."""
    from fastapi import HTTPException, status
    from app.application.services.probability_service import ProbabilityService
    from app.infrastructure.cache.cache_service import cache_service
    
    match = None
    
    # First, try database
    repository = get_match_repository(db)
    try:
        match_model = await repository.get_by_id(match_id)
        if match_model:
            # Convert model to DTO for probability service
            match = MatchResponseDTO(
                id=match_model.id,
                home_team_id=match_model.home_team_id,
                away_team_id=match_model.away_team_id,
                sport=match_model.sport,
                league=match_model.league,
                match_date=match_model.match_date,
                status=match_model.status,
                home_score=match_model.home_score,
                away_score=match_model.away_score,
                venue=match_model.venue,
                attendance=match_model.attendance,
                created_at=match_model.created_at,
                updated_at=match_model.updated_at,
            )
    except Exception as e:
        logger.debug(f"Match {match_id} not in database: {e}")
    
    # If not in database, check cache
    if not match:
        try:
            # Check live events cache - try different cache key variations
            cache_params_variations = [
                {"endpoint": "live_events", "league_id": None},
                {"endpoint": "live_events"},
            ]
            for params in cache_params_variations:
                cached_live = await cache_service.get("live_events", params)
                if cached_live:
                    # Cache stores list of match dicts directly
                    match_list = cached_live if isinstance(cached_live, list) else []
                    for match_data in match_list:
                        if isinstance(match_data, dict) and match_data.get("id") == match_id:
                            match = MatchResponseDTO(**match_data)
                            break
                if match:
                    break
            
            # Check upcoming events cache - try different cache key variations
            if not match:
                cache_params_variations = [
                    {"endpoint": "upcoming_events", "league_id": None, "date": None, "limit": 50},
                    {"endpoint": "upcoming_events", "league_id": None, "limit": 50},
                    {"endpoint": "upcoming_events"},
                ]
                for params in cache_params_variations:
                    cached_upcoming = await cache_service.get("upcoming_events", params)
                    if cached_upcoming:
                        # Cache stores list of match dicts directly
                        match_list = cached_upcoming if isinstance(cached_upcoming, list) else []
                        for match_data in match_list:
                            if isinstance(match_data, dict) and match_data.get("id") == match_id:
                                match = MatchResponseDTO(**match_data)
                                break
                    if match:
                        break
        except Exception as e:
            logger.warning(f"Error checking cache for match {match_id}: {e}")
    
    # If still not found, try fetching from external APIs
    if not match:
        try:
            from app.application.services.events_service import EventsService
            events_service = EventsService()
            
            # Try live events
            live_matches = await events_service.get_live_events(use_cache=True, cache_ttl=30)
            for m in live_matches:
                if m.id == match_id:
                    match = m
                    break
            
            # Try upcoming events
            if not match:
                upcoming_matches = await events_service.get_upcoming_events(limit=100, use_cache=True, cache_ttl=3600)
                for m in upcoming_matches:
                    if m.id == match_id:
                        match = m
                        break
        except Exception as e:
            logger.warning(f"Error fetching match {match_id} from external APIs: {e}")
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found"
        )
    
    # Calculate probabilities
    # For now, use simplified xG calculation (can be enhanced with historical data)
    # Default xG values if we don't have historical stats
    home_xg = 1.5  # Default expected goals for home team
    away_xg = 1.2  # Default expected goals for away team
    
    # TODO: Enhance with actual team statistics if available in database
    # For external API matches, we don't have historical data, so use defaults
    
    # Calculate match probabilities using Poisson distribution
    probabilities = ProbabilityService.calculate_match_probabilities(
        home_xg=home_xg,
        away_xg=away_xg,
    )
    
    from datetime import datetime
    return {
        "match_id": match_id,
        "probabilities": {
            "home_win": probabilities.home_win,
            "draw": probabilities.draw,
            "away_win": probabilities.away_win,
        },
        "expected_goals": {
            "home": home_xg,
            "away": away_xg,
        },
        "confidence": 0.7,  # Default confidence (can be calculated based on data quality)
        "calculated_at": datetime.utcnow().isoformat(),
    }


@router.get("/{match_id}", response_model=MatchResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_match(
    request: Request,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get match by ID. Checks database first, then cache, then external APIs."""
    from fastapi import HTTPException, status
    from app.infrastructure.cache.cache_service import cache_service
    
    # First, try database
    repository = get_match_repository(db)
    service = MatchService(repository)
    try:
        match = await service.get_match_by_id(match_id)
        if match:
            return match
    except HTTPException:
        pass  # Continue to check cache/external APIs
    
    # If not in database, check cache (live/upcoming matches)
    try:
        # Check live events cache - try different cache key variations
        cache_params_variations = [
            {"endpoint": "live_events", "league_id": None},
            {"endpoint": "live_events"},
        ]
        for params in cache_params_variations:
            cached_live = await cache_service.get("live_events", params)
            if cached_live:
                # Cache stores list of match dicts directly
                match_list = cached_live if isinstance(cached_live, list) else []
                for match_data in match_list:
                    if isinstance(match_data, dict) and match_data.get("id") == match_id:
                        return MatchResponseDTO(**match_data)
        
        # Check upcoming events cache - try different cache key variations
        cache_params_variations = [
            {"endpoint": "upcoming_events", "league_id": None, "date": None, "limit": 50},
            {"endpoint": "upcoming_events", "league_id": None, "limit": 50},
            {"endpoint": "upcoming_events"},
        ]
        for params in cache_params_variations:
            cached_upcoming = await cache_service.get("upcoming_events", params)
            if cached_upcoming:
                # Cache stores list of match dicts directly
                match_list = cached_upcoming if isinstance(cached_upcoming, list) else []
                for match_data in match_list:
                    if isinstance(match_data, dict) and match_data.get("id") == match_id:
                        return MatchResponseDTO(**match_data)
    except Exception as e:
        logger.warning(f"Error checking cache for match {match_id}: {e}")
    
    # If still not found, try fetching from external APIs
    try:
        from app.application.services.events_service import EventsService
        events_service = EventsService()
        
        # Try live events
        live_matches = await events_service.get_live_events(use_cache=True, cache_ttl=30)
        for match in live_matches:
            if match.id == match_id:
                return match
        
        # Try upcoming events
        upcoming_matches = await events_service.get_upcoming_events(limit=100, use_cache=True, cache_ttl=3600)
        for match in upcoming_matches:
            if match.id == match_id:
                return match
    except Exception as e:
        logger.warning(f"Error fetching match {match_id} from external APIs: {e}")
    
    # Not found anywhere
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Match not found with id: {match_id}"
    )


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
