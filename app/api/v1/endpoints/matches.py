"""Match endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
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
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD) - uses mobile app's local date instead of server time"),
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
    - Accepts date parameter from mobile app to avoid server timezone issues
    """
    from app.application.services.events_service import EventsService
    
    try:
        events_service = EventsService()
        matches = await events_service.get_live_events(
            league_id=league_id,
            date=date,  # Use date from mobile app if provided
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
    limit: int = Query(100, ge=1, le=500),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD) - deprecated, use 'from' instead"),
    from_timestamp: Optional[str] = Query(None, alias="from", description="Start timestamp (ISO 8601 or Unix timestamp)"),
    to_timestamp: Optional[str] = Query(None, alias="to", description="End timestamp (ISO 8601 or Unix timestamp)"),
    filter_type: Optional[str] = Query(None, description="Filter type: 'today', 'this_week', 'this_month' (convenience parameter)"),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming matches that haven't started yet.
    
    This endpoint fetches upcoming matches from external APIs (API-Football, TheSportsDB)
    or from the database. Matches are filtered to only include those with status 'scheduled'
    or 'NS' (Not Started) and match_date in the future.
    
    Date filtering options (in order of precedence):
    1. from/to timestamps: Explicit date range using ISO 8601 or Unix timestamps
    2. filter_type: Convenience parameter that calculates from/to automatically
       - 'today': Matches scheduled for today
       - 'this_week': Matches scheduled for this week (today to 7 days from now)
       - 'this_month': Matches scheduled for this month (today to end of month)
    3. date: Legacy parameter (YYYY-MM-DD) - deprecated, use 'from' instead
    4. None: All upcoming matches (default)
    
    Features:
    - Caching (1 hour default TTL)
    - Automatic fallback to alternative APIs
    - Normalized response format
    - Flexible date range filtering
    """
    from datetime import datetime, timedelta, timezone
    from calendar import monthrange
    
    # Use UTC+2 (Cairo timezone) for date calculations
    cairo_tz = timezone(timedelta(hours=2))
    now = datetime.now(cairo_tz)
    start_date = now
    end_date = None
    date_filter = date  # Use provided date if available (legacy support)
    
    # Parse from/to timestamps if provided (these take priority over filter_type)
    if from_timestamp:
        try:
            # Try parsing as ISO 8601
            if 'T' in from_timestamp or '+' in from_timestamp or from_timestamp.endswith('Z'):
                start_date = datetime.fromisoformat(from_timestamp.replace('Z', '+00:00'))
            else:
                # Try as Unix timestamp
                start_date = datetime.fromtimestamp(float(from_timestamp), tz=timezone.utc)
            # Ensure timezone-aware
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            else:
                start_date = start_date.astimezone(timezone.utc)
            logger.info(f"Using from_timestamp: {start_date}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid from_timestamp format: {from_timestamp}, error: {e}")
            start_date = now
    
    if to_timestamp:
        try:
            # Try parsing as ISO 8601
            if 'T' in to_timestamp or '+' in to_timestamp or to_timestamp.endswith('Z'):
                end_date = datetime.fromisoformat(to_timestamp.replace('Z', '+00:00'))
            else:
                # Try as Unix timestamp
                end_date = datetime.fromtimestamp(float(to_timestamp), tz=timezone.utc)
            # Ensure timezone-aware
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            else:
                end_date = end_date.astimezone(timezone.utc)
            logger.info(f"Using to_timestamp: {end_date}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid to_timestamp format: {to_timestamp}, error: {e}")
            end_date = None
    
    # If from/to not provided, calculate from filter_type (convenience parameter)
    # Only use filter_type if explicit timestamps were NOT provided
    if not from_timestamp and not to_timestamp and filter_type:
        if filter_type == "today":
            # Today only (in Cairo timezone)
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            # If no explicit date provided, use today's date for API call
            if not date_filter:
                date_filter = start_date.strftime("%Y-%m-%d")
        elif filter_type == "this_week":
            # This week (today to 7 days from now) in Cairo timezone
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
            # Don't pass date filter to API, we'll get a range and filter
            date_filter = None
        elif filter_type == "this_month":
            # This month (today to end of month) in Cairo timezone
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            last_day = monthrange(now.year, now.month)[1]
            end_date = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=cairo_tz)
            # Don't pass date filter to API, we'll get a range and filter
            date_filter = None
    
    from app.application.services.events_service import EventsService
    
    # Determine date filter for EventsService API call
    # If we have a specific date range (from/to or filter_type="today"), use it
    # Otherwise, get a larger set to filter
    api_date_filter = date_filter
    if from_timestamp and to_timestamp and end_date:
        # If explicit from/to provided, check if range is one day or less
        days_diff = (end_date - start_date).total_seconds() / 86400  # Convert to days
        if days_diff <= 1:
            # For single-day ranges, don't use date filter - get all events and filter by timestamp range
            # This ensures we get matches for the correct day regardless of timezone
            api_date_filter = None
            logger.info(f"Single-day range detected, fetching events and filtering by timestamp range: {start_date.isoformat()} to {end_date.isoformat()}")
        else:
            # For multi-day ranges, don't pass date filter - get all and filter
            api_date_filter = None
            logger.info(f"Multi-day range detected ({days_diff:.1f} days), fetching all events and filtering")
    elif not from_timestamp and filter_type == "today":
        # Legacy: filter_type="today" uses date string
        api_date_filter = date_filter
    
    try:
        events_service = EventsService()
        # Get upcoming events - pass date filter for specific dates, otherwise get more events
        fetch_limit = limit * 3 if (from_timestamp or filter_type) else limit * 2
        all_matches = await events_service.get_upcoming_events(
            league_id=league_id,
            date=api_date_filter,
            limit=fetch_limit,
            use_cache=True,
            cache_ttl=3600,
        )
        
        logger.info(f"Fetched {len(all_matches)} upcoming events from EventsService")
        logger.info(f"Filter parameters: from={from_timestamp}, to={to_timestamp}, filter_type={filter_type}")
        logger.info(f"Date range: start_date={start_date.isoformat()}, end_date={end_date.isoformat() if end_date else None}")
        
        # Filter by date range and status
        filtered_matches = []
        for match in all_matches:
            # Check if match is in the future and not started
            match_date = match.match_date
            if match_date:
                # Normalize match_date to timezone-aware if needed
                if match_date.tzinfo is None:
                    # Assume UTC if timezone-naive
                    match_date = match_date.replace(tzinfo=timezone.utc)
                elif match_date.tzinfo != timezone.utc:
                    # Convert to UTC if different timezone
                    match_date = match_date.astimezone(timezone.utc)
                
                # Convert start_date and end_date to UTC for comparison (match_date is in UTC)
                start_date_utc = start_date.astimezone(timezone.utc) if start_date.tzinfo else start_date.replace(tzinfo=timezone.utc)
                end_date_utc = end_date.astimezone(timezone.utc) if end_date and end_date.tzinfo else (end_date.replace(tzinfo=timezone.utc) if end_date else None)
                
                # Check if match is within the date range
                is_in_range = match_date >= start_date_utc
                if end_date_utc:
                    is_in_range = is_in_range and match_date <= end_date_utc
                
                if is_in_range:
                    # Only include scheduled/not started matches
                    status_lower = (match.status or "").lower()
                    if match.status in ["scheduled", "NS", None] or "scheduled" in status_lower or "not started" in status_lower:
                        filtered_matches.append(match)
        
        logger.info(f"Filtered to {len(filtered_matches)} matches after date/status filtering (range: {start_date.isoformat()} to {end_date.isoformat() if end_date else 'unlimited'})")
        
        # If no matches found from external API and we have a date filter, try database fallback
        if len(filtered_matches) == 0 and filter_type:
            logger.info(f"No matches from external API for filter_type={filter_type}, trying database fallback")
            repository = get_match_repository(db)
            service = MatchService(repository)
            try:
                if end_date:
                    # Convert timezone-aware datetimes to naive for database query
                    # Database stores TIMESTAMP WITHOUT TIME ZONE, so we need naive datetimes
                    start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
                    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                    matches = await repository.get_by_date_range(start_date_naive, end_date_naive)
                    # Filter to only scheduled/upcoming
                    now_naive = now.replace(tzinfo=None) if now.tzinfo else now
                    filtered = [m for m in matches if m.status in ["scheduled", "NS", None] and m.match_date and m.match_date >= now_naive]
                    logger.info(f"Database fallback: Found {len(filtered)} matches in database for date range")
                    if filtered:
                        return [await service._entity_to_dto(m) for m in filtered[:limit]]
            except Exception as db_error:
                logger.warning(f"Database fallback failed: {db_error}")
        
        # Sort by date and limit
        filtered_matches.sort(key=lambda x: x.match_date or datetime.max)
        return filtered_matches[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching upcoming matches: {e}", exc_info=True)
        # Fallback to database if external APIs fail
        repository = get_match_repository(db)
        service = MatchService(repository)
        
        try:
            # Use repository method with date range if available
            if end_date:
                matches = await repository.get_by_date_range(start_date, end_date)
                # Filter to only scheduled/upcoming
                filtered = [m for m in matches if m.status in ["scheduled", "NS", None] and m.match_date and m.match_date >= now]
                logger.info(f"Fallback: Found {len(filtered)} matches in database for date range")
                return [await service._entity_to_dto(m) for m in filtered[:limit]]
            else:
                matches = await service.get_upcoming_matches(limit=limit)
                logger.info(f"Fallback: Found {len(matches)} upcoming matches in database")
                return matches
        except Exception as db_error:
            logger.error(f"Database fallback also failed: {db_error}", exc_info=True)
            return []  # Return empty list if both API and database fail


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
    from datetime import timezone, timedelta
    
    # Use UTC+2 (Cairo timezone) for date calculations
    cairo_tz = timezone(timedelta(hours=2))
    
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
    
    # Calculate probabilities using historical data
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_, or_
    from app.infrastructure.database.models.match_model import MatchModel
    
    # Helper function to find team in database by name or ID
    async def find_team_in_db(team_id: int, team_name: Optional[str] = None) -> Optional[int]:
        """Try to find team in database by ID first, then by name with multiple strategies."""
        from app.infrastructure.database.models.team_model import TeamModel
        
        # First try by ID
        query = select(TeamModel).where(TeamModel.id == team_id)
        result = await db.execute(query)
        team = result.scalar_one_or_none()
        if team:
            logger.debug(f"Found team {team_id} by ID in database: {team.name}")
            return team.id
        
        # If not found and we have a team name, try to find by name
        if team_name:
            clean_name = team_name.strip()
            
            # Strategy 1: Exact match (case-insensitive)
            query = select(TeamModel).where(TeamModel.name.ilike(clean_name))
            result = await db.execute(query)
            team = result.scalar_one_or_none()
            if team:
                logger.debug(f"Found team '{team_name}' by exact name match: ID {team.id}")
                return team.id
            
            # Strategy 2: Remove common suffixes and try exact match
            suffixes_to_remove = [
                " FC", " United", " City", " Town", " Athletic", " Rovers",
                " FC.", " F.C.", " F.C", " CF", " CF.", " C.F.",
                " United FC", " City FC", " Town FC"
            ]
            for suffix in suffixes_to_remove:
                if clean_name.endswith(suffix):
                    base_name = clean_name[:-len(suffix)].strip()
                    query = select(TeamModel).where(TeamModel.name.ilike(base_name))
                    result = await db.execute(query)
                    team = result.scalar_one_or_none()
                    if team:
                        logger.debug(f"Found team '{team_name}' by name (removed '{suffix}'): ID {team.id}")
                        return team.id
            
            # Strategy 3: Fuzzy match - team name contains our search term
            query = select(TeamModel).where(TeamModel.name.ilike(f"%{clean_name}%"))
            result = await db.execute(query)
            teams = result.scalars().all()
            if teams:
                # If multiple matches, prefer exact substring match
                for team in teams:
                    if clean_name.lower() in team.name.lower():
                        logger.debug(f"Found team '{team_name}' by fuzzy match: ID {team.id} (matched: {team.name})")
                        return team.id
                # Otherwise return first match
                logger.debug(f"Found team '{team_name}' by fuzzy match: ID {teams[0].id} (matched: {teams[0].name})")
                return teams[0].id
            
            # Strategy 4: Reverse fuzzy - our search term contains team name
            # This helps with cases like "NK Maribor" vs "Maribor"
            all_teams_query = select(TeamModel)
            all_teams_result = await db.execute(all_teams_query)
            all_teams = all_teams_result.scalars().all()
            
            for team in all_teams:
                if team.name and team.name.lower() in clean_name.lower():
                    logger.debug(f"Found team '{team_name}' by reverse fuzzy match: ID {team.id} (matched: {team.name})")
                    return team.id
            
            # Strategy 5: Word-based matching (split by spaces and match words)
            search_words = set(clean_name.lower().split())
            for team in all_teams:
                if team.name:
                    team_words = set(team.name.lower().split())
                    # If at least 2 words match, consider it a match
                    common_words = search_words.intersection(team_words)
                    if len(common_words) >= 2:
                        logger.debug(f"Found team '{team_name}' by word matching: ID {team.id} (matched: {team.name}, words: {common_words})")
                        return team.id
        
        logger.debug(f"Team not found in database: ID={team_id}, name='{team_name}'")
        return None
    
    # Helper function to get league-based averages when team-specific data is not available
    async def get_league_based_stats(league_id: int = None, league_name: Optional[str] = None) -> dict:
        """Get league-wide statistics as fallback."""
        # Use UTC+2 (Cairo timezone) for date calculations
        cairo_tz = timezone(timedelta(hours=2))
        cutoff_date = datetime.now(cairo_tz) - timedelta(days=90)
        
        query = select(MatchModel).where(
            and_(
                MatchModel.status == "finished",
                MatchModel.match_date >= cutoff_date,
                MatchModel.home_score.isnot(None),
                MatchModel.away_score.isnot(None),
            )
        )
        
        if league_id:
            query = query.where(MatchModel.league_id == league_id)
        elif league_name:
            # Try to find league by name and get its ID
            from app.infrastructure.database.models.league_model import LeagueModel
            league_query = select(LeagueModel).where(LeagueModel.name.ilike(f"%{league_name}%"))
            league_result = await db.execute(league_query)
            league = league_result.scalar_one_or_none()
            if league:
                query = query.where(MatchModel.league_id == league.id)
        
        query = query.limit(50)  # Sample matches
        
        result = await db.execute(query)
        matches = result.scalars().all()
        
        if not matches or len(matches) < 5:
            return {
                "goals_for_avg": 1.5,
                "goals_against_avg": 1.2,
                "matches_count": 0,
            }
        
        # Calculate league-wide averages
        total_home_goals = sum(match.home_score or 0 for match in matches)
        total_away_goals = sum(match.away_score or 0 for match in matches)
        matches_count = len(matches)
        
        avg_home_goals = total_home_goals / matches_count
        avg_away_goals = total_away_goals / matches_count
        
        return {
            "goals_for_avg": avg_home_goals,  # For home teams
            "goals_against_avg": avg_away_goals,  # Home teams concede away team goals
            "matches_count": matches_count,
        }
    
    # Helper function to calculate team statistics from historical matches
    async def calculate_team_stats(team_id: int, team_name: Optional[str], is_home: bool, league_id: int = None, league_name: Optional[str] = None) -> dict:
        """Calculate team statistics from historical finished matches."""
        from app.infrastructure.database.models.team_model import TeamModel
        
        # Try to find the team in database (by ID or name)
        db_team_id = await find_team_in_db(team_id, team_name)
        
        if not db_team_id:
            # Team not in database, try league-based stats
            league_stats = await get_league_based_stats(league_id=league_id, league_name=league_name)
            if league_stats["matches_count"] > 0:
                # Use league averages with variation based on team name hash for uniqueness
                import hashlib
                team_hash = int(hashlib.md5((team_name or str(team_id)).encode()).hexdigest()[:8], 16)
                variation = (team_hash % 200) / 200.0 - 0.5  # -0.5 to 0.5 variation
                
                if is_home:
                    goals_for = max(0.8, min(2.5, league_stats["goals_for_avg"] + (variation * 0.5)))
                    goals_against = max(0.5, min(2.0, league_stats["goals_against_avg"] - (variation * 0.4)))
                else:
                    goals_for = max(0.6, min(2.0, league_stats["goals_for_avg"] - (variation * 0.3)))
                    goals_against = max(0.7, min(2.2, league_stats["goals_against_avg"] + (variation * 0.5)))
                
                return {
                    "goals_for_avg": goals_for,
                    "goals_against_avg": goals_against,
                    "matches_count": 0,  # Mark as league-based, not team-specific
                    "db_team_id": None,
                    "source": "league_based",
                }
            
            # No league data either, use defaults with team-based variation for uniqueness
            import hashlib
            team_hash = int(hashlib.md5((team_name or str(team_id)).encode()).hexdigest()[:8], 16)
            variation = (team_hash % 200) / 200.0 - 0.5  # -0.5 to 0.5 variation
            
            if is_home:
                base_goals_for = 1.5
                base_goals_against = 1.2
            else:
                base_goals_for = 1.2
                base_goals_against = 1.5
            
            return {
                "goals_for_avg": max(0.8, min(2.2, base_goals_for + (variation * 0.6))),
                "goals_against_avg": max(0.7, min(2.0, base_goals_against - (variation * 0.5))),
                "matches_count": 0,
                "db_team_id": None,
                "source": "default_with_variation",
            }
        
        # Get finished matches for this team (last 20 matches or last 3 months)
        # Use UTC+2 (Cairo timezone) for date calculations
        cairo_tz = timezone(timedelta(hours=2))
        cutoff_date = datetime.now(cairo_tz) - timedelta(days=90)
        
        query = select(MatchModel).where(
            and_(
                MatchModel.status == "finished",
                MatchModel.match_date >= cutoff_date,
                or_(
                    MatchModel.home_team_id == db_team_id,
                    MatchModel.away_team_id == db_team_id,
                )
            )
        )
        
        if league_id:
            query = query.where(MatchModel.league_id == league_id)
        
        query = query.order_by(MatchModel.match_date.desc()).limit(20)
        
        result = await db.execute(query)
        matches = result.scalars().all()
        
        if not matches or len(matches) < 3:
            # Not enough historical data
            return {
                "goals_for_avg": 1.5 if is_home else 1.2,
                "goals_against_avg": 1.2 if is_home else 1.5,
                "matches_count": len(matches),  # Return actual count even if < 3
                "db_team_id": db_team_id,
                "source": "insufficient_data",
            }
        
        # Calculate averages
        total_goals_for = 0
        total_goals_against = 0
        matches_count = len(matches)
        
        for match in matches:
            if match.home_team_id == db_team_id:
                # Team was home
                if match.home_score is not None:
                    total_goals_for += match.home_score
                if match.away_score is not None:
                    total_goals_against += match.away_score
            else:
                # Team was away
                if match.away_score is not None:
                    total_goals_for += match.away_score
                if match.home_score is not None:
                    total_goals_against += match.home_score
        
        goals_for_avg = total_goals_for / matches_count if matches_count > 0 else 1.5
        goals_against_avg = total_goals_against / matches_count if matches_count > 0 else 1.2
        
        return {
            "goals_for_avg": goals_for_avg,
            "goals_against_avg": goals_against_avg,
            "matches_count": matches_count,
            "db_team_id": db_team_id,  # Include the database team ID for debugging
        }
    
    # Calculate league average goals
    async def calculate_league_avg_goals(league_id: int = None) -> float:
        """Calculate league average goals per match."""
        # Use UTC+2 (Cairo timezone) for date calculations
        cairo_tz = timezone(timedelta(hours=2))
        cutoff_date = datetime.now(cairo_tz) - timedelta(days=90)
        
        query = select(MatchModel).where(
            and_(
                MatchModel.status == "finished",
                MatchModel.match_date >= cutoff_date,
                MatchModel.home_score.isnot(None),
                MatchModel.away_score.isnot(None),
            )
        )
        
        if league_id:
            query = query.where(MatchModel.league_id == league_id)
        
        query = query.limit(100)  # Sample last 100 matches
        
        result = await db.execute(query)
        matches = result.scalars().all()
        
        if not matches or len(matches) < 10:
            return 2.5  # Default league average
        
        total_goals = sum(
            (match.home_score or 0) + (match.away_score or 0)
            for match in matches
        )
        
        return total_goals / (len(matches) * 2)  # Average per team, then per match
    
    # Get team statistics
    home_team_id = match.home_team_id
    away_team_id = match.away_team_id
    home_team_name = getattr(match, 'home_team_name', None)
    away_team_name = getattr(match, 'away_team_name', None)
    
    # Try to get league_id from database match if available
    league_id = None
    try:
        match_model = await repository.get_by_id(match_id)
        if match_model and hasattr(match_model, 'league_id'):
            league_id = match_model.league_id
    except:
        pass  # If match not in database, league_id will be None
    
    # Get league name from match if available
    league_name = getattr(match, 'league', None)
    
    # Try to find teams and check if they have historical matches
    home_db_team_id = await find_team_in_db(home_team_id, home_team_name)
    away_db_team_id = await find_team_in_db(away_team_id, away_team_name)
    
    # Check if teams have historical matches
    home_has_history = False
    away_has_history = False
    
    if home_db_team_id:
        # Quick check: count finished matches for home team
        # Use UTC+2 (Cairo timezone) for date calculations
        cairo_tz = timezone(timedelta(hours=2))
        cutoff_date = datetime.now(cairo_tz) - timedelta(days=90)
        home_matches_query = select(MatchModel).where(
            and_(
                MatchModel.status == "finished",
                MatchModel.match_date >= cutoff_date,
                or_(
                    MatchModel.home_team_id == home_db_team_id,
                    MatchModel.away_team_id == home_db_team_id,
                )
            )
        ).limit(1)
        home_result = await db.execute(home_matches_query)
        home_has_history = home_result.scalar_one_or_none() is not None
    
    if away_db_team_id:
        # Quick check: count finished matches for away team
        # Use UTC+2 (Cairo timezone) for date calculations
        cairo_tz = timezone(timedelta(hours=2))
        cutoff_date = datetime.now(cairo_tz) - timedelta(days=90)
        away_matches_query = select(MatchModel).where(
            and_(
                MatchModel.status == "finished",
                MatchModel.match_date >= cutoff_date,
                or_(
                    MatchModel.home_team_id == away_db_team_id,
                    MatchModel.away_team_id == away_db_team_id,
                )
            )
        ).limit(1)
        away_result = await db.execute(away_matches_query)
        away_has_history = away_result.scalar_one_or_none() is not None
    
    # If teams not found OR have no historical data, try to scrape from SofaScore
    should_scrape_home = (not home_db_team_id or not home_has_history) and home_team_name
    should_scrape_away = (not away_db_team_id or not away_has_history) and away_team_name
    
    if should_scrape_home or should_scrape_away:
        logger.info(f"Attempting SofaScore scrape - Home: {should_scrape_home} (team_id={home_db_team_id}, name='{home_team_name}'), Away: {should_scrape_away} (team_id={away_db_team_id}, name='{away_team_name}')")
        try:
            from app.application.services.sofascore_service import SofaScoreService
            from app.infrastructure.repositories.team_repository import TeamRepository
            
            team_repo = TeamRepository(db)
            sofascore_service = SofaScoreService(repository, team_repo)
            
            # Scrape historical data for teams that need it
            if should_scrape_home:
                logger.info(f"Scraping SofaScore data for home team: '{home_team_name}'")
                try:
                    scraped_matches = await sofascore_service.scrape_team_historical_data(home_team_name, limit=20)
                    logger.info(f"Scraped {len(scraped_matches)} matches for home team '{home_team_name}'")
                    # Re-check after scraping
                    home_db_team_id = await find_team_in_db(home_team_id, home_team_name)
                    if home_db_team_id:
                        logger.info(f"Home team '{home_team_name}' found in database after scraping: ID {home_db_team_id}")
                except Exception as e:
                    logger.error(f"Failed to scrape data for home team '{home_team_name}': {e}", exc_info=True)
            
            if should_scrape_away:
                logger.info(f"Scraping SofaScore data for away team: '{away_team_name}'")
                try:
                    scraped_matches = await sofascore_service.scrape_team_historical_data(away_team_name, limit=20)
                    logger.info(f"Scraped {len(scraped_matches)} matches for away team '{away_team_name}'")
                    # Re-check after scraping
                    away_db_team_id = await find_team_in_db(away_team_id, away_team_name)
                    if away_db_team_id:
                        logger.info(f"Away team '{away_team_name}' found in database after scraping: ID {away_db_team_id}")
                except Exception as e:
                    logger.error(f"Failed to scrape data for away team '{away_team_name}': {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error attempting SofaScore scrape: {e}", exc_info=True)
    else:
        logger.debug(f"Skipping SofaScore scrape - Home: has_team={bool(home_db_team_id)}, has_history={home_has_history}; Away: has_team={bool(away_db_team_id)}, has_history={away_has_history}")
    
    home_stats = await calculate_team_stats(home_team_id, home_team_name, is_home=True, league_id=league_id, league_name=league_name)
    away_stats = await calculate_team_stats(away_team_id, away_team_name, is_home=False, league_id=league_id, league_name=league_name)
    league_avg = await calculate_league_avg_goals(league_id=league_id)
    
    # Calculate expected goals using the probability service
    home_xg = ProbabilityService.calculate_expected_goals(
        team_goals_for_avg=home_stats["goals_for_avg"],
        team_goals_against_avg=home_stats["goals_against_avg"],
        opponent_goals_for_avg=away_stats["goals_for_avg"],
        opponent_goals_against_avg=away_stats["goals_against_avg"],
        league_avg_goals=league_avg,
        home_advantage=0.3,
        is_home=True,
    )
    
    away_xg = ProbabilityService.calculate_expected_goals(
        team_goals_for_avg=away_stats["goals_for_avg"],
        team_goals_against_avg=away_stats["goals_against_avg"],
        opponent_goals_for_avg=home_stats["goals_for_avg"],
        opponent_goals_against_avg=home_stats["goals_against_avg"],
        league_avg_goals=league_avg,
        home_advantage=0.3,
        is_home=False,
    )
    
    # Calculate match probabilities using Poisson distribution
    probabilities = ProbabilityService.calculate_match_probabilities(
        home_xg=home_xg,
        away_xg=away_xg,
    )
    
    # Calculate confidence based on data quality
    min_matches = min(home_stats["matches_count"], away_stats["matches_count"])
    if min_matches >= 10:
        confidence = 0.9
    elif min_matches >= 5:
        confidence = 0.7
    elif min_matches >= 3:
        confidence = 0.5
    else:
        confidence = 0.3  # Low confidence for limited data
    
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
        "confidence": confidence,
        "data_quality": {
            "home_team_matches": home_stats["matches_count"],
            "away_team_matches": away_stats["matches_count"],
            "league_avg_goals": league_avg,
        },
        "calculated_at": datetime.now(cairo_tz).isoformat(),
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
