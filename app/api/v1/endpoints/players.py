"""Player endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_player_repository,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.dto.player_dto import (
    PlayerCreateDTO,
    PlayerUpdateDTO,
    PlayerResponseDTO,
)
from app.application.services.player_service import PlayerService

router = APIRouter()


@router.post("", response_model=PlayerResponseDTO, status_code=201)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def create_player(
    request: Request,
    player_data: PlayerCreateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Create a new player."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.create_player(player_data)


@router.get("/{player_id}", response_model=PlayerResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_player(
    request: Request,
    player_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get player by ID."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.get_player_by_id(player_id)


@router.get("", response_model=List[PlayerResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_all_players(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all players with pagination."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.get_all_players(skip=skip, limit=limit)


@router.put("/{player_id}", response_model=PlayerResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def update_player(
    request: Request,
    player_id: int,
    player_data: PlayerUpdateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Update a player."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.update_player(player_id, player_data)


@router.delete("/{player_id}", status_code=204)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def delete_player(
    request: Request,
    player_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a player."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    await service.delete_player(player_id)
    return None


@router.get("/team/{team_id}", response_model=List[PlayerResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_players_by_team(
    request: Request,
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all players for a team."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.get_players_by_team(team_id)


@router.get("/search", response_model=List[PlayerResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def search_players(
    request: Request,
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Search players."""
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.search_players(q, skip=skip, limit=limit)

