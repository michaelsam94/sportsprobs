"""Events service for fetching and normalizing sports events from multiple APIs."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.infrastructure.external.api_football_client import APIFootballClient
from app.infrastructure.external.thesportsdb_client import TheSportsDBClient
from app.infrastructure.external.api_client import APIError
from app.infrastructure.cache.cache_service import cache_service
from app.application.dto.match_dto import MatchResponseDTO
from app.core.config import settings

logger = logging.getLogger(__name__)


class EventsService:
    """Service for fetching and normalizing sports events from multiple APIs."""

    def __init__(self):
        """Initialize events service with API clients."""
        self.api_football = APIFootballClient()
        self.thesportsdb = TheSportsDBClient(api_key=getattr(settings, "THESPORTSDB_KEY", None))

    async def get_live_events(
        self,
        league_id: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: int = 30,  # 30 seconds for live events
    ) -> List[MatchResponseDTO]:
        """Get live events from external APIs and convert to MatchResponseDTO.

        Args:
            league_id: Optional league ID filter
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            List of MatchResponseDTO
        """
        cache_key_params = {
            "endpoint": "live_events",
            "league_id": league_id,
        }

        # Check cache first
        if use_cache:
            cached = await cache_service.get("live_events", cache_key_params)
            if cached:
                logger.info("Returning cached live events")
                return [MatchResponseDTO(**item) for item in cached]

        events: List[MatchResponseDTO] = []

        # Try API-Football first
        try:
            response = await self.api_football.get_fixtures(live=True, league_id=league_id)
            if response.get("response"):
                events = self._normalize_api_football_fixtures(response["response"])
                logger.info(f"Fetched {len(events)} live events from API-Football")
        except APIError as e:
            logger.warning(f"API-Football failed: {e}. Trying fallback...")

        # Fallback to TheSportsDB if API-Football fails or returns no results
        if not events:
            try:
                response = await self.thesportsdb.get_live_events()
                if response.get("events"):
                    events = self._normalize_thesportsdb_events(response["events"])
                    logger.info(f"Fetched {len(events)} live events from TheSportsDB")
            except APIError as e:
                logger.warning(f"TheSportsDB failed: {e}")

        # Cache the result
        if use_cache and events:
            cache_data = [event.model_dump() for event in events]
            await cache_service.set("live_events", cache_data, cache_key_params, ttl=cache_ttl)

        return events

    async def get_upcoming_events(
        self,
        league_id: Optional[int] = None,
        date: Optional[str] = None,
        limit: int = 50,
        use_cache: bool = True,
        cache_ttl: int = 3600,  # 1 hour for upcoming events
    ) -> List[MatchResponseDTO]:
        """Get upcoming events from external APIs and convert to MatchResponseDTO.

        Args:
            league_id: Optional league ID filter
            date: Optional date filter (YYYY-MM-DD)
            limit: Maximum number of events to return
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            List of MatchResponseDTO
        """
        cache_key_params = {
            "endpoint": "upcoming_events",
            "league_id": league_id,
            "date": date,
            "limit": limit,
        }

        # Check cache first
        if use_cache:
            cached = await cache_service.get("upcoming_events", cache_key_params)
            if cached:
                logger.info("Returning cached upcoming events")
                return [MatchResponseDTO(**item) for item in cached]

        events: List[MatchResponseDTO] = []

        # Try API-Football first
        try:
            response = await self.api_football.get_fixtures(
                live=False,
                date=date,
                league_id=league_id,
            )
            if response.get("response"):
                all_events = self._normalize_api_football_fixtures(response["response"])
                # Filter upcoming events (status NS - Not Started)
                events = [e for e in all_events if e.status == "NS"][:limit]
                logger.info(f"Fetched {len(events)} upcoming events from API-Football")
        except APIError as e:
            logger.warning(f"API-Football failed: {e}. Trying fallback...")

        # Fallback to TheSportsDB if API-Football fails
        if not events:
            try:
                response = await self.thesportsdb.get_events_by_date(date=date)
                if response.get("events"):
                    all_events = self._normalize_thesportsdb_events(response["events"])
                    # Filter upcoming events
                    events = [e for e in all_events if e.status in ["NS", "TBD"]][:limit]
                    logger.info(f"Fetched {len(events)} upcoming events from TheSportsDB")
            except APIError as e:
                logger.warning(f"TheSportsDB failed: {e}")

        # Cache the result
        if use_cache and events:
            cache_data = [event.model_dump() for event in events]
            await cache_service.set("upcoming_events", cache_data, cache_key_params, ttl=cache_ttl)

        return events

    def _normalize_api_football_fixtures(self, fixtures: List[Dict]) -> List[MatchResponseDTO]:
        """Normalize API-Football fixtures to MatchResponseDTO."""
        events = []
        for fixture in fixtures:
            try:
                # Extract fixture data
                fixture_data = fixture.get("fixture", {})
                teams_data = fixture.get("teams", {})
                score_data = fixture.get("score", {})
                league_data = fixture.get("league", {})

                # Parse start time
                start_time_str = fixture_data.get("date")
                start_time = None
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    except:
                        start_time = datetime.utcnow()
                else:
                    start_time = datetime.utcnow()

                # Extract status
                status = fixture_data.get("status", {}).get("short", "NS")
                minute = fixture_data.get("status", {}).get("elapsed")

                # Build score
                home_score = None
                away_score = None
                if score_data.get("fulltime"):
                    home_score = score_data.get("fulltime", {}).get("home")
                    away_score = score_data.get("fulltime", {}).get("away")
                elif score_data.get("halftime"):
                    home_score = score_data.get("halftime", {}).get("home")
                    away_score = score_data.get("halftime", {}).get("away")

                # Build teams
                home_team = teams_data.get("home", {})
                away_team = teams_data.get("away", {})

                # Build league
                league = league_data.get("name", "Unknown")

                # Ensure team IDs are valid (> 0)
                home_team_id = home_team.get("id") or 1
                away_team_id = away_team.get("id") or 1
                if home_team_id <= 0:
                    home_team_id = 1
                if away_team_id <= 0:
                    away_team_id = 1
                
                event = MatchResponseDTO(
                    id=fixture_data.get("id", 0),
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    sport="football",  # Default sport
                    league=league,
                    match_date=start_time,
                    status=status,
                    home_score=home_score,
                    away_score=away_score,
                    venue=fixture_data.get("venue", {}).get("name"),
                    attendance=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                events.append(event)
            except Exception as e:
                logger.error(f"Error normalizing API-Football fixture: {e}")
                continue

        return events

    def _normalize_thesportsdb_events(self, events_data: List[Dict]) -> List[MatchResponseDTO]:
        """Normalize TheSportsDB events to MatchResponseDTO."""
        events = []
        for event_data in events_data:
            try:
                # Parse start time
                start_time_str = event_data.get("dateEvent") + " " + event_data.get("strTime", "00:00:00")
                try:
                    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                except:
                    start_time = datetime.utcnow()

                # Extract status
                status = event_data.get("strStatus", "NS")
                if status == "Live":
                    status = "LIVE"
                elif status in ["Full Time", "Match Finished"]:
                    status = "FT"

                # Build score
                home_score = event_data.get("intHomeScore")
                away_score = event_data.get("intAwayScore")

                # Ensure team IDs are valid (> 0)
                home_team_id = event_data.get("idHomeTeam") or 1
                away_team_id = event_data.get("idAwayTeam") or 1
                if home_team_id <= 0:
                    home_team_id = 1
                if away_team_id <= 0:
                    away_team_id = 1
                
                event = MatchResponseDTO(
                    id=event_data.get("idEvent", 0),
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    sport="football",  # Default sport
                    league=event_data.get("strLeague", "Unknown"),
                    match_date=start_time,
                    status=status,
                    home_score=home_score,
                    away_score=away_score,
                    venue=event_data.get("strVenue"),
                    attendance=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                events.append(event)
            except Exception as e:
                logger.error(f"Error normalizing TheSportsDB event: {e}")
                continue

        return events

