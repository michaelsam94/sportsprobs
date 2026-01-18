"""Team service - application layer business logic."""

from typing import List
from datetime import datetime

from app.domain.entities.team import Team
from app.domain.repositories.team_repository import ITeamRepository
from app.application.dto.team_dto import (
    TeamCreateDTO,
    TeamUpdateDTO,
    TeamResponseDTO,
)
from app.core.exceptions import NotFoundError, ValidationError


class TeamService:
    """Service for team operations."""

    def __init__(self, repository: ITeamRepository):
        """Initialize team service with repository."""
        self.repository = repository

    async def create_team(self, dto: TeamCreateDTO) -> TeamResponseDTO:
        """Create a new team."""
        team = Team(
            name=dto.name,
            code=dto.code,
            sport=dto.sport,
            league=dto.league,
            country=dto.country,
            city=dto.city,
            founded_year=dto.founded_year,
            logo_url=dto.logo_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repository.create(team)
        return self._entity_to_dto(created)

    async def get_team_by_id(self, team_id: int) -> TeamResponseDTO:
        """Get team by ID."""
        team = await self.repository.get_by_id(team_id)
        if not team:
            raise NotFoundError("Team", str(team_id))
        return self._entity_to_dto(team)

    async def get_all_teams(
        self, skip: int = 0, limit: int = 100
    ) -> List[TeamResponseDTO]:
        """Get all teams with pagination."""
        teams = await self.repository.get_all(skip=skip, limit=limit)
        return [self._entity_to_dto(team) for team in teams]

    async def update_team(
        self, team_id: int, dto: TeamUpdateDTO
    ) -> TeamResponseDTO:
        """Update a team."""
        team = await self.repository.get_by_id(team_id)
        if not team:
            raise NotFoundError("Team", str(team_id))

        # Update fields
        if dto.name is not None:
            team.name = dto.name
        if dto.code is not None:
            team.code = dto.code
        if dto.sport is not None:
            team.sport = dto.sport
        if dto.league is not None:
            team.league = dto.league
        if dto.country is not None:
            team.country = dto.country
        if dto.city is not None:
            team.city = dto.city
        if dto.founded_year is not None:
            team.founded_year = dto.founded_year
        if dto.logo_url is not None:
            team.logo_url = dto.logo_url

        team.updated_at = datetime.utcnow()

        updated = await self.repository.update(team)
        return self._entity_to_dto(updated)

    async def delete_team(self, team_id: int) -> bool:
        """Delete a team."""
        team = await self.repository.get_by_id(team_id)
        if not team:
            raise NotFoundError("Team", str(team_id))
        return await self.repository.delete(team_id)

    async def get_teams_by_sport(self, sport: str) -> List[TeamResponseDTO]:
        """Get all teams for a sport."""
        teams = await self.repository.get_by_sport(sport)
        return [self._entity_to_dto(team) for team in teams]

    async def search_teams(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[TeamResponseDTO]:
        """Search teams."""
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        teams = await self.repository.search(query, skip=skip, limit=limit)
        return [self._entity_to_dto(team) for team in teams]

    def _entity_to_dto(self, team: Team) -> TeamResponseDTO:
        """Convert entity to DTO."""
        return TeamResponseDTO(
            id=team.id,
            name=team.name,
            code=team.code,
            sport=team.sport,
            league=team.league,
            country=team.country,
            city=team.city,
            founded_year=team.founded_year,
            logo_url=team.logo_url,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

