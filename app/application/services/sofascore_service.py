"""Service for scraping and processing SofaScore data."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.infrastructure.external.sofascore_client import SofaScoreClient
from app.application.dto.match_dto import MatchResponseDTO
from app.infrastructure.repositories.match_repository import MatchRepository
from app.infrastructure.repositories.team_repository import TeamRepository
from app.domain.entities.match import Match
from app.domain.entities.team import Team

logger = logging.getLogger(__name__)


class SofaScoreService:
    """Service for scraping and storing SofaScore match data."""

    def __init__(self, match_repository: MatchRepository, team_repository: TeamRepository):
        """Initialize SofaScore service.
        
        Args:
            match_repository: Match repository for database operations
            team_repository: Team repository for database operations
        """
        self.client = SofaScoreClient()
        self.match_repository = match_repository
        self.team_repository = team_repository

    async def scrape_and_store_match(self, match_url: str) -> MatchResponseDTO:
        """Scrape match data from SofaScore and store in database.
        
        Args:
            match_url: SofaScore match URL
        
        Returns:
            MatchResponseDTO with scraped and stored match data
        """
        try:
            # Parse URL
            url_info = self.client.parse_match_url(match_url)
            match_id = url_info.get("match_id")
            
            if not match_id:
                raise ValueError(f"Could not extract match ID from URL: {match_url}")
            
            # Scrape match data
            match_data = await self.client.get_match_data(match_url)
            
            if not match_data:
                raise ValueError(f"Could not scrape match data from URL: {match_url}")
            
            # Get or create teams
            home_team = await self._get_or_create_team(
                name=match_data.get("home_team"),
                slug=url_info.get("home_team_slug"),
            )
            away_team = await self._get_or_create_team(
                name=match_data.get("away_team"),
                slug=url_info.get("away_team_slug"),
            )
            
            # Create match entity
            match_entity = Match(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                sport="football",
                league=match_data.get("league", "Unknown"),
                match_date=self._parse_date(match_data.get("start_date")),
                status=self._normalize_status(match_data.get("status", "scheduled")),
                home_score=match_data.get("home_score"),
                away_score=match_data.get("away_score"),
                venue=match_data.get("venue"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            # Store in database
            stored_match = await self.match_repository.create(match_entity)
            
            # Convert to DTO
            return await self._entity_to_dto(stored_match)
            
        except Exception as e:
            logger.error(f"Error scraping and storing match from {match_url}: {e}", exc_info=True)
            raise

    async def scrape_team_historical_data(self, team_name: str, limit: int = 50) -> List[MatchResponseDTO]:
        """Scrape historical matches for a team and store in database.
        
        Args:
            team_name: Team name to search for
            limit: Maximum number of matches to scrape
        
        Returns:
            List of MatchResponseDTO with scraped matches
        """
        try:
            # Get historical matches from SofaScore
            historical_matches = await self.client.get_team_historical_matches(team_name, limit=limit)
            
            stored_matches = []
            
            for match_data in historical_matches:
                try:
                    # Get or create teams
                    home_team = await self._get_or_create_team(name=match_data.get("homeTeam", {}).get("name"))
                    away_team = await self._get_or_create_team(name=match_data.get("awayTeam", {}).get("name"))
                    
                    # Check if match already exists (by date and teams)
                    match_date = self._parse_date(match_data.get("startTimestamp"))
                    
                    # Simple check: if match date is in the past and we have scores, likely already stored
                    # For now, we'll just try to create and let database handle duplicates
                    # In production, you might want to add a unique constraint on (home_team_id, away_team_id, match_date)
                    
                    # Create match entity
                    match_entity = Match(
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        sport="football",
                        league=match_data.get("tournament", {}).get("name", "Unknown"),
                        match_date=self._parse_date(match_data.get("startTimestamp")),
                        status=self._normalize_status(match_data.get("status", {}).get("type", "finished")),
                        home_score=match_data.get("homeScore", {}).get("current"),
                        away_score=match_data.get("awayScore", {}).get("current"),
                        venue=match_data.get("venue", {}).get("name"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    
                    # Store in database
                    stored_match = await self.match_repository.create(match_entity)
                    stored_matches.append(await self._entity_to_dto(stored_match))
                    
                except Exception as e:
                    logger.warning(f"Error storing historical match: {e}")
                    continue
            
            logger.info(f"Stored {len(stored_matches)} historical matches for team {team_name}")
            return stored_matches
            
        except Exception as e:
            logger.error(f"Error scraping historical data for team {team_name}: {e}", exc_info=True)
            return []

    async def _get_or_create_team(self, name: str, slug: Optional[str] = None) -> Team:
        """Get team from database or create if not exists.
        
        Args:
            name: Team name
            slug: Optional team slug
        
        Returns:
            Team entity
        """
        # Try to find by name
        teams = await self.team_repository.search(name)
        if teams:
            return teams[0]
        
        # Create new team
        team = Team(
            name=name,
            code=slug,
            sport="football",
            league="Unknown",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        return await self.team_repository.create(team)

    def _parse_date(self, date_str: Any) -> datetime:
        """Parse date string to datetime."""
        if isinstance(date_str, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(date_str)
        
        if isinstance(date_str, str):
            # Try ISO format
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
            
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        
        # Default to now
        return datetime.utcnow()

    def _normalize_status(self, status: str) -> str:
        """Normalize match status."""
        status_lower = status.lower()
        
        if status_lower in ['finished', 'ft', 'full time']:
            return "finished"
        elif status_lower in ['live', 'in progress', 'playing']:
            return "LIVE"
        elif status_lower in ['scheduled', 'ns', 'not started']:
            return "scheduled"
        elif status_lower in ['postponed', 'cancelled']:
            return "postponed"
        else:
            return "scheduled"

    async def _entity_to_dto(self, match: Match) -> MatchResponseDTO:
        """Convert match entity to DTO."""
        from app.application.services.match_service import MatchService
        service = MatchService(self.match_repository)
        return await service._entity_to_dto(match)

