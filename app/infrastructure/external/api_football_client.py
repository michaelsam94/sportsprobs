"""API-Football client for fetching sports data."""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.infrastructure.external.api_client import APIClient, APIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class APIFootballClient(APIClient):
    """Client for API-Football (https://www.api-football.com/)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize API-Football client.

        Args:
            api_key: API key (defaults to API_FOOTBALL_KEY from settings)
        """
        api_key = api_key or getattr(settings, "API_FOOTBALL_KEY", None)
        base_url = "https://v3.football.api-sports.io"
        
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=10,  # Free tier: 10 requests/minute
        )
        
        # Store headers for API-Football (uses X-RapidAPI-Key)
        self._api_football_headers = {}
        if api_key:
            self._api_football_headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "v3.football.api-sports.io",
            }

    async def get_fixtures(
        self,
        live: bool = False,
        date: Optional[str] = None,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get fixtures (matches) from API-Football.

        Args:
            live: If True, get only live fixtures
            date: Date filter (YYYY-MM-DD format)
            league_id: Filter by league ID
            team_id: Filter by team ID

        Returns:
            API response dictionary
        """
        params = {}
        
        if live:
            params["live"] = "all"
        elif date:
            params["date"] = date
        else:
            # Default to today
            params["date"] = datetime.utcnow().strftime("%Y-%m-%d")
        
        if league_id:
            params["league"] = league_id
        if team_id:
            params["team"] = team_id

        try:
            response = await self.get("/fixtures", params=params, headers=self._api_football_headers)
            return response
        except APIError as e:
            logger.error(f"API-Football error: {e}")
            raise

