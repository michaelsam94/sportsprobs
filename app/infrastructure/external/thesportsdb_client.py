"""TheSportsDB client for fetching sports data."""

from typing import Dict, Any, Optional
import logging

from app.infrastructure.external.api_client import APIClient, APIError

logger = logging.getLogger(__name__)


class TheSportsDBClient(APIClient):
    """Client for TheSportsDB (https://www.thesportsdb.com/)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize TheSportsDB client.

        Args:
            api_key: API key (optional, free tier doesn't require key)
        """
        base_url = "https://www.thesportsdb.com/api/v1/json"
        
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=100,  # Free tier: 100 requests/day, but we'll be conservative
        )

    async def get_events_by_date(
        self,
        sport: str = "Soccer",
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get events by date from TheSportsDB.

        Args:
            sport: Sport name (default: Soccer)
            date: Date filter (YYYY-MM-DD format)

        Returns:
            API response dictionary
        """
        from datetime import datetime
        
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "d": date,
            "s": sport,
        }

        try:
            api_key = self.api_key or "1"  # Default to "1" for free tier
            response = await self.get(f"/{api_key}/eventsday.php", params=params)
            return response
        except APIError as e:
            logger.error(f"TheSportsDB error: {e}")
            raise

    async def get_live_events(
        self,
        sport: str = "Soccer",
    ) -> Dict[str, Any]:
        """Get live events from TheSportsDB.

        Args:
            sport: Sport name (default: Soccer)

        Returns:
            API response dictionary
        """
        params = {
            "s": sport,
        }

        try:
            api_key = self.api_key or "1"  # Default to "1" for free tier
            response = await self.get(f"/{api_key}/livescore.php", params=params)
            return response
        except APIError as e:
            logger.error(f"TheSportsDB error: {e}")
            raise

