"""Repository interfaces."""

from app.domain.repositories.player_repository import IPlayerRepository
from app.domain.repositories.team_repository import ITeamRepository
from app.domain.repositories.match_repository import IMatchRepository

__all__ = ["IPlayerRepository", "ITeamRepository", "IMatchRepository"]

