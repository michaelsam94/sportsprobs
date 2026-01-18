"""Player service - application layer business logic."""

from typing import List, Optional
from datetime import datetime

from app.domain.entities.player import Player
from app.domain.repositories.player_repository import IPlayerRepository
from app.application.dto.player_dto import (
    PlayerCreateDTO,
    PlayerUpdateDTO,
    PlayerResponseDTO,
)
from app.core.exceptions import NotFoundError, ValidationError


class PlayerService:
    """Service for player operations."""

    def __init__(self, repository: IPlayerRepository):
        """Initialize player service with repository."""
        self.repository = repository

    async def create_player(self, dto: PlayerCreateDTO) -> PlayerResponseDTO:
        """Create a new player."""
        player = Player(
            name=dto.name,
            position=dto.position,
            team_id=dto.team_id,
            jersey_number=dto.jersey_number,
            height=dto.height,
            weight=dto.weight,
            date_of_birth=dto.date_of_birth,
            nationality=dto.nationality,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repository.create(player)
        return self._entity_to_dto(created)

    async def get_player_by_id(self, player_id: int) -> PlayerResponseDTO:
        """Get player by ID."""
        player = await self.repository.get_by_id(player_id)
        if not player:
            raise NotFoundError("Player", str(player_id))
        return self._entity_to_dto(player)

    async def get_all_players(
        self, skip: int = 0, limit: int = 100
    ) -> List[PlayerResponseDTO]:
        """Get all players with pagination."""
        players = await self.repository.get_all(skip=skip, limit=limit)
        return [self._entity_to_dto(player) for player in players]

    async def update_player(
        self, player_id: int, dto: PlayerUpdateDTO
    ) -> PlayerResponseDTO:
        """Update a player."""
        player = await self.repository.get_by_id(player_id)
        if not player:
            raise NotFoundError("Player", str(player_id))

        # Update fields
        if dto.name is not None:
            player.name = dto.name
        if dto.position is not None:
            player.position = dto.position
        if dto.team_id is not None:
            player.team_id = dto.team_id
        if dto.jersey_number is not None:
            player.jersey_number = dto.jersey_number
        if dto.height is not None:
            player.height = dto.height
        if dto.weight is not None:
            player.weight = dto.weight
        if dto.date_of_birth is not None:
            player.date_of_birth = dto.date_of_birth
        if dto.nationality is not None:
            player.nationality = dto.nationality

        player.updated_at = datetime.utcnow()

        updated = await self.repository.update(player)
        return self._entity_to_dto(updated)

    async def delete_player(self, player_id: int) -> bool:
        """Delete a player."""
        player = await self.repository.get_by_id(player_id)
        if not player:
            raise NotFoundError("Player", str(player_id))
        return await self.repository.delete(player_id)

    async def get_players_by_team(self, team_id: int) -> List[PlayerResponseDTO]:
        """Get all players for a team."""
        players = await self.repository.get_by_team_id(team_id)
        return [self._entity_to_dto(player) for player in players]

    async def search_players(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[PlayerResponseDTO]:
        """Search players."""
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        players = await self.repository.search(query, skip=skip, limit=limit)
        return [self._entity_to_dto(player) for player in players]

    def _entity_to_dto(self, player: Player) -> PlayerResponseDTO:
        """Convert entity to DTO."""
        return PlayerResponseDTO(
            id=player.id,
            name=player.name,
            position=player.position,
            team_id=player.team_id,
            jersey_number=player.jersey_number,
            height=player.height,
            weight=player.weight,
            date_of_birth=player.date_of_birth,
            nationality=player.nationality,
            created_at=player.created_at,
            updated_at=player.updated_at,
        )

