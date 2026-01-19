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
            rate_limit_per_minute=30,  # Free tier: 30 requests/minute (per documentation)
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
            api_key = self.api_key or "123"  # Free tier API key is "123"
            response = await self.get(f"/{api_key}/eventsday.php", params=params)
            return response
        except APIError as e:
            # Log as warning since TheSportsDB is a fallback service
            error_msg = str(e)
            # Truncate long HTML error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            logger.warning(f"TheSportsDB error (fallback service): {error_msg}")
            raise

    async def get_live_events(
        self,
        sport: str = "Soccer",
        date: Optional[str] = None,  # Date from mobile app (YYYY-MM-DD) - uses this instead of server time
    ) -> Dict[str, Any]:
        """Get live events from TheSportsDB.
        
        Note: TheSportsDB v1 API doesn't have a livescore endpoint.
        This method uses eventsday.php with the provided date (required by API).
        The date is only used for the API call format, not for filtering results.
        For true live scores, v2 API is required (premium only).

        Args:
            sport: Sport name (default: Soccer)
            date: Date in YYYY-MM-DD format (optional, defaults to UTC now if not provided)

        Returns:
            API response dictionary
        """
        from datetime import datetime
        
        # TheSportsDB API requires a date parameter, but we filter by status, not date
        # Use provided date from mobile app, or fallback to UTC now if not provided
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "d": date,
            "s": sport,
        }

        try:
            api_key = self.api_key or "123"  # Free tier API key is "123"
            response = await self.get(f"/{api_key}/eventsday.php", params=params)
            # Return all events - filtering by live status will be done in the normalization step
            # This allows us to see all matches from the API response
            return response
        except APIError as e:
            # Log as warning since TheSportsDB is a fallback service
            error_msg = str(e)
            # Truncate long HTML error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            logger.warning(f"TheSportsDB error (fallback service): {error_msg}")
            raise

