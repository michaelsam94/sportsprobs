"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status, Depends

from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.player_repository import PlayerRepository
from app.infrastructure.repositories.team_repository import TeamRepository
from app.infrastructure.repositories.match_repository import MatchRepository
from app.application.services.player_service import PlayerService
from app.application.services.team_service import TeamService
from app.application.services.match_service import MatchService
from app.infrastructure.external.sports_data_client import SportsDataClient
from app.application.services.proxy_service import ProxyService
from app.infrastructure.security.api_key_service import APIKey, get_api_key_service, APIKeyService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session."""
    async for session in get_db_session():
        yield session


def get_player_repository(
    db: AsyncSession,
) -> PlayerRepository:
    """Dependency for player repository."""
    return PlayerRepository(db)


def get_team_repository(
    db: AsyncSession,
) -> TeamRepository:
    """Dependency for team repository."""
    return TeamRepository(db)


def get_match_repository(
    db: AsyncSession,
) -> MatchRepository:
    """Dependency for match repository."""
    return MatchRepository(db)


def get_player_service(
    repository: PlayerRepository,
) -> PlayerService:
    """Dependency for player service."""
    return PlayerService(repository)


def get_team_service(
    repository: TeamRepository,
) -> TeamService:
    """Dependency for team service."""
    return TeamService(repository)


def get_match_service(
    repository: MatchRepository,
) -> MatchService:
    """Dependency for match service."""
    return MatchService(repository)


def get_sports_data_client() -> SportsDataClient:
    """Dependency for Sports Data API client."""
    return SportsDataClient()


def get_proxy_service(
    api_client: Optional[SportsDataClient] = Depends(get_sports_data_client),
) -> ProxyService:
    """Dependency for proxy service."""
    return ProxyService(api_client=api_client)


def get_api_key(request: Request) -> APIKey:
    """Dependency to get authenticated API key from request.

    Raises:
        HTTPException: If API key not found or invalid
    """
    api_key = getattr(request.state, "api_key", None)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def get_client_id(request: Request) -> str:
    """Dependency to get client ID from request."""
    return getattr(request.state, "client_id", "anonymous")
