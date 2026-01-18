"""Team repository implementation."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.domain.entities.team import Team
from app.domain.repositories.team_repository import ITeamRepository
from app.infrastructure.database.models.team_model import TeamModel
from app.infrastructure.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team, TeamModel], ITeamRepository):
    """Team repository implementation."""

    def __init__(self, session: AsyncSession):
        """Initialize team repository."""
        super().__init__(session, TeamModel, Team)

    def _model_to_entity(self, model: TeamModel) -> Team:
        """Convert database model to domain entity."""
        if not model:
            return None
        return Team(
            id=model.id,
            name=model.name,
            code=model.code,
            sport=model.sport,
            league=model.league,
            country=model.country,
            city=model.city,
            founded_year=model.founded_year,
            logo_url=model.logo_url,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Team) -> TeamModel:
        """Convert domain entity to database model."""
        return TeamModel(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            sport=entity.sport,
            league=entity.league,
            country=entity.country,
            city=entity.city,
            founded_year=entity.founded_year,
            logo_url=entity.logo_url,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_sport(self, sport: str) -> List[Team]:
        """Get all teams for a sport."""
        result = await self.session.execute(
            select(self.model).where(self.model.sport == sport)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_league(self, league: str) -> List[Team]:
        """Get all teams in a league."""
        result = await self.session.execute(
            select(self.model).where(self.model.league == league)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_code(self, code: str) -> Optional[Team]:
        """Get team by code."""
        result = await self.session.execute(
            select(self.model).where(self.model.code == code)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Team]:
        """Search teams by name or other criteria."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(self.model)
            .where(
                or_(
                    self.model.name.ilike(search_pattern),
                    self.model.code.ilike(search_pattern),
                    self.model.league.ilike(search_pattern),
                    self.model.city.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

