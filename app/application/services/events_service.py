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

                # Build score - API-Football score structure varies for live vs finished matches
                home_score = None
                away_score = None
                
                # For live matches, check multiple possible score locations
                if status in ["1H", "2H", "HT", "ET", "P", "BT", "INT", "LIVE"]:
                    # Check teams.goals for live matches (some API versions use this)
                    if teams_data.get("home", {}).get("goals") is not None:
                        home_score = teams_data.get("home", {}).get("goals")
                    if teams_data.get("away", {}).get("goals") is not None:
                        away_score = teams_data.get("away", {}).get("goals")
                    
                    # Also check score.goals field (alternative structure)
                    if (home_score is None or away_score is None) and score_data.get("goals"):
                        goals_score = score_data.get("goals", {})
                        if home_score is None:
                            home_score = goals_score.get("home")
                        if away_score is None:
                            away_score = goals_score.get("away")
                    
                    # Check fixture.goals (some API versions)
                    if (home_score is None or away_score is None) and fixture_data.get("goals"):
                        fixture_goals = fixture_data.get("goals", {})
                        if home_score is None:
                            home_score = fixture_goals.get("home")
                        if away_score is None:
                            away_score = fixture_goals.get("away")
                
                # Check fulltime score (works for both live and finished matches)
                # For live matches, fulltime may contain current score
                if (home_score is None or away_score is None) and score_data.get("fulltime"):
                    fulltime_score = score_data.get("fulltime", {})
                    if home_score is None:
                        home_score = fulltime_score.get("home")
                    if away_score is None:
                        away_score = fulltime_score.get("away")
                
                # Check extratime (for matches in extra time)
                if (home_score is None or away_score is None) and score_data.get("extratime"):
                    extratime_score = score_data.get("extratime", {})
                    if home_score is None:
                        home_score = extratime_score.get("home")
                    if away_score is None:
                        away_score = extratime_score.get("away")
                
                # Fallback to halftime if available
                if (home_score is None or away_score is None) and score_data.get("halftime"):
                    halftime_score = score_data.get("halftime", {})
                    if home_score is None:
                        home_score = halftime_score.get("home")
                    if away_score is None:
                        away_score = halftime_score.get("away")
                
                # Debug logging for live matches without scores
                if status in ["1H", "2H", "HT", "ET", "P", "BT", "INT", "LIVE"] and (home_score is None or away_score is None):
                    logger.debug(
                        f"Live match {fixture_data.get('id')} ({status}) - Score extraction: "
                        f"score_data={score_data}, teams_data={teams_data}, "
                        f"fixture_data_keys={list(fixture_data.keys())}"
                    )

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

                # Extract status
                status = event_data.get("strStatus", "NS")
                if status == "Live":
                    status = "LIVE"
                elif status in ["Full Time", "Match Finished"]:
                    status = "FT"

                # Build score - convert to int if provided (TheSportsDB may return as string or null)
                home_score = event_data.get("intHomeScore")
                away_score = event_data.get("intAwayScore")
                
                # Convert scores to int if they're strings
                if home_score is not None:
                    try:
                        home_score = int(home_score)
                    except (ValueError, TypeError):
                        home_score = None
                
                if away_score is not None:
                    try:
                        away_score = int(away_score)
                    except (ValueError, TypeError):
                        away_score = None

                # Extract team names
                home_team_name = event_data.get("strHomeTeam")
                away_team_name = event_data.get("strAwayTeam")

                # Ensure team IDs are valid (> 0)
                # TheSportsDB returns team IDs as strings, so convert to int
                home_team_id_raw = event_data.get("idHomeTeam")
                try:
                    if home_team_id_raw is None or home_team_id_raw == "":
                        home_team_id = 1
                    else:
                        home_team_id = int(home_team_id_raw)
                except (ValueError, TypeError):
                    home_team_id = 1
                
                away_team_id_raw = event_data.get("idAwayTeam")
                try:
                    if away_team_id_raw is None or away_team_id_raw == "":
                        away_team_id = 1
                    else:
                        away_team_id = int(away_team_id_raw)
                except (ValueError, TypeError):
                    away_team_id = 1
                
                if home_team_id <= 0:
                    home_team_id = 1
                if away_team_id <= 0:
                    away_team_id = 1
                
                # Convert event ID to int (TheSportsDB returns it as string)
                event_id_raw = event_data.get("idEvent")
                try:
                    if event_id_raw is None or event_id_raw == "":
                        event_id = 0
                    else:
                        event_id = int(event_id_raw)
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
                logger.error(f"Error normalizing TheSportsDB event: {e}")
                continue

        return events

