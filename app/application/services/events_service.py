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
        date: Optional[str] = None,  # Date from mobile app (YYYY-MM-DD)
        use_cache: bool = True,
        cache_ttl: int = 30,  # 30 seconds for live events
    ) -> List[MatchResponseDTO]:
        """Get live events from external APIs and convert to MatchResponseDTO.

        Args:
            league_id: Optional league ID filter
            date: Date from mobile app (YYYY-MM-DD) - uses this instead of server time
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            List of MatchResponseDTO
        """
        cache_key_params = {
            "endpoint": "live_events",
            "league_id": league_id,
            "date": date,  # Include date in cache key
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
                response = await self.thesportsdb.get_live_events(date=date)
                if response.get("events"):
                    all_events = self._normalize_thesportsdb_events(response["events"])
                    # Filter to include LIVE matches and matches scheduled for today (not finished)
                    # Include: LIVE, NS (Not Started), and scheduled matches
                    # Exclude: FT (Finished), POSTPONED, CANCELLED
                    events = [
                        e for e in all_events 
                        if e.status in ["LIVE", "NS", "scheduled"] 
                        and e.status not in ["FT", "POSTPONED", "CANCELLED"]
                    ]
                    logger.info(f"Fetched {len(events)} live/upcoming events from TheSportsDB (filtered from {len(all_events)} total events)")
            except APIError as e:
                logger.warning(f"TheSportsDB failed: {e}")

        # Cache the result
        if use_cache and events:
            cache_data = [event.model_dump() for event in events]
            await cache_service.set("live_events", cache_data, cache_key_params, ttl_seconds=cache_ttl)

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
            await cache_service.set("upcoming_events", cache_data, cache_key_params, ttl_seconds=cache_ttl)

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

                # Extract team names
                home_team_name = home_team.get("name")
                away_team_name = away_team.get("name")

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
                    home_team_name=home_team_name,
                    away_team_name=away_team_name,
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

                # Extract and normalize status
                status = event_data.get("strStatus", "NS")
                # Map TheSportsDB status values to standard status codes
                if status == "Live":
                    status = "LIVE"
                elif status in ["1H", "2H", "HT"]:  # First half, second half, half time
                    status = "LIVE"
                elif status in ["Full Time", "Match Finished"]:
                    status = "FT"
                elif status in ["NS", "Not Started"]:
                    status = "NS"
                # Keep other statuses as-is (e.g., "Cancelled", "Postponed")

                # Build score - convert strings to integers
                home_score = None
                away_score = None
                try:
                    home_score_str = event_data.get("intHomeScore")
                    if home_score_str is not None and home_score_str != "":
                        home_score = int(home_score_str)
                except (ValueError, TypeError):
                    pass
                
                try:
                    away_score_str = event_data.get("intAwayScore")
                    if away_score_str is not None and away_score_str != "":
                        away_score = int(away_score_str)
                except (ValueError, TypeError):
                    pass

                # Extract team names
                home_team_name = event_data.get("strHomeTeam")
                away_team_name = event_data.get("strAwayTeam")

                # Ensure team IDs are valid (> 0) - convert strings to int
                try:
                    home_team_id = int(event_data.get("idHomeTeam") or 0)
                    if home_team_id <= 0:
                        home_team_id = 1
                except (ValueError, TypeError):
                    home_team_id = 1
                
                try:
                    away_team_id = int(event_data.get("idAwayTeam") or 0)
                    if away_team_id <= 0:
                        away_team_id = 1
                except (ValueError, TypeError):
                    away_team_id = 1
                
                # Parse event ID
                try:
                    event_id = int(event_data.get("idEvent") or 0)
                except (ValueError, TypeError):
                    event_id = 0
                
                event = MatchResponseDTO(
                    id=event_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    home_team_name=home_team_name,
                    away_team_name=away_team_name,
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
                logger.error(f"Error normalizing TheSportsDB event: {e}", exc_info=True)
                continue

        return events

