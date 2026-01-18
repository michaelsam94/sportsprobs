"""Sports Data API client implementation."""

from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.infrastructure.external.api_client import APIClient, APIError


class SportsDataClient(APIClient):
    """Client for Sports Data API."""

    def __init__(self):
        """Initialize Sports Data API client."""
        super().__init__(
            base_url=settings.SPORTS_DATA_API_URL,
            api_key=settings.SPORTS_DATA_API_KEY,
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit_per_minute=60,
        )

    async def get_players(
        self,
        sport: str,
        team: Optional[str] = None,
        season: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get players from Sports Data API.

        Args:
            sport: Sport name (e.g., 'nfl', 'nba', 'mlb')
            team: Optional team filter
            season: Optional season year

        Returns:
            API response with players data
        """
        endpoint = f"{sport}/Players"
        params = {}
        if team:
            params["team"] = team
        if season:
            params["season"] = str(season)

        return await self.get(endpoint, params=params)

    async def get_teams(
        self,
        sport: str,
        season: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get teams from Sports Data API.

        Args:
            sport: Sport name (e.g., 'nfl', 'nba', 'mlb')
            season: Optional season year

        Returns:
            API response with teams data
        """
        endpoint = f"{sport}/Teams"
        params = {}
        if season:
            params["season"] = str(season)

        return await self.get(endpoint, params=params)

    async def get_schedules(
        self,
        sport: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get schedules/matches from Sports Data API.

        Args:
            sport: Sport name (e.g., 'nfl', 'nba', 'mlb')
            season: Optional season year
            week: Optional week number

        Returns:
            API response with schedules data
        """
        endpoint = f"{sport}/Schedules"
        params = {}
        if season:
            params["season"] = str(season)
        if week:
            params["week"] = str(week)

        return await self.get(endpoint, params=params)

    async def get_player_stats(
        self,
        sport: str,
        player_id: str,
        season: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get player statistics.

        Args:
            sport: Sport name
            player_id: Player identifier
            season: Optional season year

        Returns:
            API response with player stats
        """
        endpoint = f"{sport}/PlayerGameStatsByPlayerID/{player_id}"
        params = {}
        if season:
            params["season"] = str(season)

        return await self.get(endpoint, params=params)

