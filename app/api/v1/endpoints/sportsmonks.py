"""SportsMonks API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
import logging

from app.core.config import settings
from app.core.rate_limit import limiter
from app.infrastructure.external.sportsmonks_client import SportsMonksClient

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/livescores/inplay")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_live_scores(
    request: Request,
    include: Optional[str] = Query(
        None,
        description="Comma-separated list of relations to include (e.g., 'participants;scores;periods;events;league.country;round')"
    ),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
):
    """Get live in-play scores from SportsMonks API.
    
    This endpoint fetches currently live matches from SportsMonks with detailed information
    including participants, scores, periods, events, league, and round data.
    
    Example response includes:
    - Match details (id, name, starting_at, state_id, etc.)
    - Participants (teams with metadata like position, location)
    - League information with country details
    - Round information
    - Scores, periods, and events (when available)
    
    Features:
    - Real-time live match data
    - Comprehensive match information
    - League and country details
    - Team metadata (position, location)
    """
    try:
        client = SportsMonksClient()
        matches = await client.get_live_scores(include=include, league_id=league_id)
        
        if not matches:
            return []
        
        return matches
        
    except Exception as e:
        logger.error(f"Error fetching live scores from SportsMonks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch live scores: {str(e)}"
        )


@router.get("/fixtures")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_fixtures(
    request: Request,
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD format)"),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    include: Optional[str] = Query(
        None,
        description="Comma-separated list of relations to include"
    ),
):
    """Get fixtures (matches) from SportsMonks API.
    
    This endpoint fetches fixtures/matches from SportsMonks with optional filtering
    by date, league, or team.
    
    Features:
    - Filter by date, league, or team
    - Comprehensive match information
    - Customizable includes for related data
    """
    try:
        client = SportsMonksClient()
        matches = await client.get_fixtures(
            date=date,
            league_id=league_id,
            team_id=team_id,
            include=include
        )
        
        if not matches:
            return []
        
        return matches
        
    except Exception as e:
        logger.error(f"Error fetching fixtures from SportsMonks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fixtures: {str(e)}"
        )


@router.get("/fixtures/{match_id}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_match_by_id(
    request: Request,
    match_id: int,
    include: Optional[str] = Query(
        None,
        description="Comma-separated list of relations to include"
    ),
):
    """Get a specific match by ID from SportsMonks API.
    
    This endpoint fetches detailed information about a specific match including
    all related data like participants, scores, events, etc.
    
    Args:
        match_id: SportsMonks match/fixture ID
        include: Optional comma-separated list of relations to include
    """
    try:
        client = SportsMonksClient()
        match = await client.get_match_by_id(match_id, include=include)
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with ID {match_id} not found"
            )
        
        return match
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match {match_id} from SportsMonks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch match: {str(e)}"
        )

