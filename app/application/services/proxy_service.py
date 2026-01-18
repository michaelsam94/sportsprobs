"""Proxy service for external APIs."""

from typing import Dict, Any, Optional, List
import logging

from app.infrastructure.external.sports_data_client import SportsDataClient, APIError
from app.infrastructure.cache.cache_service import cache_service

logger = logging.getLogger(__name__)


class ProxyService:
    """Service for proxying external API requests with caching and normalization."""

    def __init__(self, api_client: SportsDataClient = None):
        """Initialize proxy service."""
        self.api_client = api_client or SportsDataClient()

    async def get_players(
        self,
        sport: str,
        team: Optional[str] = None,
        season: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """Get players from external API with caching and normalization.

        Args:
            sport: Sport name
            team: Optional team filter
            season: Optional season year
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            Normalized response
        """
        # Check cache first
        if use_cache:
            cache_key_params = {
                "sport": sport,
                "endpoint": "players",
            }
            if team:
                cache_key_params["team"] = team
            if season:
                cache_key_params["season"] = season

            cached = await cache_service.get("players", cache_key_params)
            if cached:
                logger.info("Returning cached players data")
                return cached

        try:
            # Fetch from API
            raw_response = await self.api_client.get_players(
                sport=sport,
                team=team,
                season=season,
            )

            # Normalize response
            normalized = self._normalize_players_response(raw_response)

            # Cache the response
            if use_cache:
                await cache_service.set(
                    "players",
                    normalized,
                    cache_key_params,
                    ttl_seconds=cache_ttl,
                )

            return normalized

        except APIError as e:
            logger.error(f"API error fetching players: {e}")
            # Try to return cached data as fallback
            if use_cache:
                cached = await cache_service.get("players", cache_key_params)
                if cached:
                    logger.warning("Returning stale cached data due to API error")
                    return cached
            raise

    async def get_teams(
        self,
        sport: str,
        season: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: int = 600,
    ) -> Dict[str, Any]:
        """Get teams from external API with caching and normalization.

        Args:
            sport: Sport name
            season: Optional season year
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            Normalized response
        """
        # Check cache first
        if use_cache:
            cache_key_params = {
                "sport": sport,
                "endpoint": "teams",
            }
            if season:
                cache_key_params["season"] = season

            cached = await cache_service.get("teams", cache_key_params)
            if cached:
                logger.info("Returning cached teams data")
                return cached

        try:
            # Fetch from API
            raw_response = await self.api_client.get_teams(
                sport=sport,
                season=season,
            )

            # Normalize response
            normalized = self._normalize_teams_response(raw_response)

            # Cache the response
            if use_cache:
                await cache_service.set(
                    "teams",
                    normalized,
                    cache_key_params,
                    ttl_seconds=cache_ttl,
                )

            return normalized

        except APIError as e:
            logger.error(f"API error fetching teams: {e}")
            # Try to return cached data as fallback
            if use_cache:
                cached = await cache_service.get("teams", cache_key_params)
                if cached:
                    logger.warning("Returning stale cached data due to API error")
                    return cached
            raise

    async def get_schedules(
        self,
        sport: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """Get schedules from external API with caching and normalization.

        Args:
            sport: Sport name
            season: Optional season year
            week: Optional week number
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            Normalized response
        """
        # Check cache first
        if use_cache:
            cache_key_params = {
                "sport": sport,
                "endpoint": "schedules",
            }
            if season:
                cache_key_params["season"] = season
            if week:
                cache_key_params["week"] = week

            cached = await cache_service.get("schedules", cache_key_params)
            if cached:
                logger.info("Returning cached schedules data")
                return cached

        try:
            # Fetch from API
            raw_response = await self.api_client.get_schedules(
                sport=sport,
                season=season,
                week=week,
            )

            # Normalize response
            normalized = self._normalize_schedules_response(raw_response)

            # Cache the response
            if use_cache:
                await cache_service.set(
                    "schedules",
                    normalized,
                    cache_key_params,
                    ttl_seconds=cache_ttl,
                )

            return normalized

        except APIError as e:
            logger.error(f"API error fetching schedules: {e}")
            # Try to return cached data as fallback
            if use_cache:
                cached = await cache_service.get("schedules", cache_key_params)
                if cached:
                    logger.warning("Returning stale cached data due to API error")
                    return cached
            raise

    def _normalize_players_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize players API response to consistent format.

        Args:
            raw_response: Raw API response

        Returns:
            Normalized response
        """
        # Handle different response formats
        if isinstance(raw_response, list):
            players = raw_response
        elif isinstance(raw_response, dict):
            players = raw_response.get("players", raw_response.get("data", []))
        else:
            players = []

        normalized_players = []
        for player in players:
            normalized_players.append({
                "id": player.get("PlayerID") or player.get("id"),
                "name": player.get("FirstName", "") + " " + player.get("LastName", ""),
                "first_name": player.get("FirstName") or player.get("first_name", ""),
                "last_name": player.get("LastName") or player.get("last_name", ""),
                "position": player.get("Position") or player.get("position", ""),
                "team": player.get("Team") or player.get("team", ""),
                "jersey_number": player.get("Jersey") or player.get("jersey_number"),
                "height": player.get("Height") or player.get("height"),
                "weight": player.get("Weight") or player.get("weight"),
                "date_of_birth": player.get("BirthDate") or player.get("date_of_birth"),
                "nationality": player.get("Nationality") or player.get("nationality"),
            })

        return {
            "success": True,
            "data": normalized_players,
            "count": len(normalized_players),
            "source": "external_api",
        }

    def _normalize_teams_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize teams API response to consistent format.

        Args:
            raw_response: Raw API response

        Returns:
            Normalized response
        """
        # Handle different response formats
        if isinstance(raw_response, list):
            teams = raw_response
        elif isinstance(raw_response, dict):
            teams = raw_response.get("teams", raw_response.get("data", []))
        else:
            teams = []

        normalized_teams = []
        for team in teams:
            normalized_teams.append({
                "id": team.get("TeamID") or team.get("id"),
                "name": team.get("Name") or team.get("name", ""),
                "code": team.get("Key") or team.get("code", ""),
                "city": team.get("City") or team.get("city", ""),
                "conference": team.get("Conference") or team.get("conference", ""),
                "division": team.get("Division") or team.get("division", ""),
                "logo_url": team.get("WikipediaLogoUrl") or team.get("logo_url", ""),
            })

        return {
            "success": True,
            "data": normalized_teams,
            "count": len(normalized_teams),
            "source": "external_api",
        }

    def _normalize_schedules_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize schedules API response to consistent format.

        Args:
            raw_response: Raw API response

        Returns:
            Normalized response
        """
        # Handle different response formats
        if isinstance(raw_response, list):
            schedules = raw_response
        elif isinstance(raw_response, dict):
            schedules = raw_response.get("schedules", raw_response.get("games", raw_response.get("data", [])))
        else:
            schedules = []

        normalized_schedules = []
        for schedule in schedules:
            normalized_schedules.append({
                "id": schedule.get("GameID") or schedule.get("id"),
                "home_team": schedule.get("HomeTeam") or schedule.get("home_team", ""),
                "away_team": schedule.get("AwayTeam") or schedule.get("away_team", ""),
                "date": schedule.get("DateTime") or schedule.get("date"),
                "status": schedule.get("Status") or schedule.get("status", "scheduled"),
                "home_score": schedule.get("HomeTeamScore") or schedule.get("home_score"),
                "away_score": schedule.get("AwayTeamScore") or schedule.get("away_score"),
                "venue": schedule.get("Stadium") or schedule.get("venue", ""),
            })

        return {
            "success": True,
            "data": normalized_schedules,
            "count": len(normalized_schedules),
            "source": "external_api",
        }

