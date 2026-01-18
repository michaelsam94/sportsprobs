"""Player repository interface."""

from abc import abstractmethod
from typing import Optional, List

from app.domain.repositories.base_repository import IBaseRepository
from app.domain.entities.player import Player


class IPlayerRepository(IBaseRepository[Player]):
    """Player repository interface."""

    @abstractmethod
    async def get_by_team_id(self, team_id: int) -> List[Player]:
        """Get all players for a team."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Player]:
        """Get player by name."""
        pass

    @abstractmethod
    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Player]:
        """Search players by name or other criteria."""
        pass

