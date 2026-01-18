"""Team repository interface."""

from abc import abstractmethod
from typing import Optional, List

from app.domain.repositories.base_repository import IBaseRepository
from app.domain.entities.team import Team


class ITeamRepository(IBaseRepository[Team]):
    """Team repository interface."""

    @abstractmethod
    async def get_by_sport(self, sport: str) -> List[Team]:
        """Get all teams for a sport."""
        pass

    @abstractmethod
    async def get_by_league(self, league: str) -> List[Team]:
        """Get all teams in a league."""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Team]:
        """Get team by code."""
        pass

    @abstractmethod
    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Team]:
        """Search teams by name or other criteria."""
        pass

