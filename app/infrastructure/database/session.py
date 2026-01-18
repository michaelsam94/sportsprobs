"""Database session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.base import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

