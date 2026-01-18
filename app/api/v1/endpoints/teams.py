"""Team endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_team_repository,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.application.dto.team_dto import (
    TeamCreateDTO,
    TeamUpdateDTO,
    TeamResponseDTO,
)
from app.application.services.team_service import TeamService

router = APIRouter()


@router.post("", response_model=TeamResponseDTO, status_code=201)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def create_team(
    request: Request,
    team_data: TeamCreateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Create a new team."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.create_team(team_data)


@router.get("/{team_id}", response_model=TeamResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_team(
    request: Request,
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get team by ID."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.get_team_by_id(team_id)


@router.get("", response_model=List[TeamResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_all_teams(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all teams with pagination."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.get_all_teams(skip=skip, limit=limit)


@router.put("/{team_id}", response_model=TeamResponseDTO)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def update_team(
    request: Request,
    team_id: int,
    team_data: TeamUpdateDTO,
    db: AsyncSession = Depends(get_db),
):
    """Update a team."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.update_team(team_id, team_data)


@router.delete("/{team_id}", status_code=204)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def delete_team(
    request: Request,
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a team."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    await service.delete_team(team_id)
    return None


@router.get("/sport/{sport}", response_model=List[TeamResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_teams_by_sport(
    request: Request,
    sport: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all teams for a sport."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.get_teams_by_sport(sport)


@router.get("/search", response_model=List[TeamResponseDTO])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def search_teams(
    request: Request,
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Search teams."""
    repository = get_team_repository(db)
    service = TeamService(repository)
    return await service.search_teams(q, skip=skip, limit=limit)

