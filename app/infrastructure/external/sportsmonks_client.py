"""SportsMonks API client for fetching sports data."""

from typing import Dict, Any, Optional, List
import logging

from app.infrastructure.external.api_client import APIClient, APIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SportsMonksClient(APIClient):
    """Client for SportsMonks API (https://www.sportmonks.com/)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize SportsMonks client.

        Args:
            api_key: API key (defaults to SPORTSMONKS_API_KEY from settings)
        """
        api_key = api_key or getattr(settings, "SPORTSMONKS_API_KEY", None)
        base_url = getattr(settings, "SPORTSMONKS_API_URL", "https://api.sportmonks.com/v3")
        
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=60,  # Adjust based on your plan
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ):
        """Override _make_request to use api_token in query params instead of header.
        
        SportsMonks uses api_token as a query parameter, not a header.
        """
        # Ensure params dict exists
        if params is None:
            params = {}
        
        # Add API token to query parameters (SportsMonks uses api_token, not header)
        if self.api_key:
            params["api_token"] = self.api_key
        
        # Prevent base class from adding API key as header by passing a dummy header
        if headers is None:
            headers = {}
        # Set a dummy value to prevent base class from adding X-API-Key header
        headers["X-API-Key"] = ""
        
        # Call parent's _make_request
        return await super()._make_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json_data=json_data,
            headers=headers,
        )

    async def get_live_scores(
        self,
        include: Optional[str] = None,
        league_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get live in-play scores from SportsMonks.

        Args:
            include: Comma-separated list of relations to include (e.g., "participants;scores;periods;events;league.country;round")
            league_id: Filter by league ID (optional)

        Returns:
            List of match dictionaries
        """
        params = {}
        
        # Add include parameter
        if include:
            params["include"] = include
        else:
            # Default includes based on example
            params["include"] = "participants;scores;periods;events;league.country;round"
        
        # Add league filter if provided (SportsMonks uses filters=fixtureLeagues:ID format)
        if league_id:
            params["filters"] = f"fixtureLeagues:{league_id}"

        try:
            response = await self.get("/football/livescores/inplay", params=params)
            
            # SportsMonks returns data in a 'data' field or directly as a list
            if isinstance(response, dict):
                return response.get("data", [])
            elif isinstance(response, list):
                return response
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return []
        except APIError as e:
            logger.error(f"SportsMonks API error: {e}")
            raise

    async def get_fixtures(
        self,
        date: Optional[str] = None,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
        include: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get fixtures (matches) from SportsMonks.

        Args:
            date: Date filter (YYYY-MM-DD format) - if provided, uses /fixtures/date/{date} endpoint
            league_id: Filter by league ID (will filter results in Python after API call)
            team_id: Filter by team ID (will filter results in Python after API call)
            include: Comma-separated list of relations to include

        Returns:
            List of match dictionaries
        """
        params = {}
        
        # Add include parameter
        if include:
            params["include"] = include
        else:
            params["include"] = "participants;scores;periods;events;league.country;round"
        
        # Use date-specific endpoint if date is provided
        if date:
            # Use /fixtures/date/{date} endpoint for specific date
            endpoint = f"/football/fixtures/date/{date}"
            response = await self.get(endpoint, params=params)
        else:
            # No date filter, use regular fixtures endpoint
            response = await self.get("/football/fixtures", params=params)
        
        # Parse response
        matches = []
        if isinstance(response, dict):
            matches = response.get("data", [])
        elif isinstance(response, list):
            matches = response
        
        # Filter by league_id in Python if provided
        if league_id and matches:
            filtered_matches = []
            for match in matches:
                match_league = match.get("league", {})
                if isinstance(match_league, dict):
                    match_league_id = match_league.get("id")
                    if match_league_id == league_id:
                        filtered_matches.append(match)
                elif match.get("league_id") == league_id:
                    filtered_matches.append(match)
            matches = filtered_matches
        
        # Filter by team_id in Python if provided
        if team_id and matches:
            filtered_matches = []
            for match in matches:
                participants = match.get("participants", [])
                if isinstance(participants, list):
                    for participant in participants:
                        if participant.get("id") == team_id:
                            filtered_matches.append(match)
                            break
            matches = filtered_matches
        
        return matches

    async def get_match_by_id(
        self,
        match_id: int,
        include: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific match by ID.

        Args:
            match_id: Match ID
            include: Comma-separated list of relations to include

        Returns:
            Match dictionary or None if not found
        """
        params = {}
        
        # Add include parameter
        if include:
            params["include"] = include
        else:
            params["include"] = "participants;scores;periods;events;league.country;round"

        try:
            response = await self.get(f"/football/fixtures/{match_id}", params=params)
            
            if isinstance(response, dict):
                return response.get("data")
            else:
                return response
        except APIError as e:
            if e.status_code == 404:
                return None
            logger.error(f"SportsMonks API error: {e}")
            raise

