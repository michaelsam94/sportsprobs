"""Gemini AI sports analysis endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.dependencies import get_db, get_match_repository, get_team_repository
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.dto.match_dto import MatchResponseDTO
from app.infrastructure.external.gemini_client import GeminiClient
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-match", status_code=200)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze_match(
    request: Request,
    home_team: str = Query(..., description="Home team name"),
    away_team: str = Query(..., description="Away team name"),
    sport: str = Query("football", description="Sport type (football, basketball, etc.)"),
    league: Optional[str] = Query(None, description="League name (optional)"),
    match_date: Optional[str] = Query(None, description="Match date (optional)"),
):
    """Get comprehensive match analysis using Gemini AI.
    
    This endpoint uses Google Gemini AI to provide detailed statistical analysis including:
    - Team performance metrics (recent form, home/away records, league position)
    - Head-to-head statistics
    - Player statistics and key players
    - Tactical analysis (formations, playing styles, strengths/weaknesses)
    - Match-specific factors (home advantage, motivation, fatigue)
    - Statistical predictions (probabilities, expected goals, likely scorelines)
    - Key statistics (possession, shots, passes, corners, fouls, etc.)
    - Advanced metrics (xG, xGA, xP)
    - Trend analysis
    - Risk factors (injuries, suspensions, poor form)
    
    Example:
        POST /api/v1/sofascore/analyze-match?home_team=Arsenal&away_team=Chelsea&league=Premier League
    """
    try:
        client = GeminiClient()
        analysis = await client.analyze_match(
            home_team=home_team,
            away_team=away_team,
            sport=sport,
            league=league,
            match_date=match_date
        )
        
        logger.info(f"Successfully generated Gemini analysis for {home_team} vs {away_team}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating Gemini analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get("/team-statistics", status_code=200)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_team_statistics(
    request: Request,
    team_name: str = Query(..., description="Team name"),
    sport: str = Query("football", description="Sport type"),
    league: Optional[str] = Query(None, description="League name (optional)"),
):
    """Get comprehensive team statistics using Gemini AI.
    
    This endpoint provides detailed team statistics including:
    - Current season performance (wins, draws, losses, goals, points, position)
    - Recent form (last 5-10 matches)
    - Home and away records
    - Key players and their statistics
    - Tactical style and formation
    - Strengths and weaknesses
    - Average statistics per match
    - Historical performance trends
    
    Example:
        GET /api/v1/sofascore/team-statistics?team_name=Manchester United&league=Premier League
    """
    try:
        client = GeminiClient()
        stats = await client.get_team_statistics(
            team_name=team_name,
            sport=sport,
            league=league
        )
        
        logger.info(f"Successfully generated team statistics for {team_name}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting team statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team statistics: {str(e)}"
        )


@router.post("/analyze-match-with-context", status_code=200)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze_match_with_context(
    request: Request,
    match_data: Dict[str, Any],
):
    """Analyze match using existing match data as context.
    
    This endpoint enhances existing match data with comprehensive Gemini AI analysis.
    Provide match data in the request body, and the AI will use it as context for deeper analysis.
    
    Expected match_data fields:
    - home_team: Home team name
    - away_team: Away team name
    - sport: Sport type (default: football)
    - league: League name (optional)
    - match_date: Match date (optional)
    - Any other relevant match information
    
    Example:
        POST /api/v1/sofascore/analyze-match-with-context
        Body: {{"home_team": "Arsenal", "away_team": "Chelsea", "league": "Premier League"}}
    """
    try:
        client = GeminiClient()
        analysis = await client.analyze_match_with_context(match_data=match_data)
        
        logger.info(f"Successfully generated contextual analysis")
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating contextual analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate contextual analysis: {str(e)}"
        )

