"""Player repository implementation."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.domain.entities.player import Player
from app.domain.repositories.player_repository import IPlayerRepository
from app.infrastructure.database.models.player_model import PlayerModel
from app.infrastructure.repositories.base_repository import BaseRepository


class PlayerRepository(BaseRepository[Player, PlayerModel], IPlayerRepository):
    """Player repository implementation."""

    def __init__(self, session: AsyncSession):
        """Initialize player repository."""
        super().__init__(session, PlayerModel, Player)

    def _model_to_entity(self, model: PlayerModel) -> Player:
        """Convert database model to domain entity."""
        if not model:
            return None
        return Player(
            id=model.id,
            name=model.name,
            position=model.position,
            team_id=model.team_id,
            jersey_number=model.jersey_number,
            height=model.height,
            weight=model.weight,
            date_of_birth=model.date_of_birth,
            nationality=model.nationality,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Player) -> PlayerModel:
        """Convert domain entity to database model."""
        return PlayerModel(
            id=entity.id,
            name=entity.name,
            position=entity.position,
            team_id=entity.team_id,
            jersey_number=entity.jersey_number,
            height=entity.height,
            weight=entity.weight,
            date_of_birth=entity.date_of_birth,
            nationality=entity.nationality,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_team_id(self, team_id: int) -> List[Player]:
        """Get all players for a team."""
        result = await self.session.execute(
            select(self.model).where(self.model.team_id == team_id)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_name(self, name: str) -> Optional[Player]:
        """Get player by name."""
        result = await self.session.execute(
            select(self.model).where(self.model.name == name)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Player]:
        """Search players by name or other criteria."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(self.model)
            .where(
                or_(
                    self.model.name.ilike(search_pattern),
                    self.model.position.ilike(search_pattern),
                    self.model.nationality.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

