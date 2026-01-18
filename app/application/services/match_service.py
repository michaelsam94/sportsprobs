"""Match service - application layer business logic."""

from typing import List
from datetime import datetime

from app.domain.entities.match import Match
from app.domain.repositories.match_repository import IMatchRepository
from app.application.dto.match_dto import (
    MatchCreateDTO,
    MatchUpdateDTO,
    MatchResponseDTO,
)
from app.core.exceptions import NotFoundError, ValidationError


class MatchService:
    """Service for match operations."""

    def __init__(self, repository: IMatchRepository):
        """Initialize match service with repository."""
        self.repository = repository

    async def create_match(self, dto: MatchCreateDTO) -> MatchResponseDTO:
        """Create a new match."""
        if dto.home_team_id == dto.away_team_id:
            raise ValidationError("Home and away teams must be different")

        match = Match(
            home_team_id=dto.home_team_id,
            away_team_id=dto.away_team_id,
            sport=dto.sport,
            league=dto.league,
            match_date=dto.match_date,
            status=dto.status,
            home_score=dto.home_score,
            away_score=dto.away_score,
            venue=dto.venue,
            attendance=dto.attendance,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repository.create(match)
        return self._entity_to_dto(created)

    async def get_match_by_id(self, match_id: int) -> MatchResponseDTO:
        """Get match by ID."""
        match = await self.repository.get_by_id(match_id)
        if not match:
            raise NotFoundError("Match", str(match_id))
        return self._entity_to_dto(match)

    async def get_all_matches(
        self, skip: int = 0, limit: int = 100
    ) -> List[MatchResponseDTO]:
        """Get all matches with pagination."""
        matches = await self.repository.get_all(skip=skip, limit=limit)
        return [self._entity_to_dto(match) for match in matches]

    async def update_match(
        self, match_id: int, dto: MatchUpdateDTO
    ) -> MatchResponseDTO:
        """Update a match."""
        match = await self.repository.get_by_id(match_id)
        if not match:
            raise NotFoundError("Match", str(match_id))

        # Validate team IDs if both are being updated
        if dto.home_team_id is not None and dto.away_team_id is not None:
            if dto.home_team_id == dto.away_team_id:
                raise ValidationError("Home and away teams must be different")

        # Update fields
        if dto.home_team_id is not None:
            match.home_team_id = dto.home_team_id
        if dto.away_team_id is not None:
            match.away_team_id = dto.away_team_id
        if dto.sport is not None:
            match.sport = dto.sport
        if dto.league is not None:
            match.league = dto.league
        if dto.match_date is not None:
            match.match_date = dto.match_date
        if dto.status is not None:
            match.status = dto.status
        if dto.home_score is not None:
            match.home_score = dto.home_score
        if dto.away_score is not None:
            match.away_score = dto.away_score
        if dto.venue is not None:
            match.venue = dto.venue
        if dto.attendance is not None:
            match.attendance = dto.attendance

        match.updated_at = datetime.utcnow()

        updated = await self.repository.update(match)
        return self._entity_to_dto(updated)

    async def delete_match(self, match_id: int) -> bool:
        """Delete a match."""
        match = await self.repository.get_by_id(match_id)
        if not match:
            raise NotFoundError("Match", str(match_id))
        return await self.repository.delete(match_id)

    async def get_matches_by_team(self, team_id: int) -> List[MatchResponseDTO]:
        """Get all matches for a team."""
        matches = await self.repository.get_by_team_id(team_id)
        return [self._entity_to_dto(match) for match in matches]

    async def get_upcoming_matches(self, limit: int = 10) -> List[MatchResponseDTO]:
        """Get upcoming matches."""
        matches = await self.repository.get_upcoming(limit=limit)
        return [self._entity_to_dto(match) for match in matches]

    async def get_live_matches(self) -> List[MatchResponseDTO]:
        """Get currently live matches."""
        matches = await self.repository.get_live()
        return [self._entity_to_dto(match) for match in matches]

    def _entity_to_dto(self, match: Match) -> MatchResponseDTO:
        """Convert entity to DTO."""
        return MatchResponseDTO(
            id=match.id,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            sport=match.sport,
            league=match.league,
            match_date=match.match_date,
            status=match.status,
            home_score=match.home_score,
            away_score=match.away_score,
            venue=match.venue,
            attendance=match.attendance,
            created_at=match.created_at,
            updated_at=match.updated_at,
        )

