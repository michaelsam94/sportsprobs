"""SofaScore scraping endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.dependencies import get_db, get_match_repository, get_team_repository
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.dto.match_dto import MatchResponseDTO
from app.application.services.sofascore_service import SofaScoreService
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scrape-match", response_model=MatchResponseDTO, status_code=201)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def scrape_match(
    request: Request,
    match_url: str = Query(..., description="SofaScore match URL"),
    db: AsyncSession = Depends(get_db),
):
    """Scrape a match from SofaScore and store in database.
    
    Example URL: https://www.sofascore.com/football/match/nk-maribor-debreceni-vsc/wNsvY#id:15389642
    
    This endpoint:
    - Scrapes match data from SofaScore
    - Creates/updates teams in database
    - Stores match in database
    - Returns the stored match data
    """
    try:
        match_repository = get_match_repository(db)
        team_repository = get_team_repository(db)
        
        service = SofaScoreService(match_repository, team_repository)
        match = await service.scrape_and_store_match(match_url)
        
        logger.info(f"Successfully scraped and stored match from SofaScore: {match_url}")
        return match
        
    except Exception as e:
        logger.error(f"Error scraping match from SofaScore: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape match: {str(e)}"
        )


@router.post("/scrape-team-history", response_model=List[MatchResponseDTO])
@limiter.limit("10/minute")  # Lower rate limit for bulk operations
async def scrape_team_history(
    request: Request,
    team_name: str = Query(..., description="Team name to scrape historical matches for"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of matches to scrape"),
    db: AsyncSession = Depends(get_db),
):
    """Scrape historical matches for a team from SofaScore.
    
    This endpoint:
    - Searches for the team on SofaScore
    - Scrapes their recent historical matches
    - Stores matches in database
    - Returns list of stored matches
    
    This helps build historical data for analytics.
    """
    try:
        match_repository = get_match_repository(db)
        team_repository = get_team_repository(db)
        
        service = SofaScoreService(match_repository, team_repository)
        matches = await service.scrape_team_historical_data(team_name, limit=limit)
        
        logger.info(f"Successfully scraped {len(matches)} historical matches for team: {team_name}")
        return matches
        
    except Exception as e:
        logger.error(f"Error scraping team history from SofaScore: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape team history: {str(e)}"
        )

