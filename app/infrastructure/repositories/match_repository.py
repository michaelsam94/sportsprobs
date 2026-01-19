"""Match repository implementation."""

from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.domain.entities.match import Match
from app.domain.repositories.match_repository import IMatchRepository
from app.infrastructure.database.models.match_model import MatchModel
from app.infrastructure.repositories.base_repository import BaseRepository


class MatchRepository(BaseRepository[Match, MatchModel], IMatchRepository):
    """Match repository implementation."""

    def __init__(self, session: AsyncSession):
        """Initialize match repository."""
        super().__init__(session, MatchModel, Match)

    def _model_to_entity(self, model: MatchModel) -> Match:
        """Convert database model to domain entity."""
        if not model:
            return None
        return Match(
            id=model.id,
            home_team_id=model.home_team_id,
            away_team_id=model.away_team_id,
            sport=model.sport,
            league=model.league,
            match_date=model.match_date,
            status=model.status,
            home_score=model.home_score,
            away_score=model.away_score,
            venue=model.venue,
            attendance=model.attendance,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Match) -> MatchModel:
        """Convert domain entity to database model."""
        return MatchModel(
            id=entity.id,
            home_team_id=entity.home_team_id,
            away_team_id=entity.away_team_id,
            sport=entity.sport,
            league=entity.league,
            match_date=entity.match_date,
            status=entity.status,
            home_score=entity.home_score,
            away_score=entity.away_score,
            venue=entity.venue,
            attendance=entity.attendance,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_team_id(self, team_id: int) -> List[Match]:
        """Get all matches for a team."""
        result = await self.session.execute(
            select(self.model).where(
                or_(
                    self.model.home_team_id == team_id,
                    self.model.away_team_id == team_id,
                )
            )
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_sport(self, sport: str) -> List[Match]:
        """Get all matches for a sport."""
        result = await self.session.execute(
            select(self.model).where(self.model.sport == sport)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Match]:
        """Get matches within a date range."""
        result = await self.session.execute(
            select(self.model).where(
                and_(
                    self.model.match_date >= start_date,
                    self.model.match_date <= end_date,
                )
            )
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_upcoming(self, limit: int = 10) -> List[Match]:
        """Get upcoming matches."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(self.model)
            .where(
                and_(
                    self.model.match_date >= now,
                    self.model.status == "scheduled",
                )
            )
            .order_by(self.model.match_date)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_live(self) -> List[Match]:
        """Get currently live matches."""
        result = await self.session.execute(
            select(self.model).where(self.model.status == "live")
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_finished(self, limit: int = 10) -> List[Match]:
        """Get finished matches."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.status == "finished")
            .order_by(self.model.match_date.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

