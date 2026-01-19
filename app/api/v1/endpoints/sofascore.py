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
from app.infrastructure.external.sofascore_client import SofaScoreClient
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


@router.post("/search", status_code=200)
@limiter.limit("5/minute")  # Lower rate limit for browser automation (slower)
async def search_sofascore(
    request: Request,
    query: str = Query(..., description="Search query (team name, match, competition, etc.)"),
    result_index: int = Query(0, ge=0, le=10, description="Index of result to select from dropdown (0 = first result)"),
):
    """Search SofaScore using browser automation (when URL query params don't work).
    
    This endpoint:
    - Opens SofaScore website
    - Types query into search input (#search-input)
    - Waits for dropdown results (.z_dropdown)
    - Selects the specified result from dropdown
    - Returns the selected result data and final URL
    
    Use this when normal URL query parameters don't work for the sports-api.
    
    Example:
        POST /api/v1/sofascore/search?query=Manchester United&result_index=0
    """
    try:
        client = SofaScoreClient()
        result = await client.search_and_select_result(
            query=query,
            result_index=result_index
        )
        
        logger.info(f"Successfully searched and selected result for query: {query}")
        return result
        
    except Exception as e:
        logger.error(f"Error searching SofaScore for query '{query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search SofaScore: {str(e)}"
        )


@router.post("/search-and-scrape", response_model=MatchResponseDTO, status_code=201)
@limiter.limit("3/minute")  # Very low rate limit for browser automation + scraping
async def search_and_scrape_match(
    request: Request,
    query: str = Query(..., description="Search query (team name, match, etc.)"),
    result_index: int = Query(0, ge=0, le=10, description="Index of result to select from dropdown"),
    db: AsyncSession = Depends(get_db),
):
    """Search SofaScore using browser automation and scrape the selected match data.
    
    This endpoint:
    - Opens SofaScore website
    - Searches using the search input
    - Selects a result from dropdown
    - Scrapes match data from the resulting page
    - Stores match in database
    - Returns the stored match data
    
    Example:
        POST /api/v1/sofascore/search-and-scrape?query=Arsenal vs Chelsea&result_index=0
    """
    try:
        client = SofaScoreClient()
        
        # Search and get match data using browser automation
        match_data = await client.search_and_get_match_data(
            query=query,
            result_index=result_index
        )
        
        if not match_data or not match_data.get("final_url"):
            raise ValueError(f"Could not find match data for query: {query}")
        
        # Use existing service to store the match
        match_repository = get_match_repository(db)
        team_repository = get_team_repository(db)
        service = SofaScoreService(match_repository, team_repository)
        
        # Store the match using the final URL
        match = await service.scrape_and_store_match(match_data["final_url"])
        
        logger.info(f"Successfully searched, scraped and stored match for query: {query}")
        return match
        
    except Exception as e:
        logger.error(f"Error searching and scraping SofaScore for query '{query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search and scrape match: {str(e)}"
        )

