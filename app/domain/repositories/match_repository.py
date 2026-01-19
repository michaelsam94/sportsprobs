"""Match repository interface."""

from abc import abstractmethod
from typing import List
from datetime import datetime

from app.domain.repositories.base_repository import IBaseRepository
from app.domain.entities.match import Match


class IMatchRepository(IBaseRepository[Match]):
    """Match repository interface."""

    @abstractmethod
    async def get_by_team_id(self, team_id: int) -> List[Match]:
        """Get all matches for a team."""
        pass

    @abstractmethod
    async def get_by_sport(self, sport: str) -> List[Match]:
        """Get all matches for a sport."""
        pass

    @abstractmethod
    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Match]:
        """Get matches within a date range."""
        pass

    @abstractmethod
    async def get_upcoming(self, limit: int = 10) -> List[Match]:
        """Get upcoming matches."""
        pass

    @abstractmethod
    async def get_live(self) -> List[Match]:
        """Get currently live matches."""
        pass

    @abstractmethod
    async def get_finished(self, limit: int = 10) -> List[Match]:
        """Get finished matches."""
        pass

