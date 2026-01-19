"""API key repository for database operations."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.api_key_model import APIKeyModel
from app.infrastructure.security.api_key_service import APIKey


class APIKeyRepository:
    """Repository for API key database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository.

        Args:
            db: Database session
        """
        self.db = db

    async def create(self, api_key: APIKey) -> APIKeyModel:
        """Create a new API key in database.

        Args:
            api_key: APIKey object to create

        Returns:
            Created APIKeyModel
        """
        db_key = APIKeyModel(
            key_id=api_key.key_id,
            key_hash=api_key.key_hash,
            name=api_key.name,
            client_id=api_key.client_id,
            rate_limit_per_minute=api_key.rate_limit_per_minute,
            rate_limit_per_hour=api_key.rate_limit_per_hour,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used=api_key.last_used,
            expires_at=api_key.expires_at,
        )
        self.db.add(db_key)
        await self.db.commit()
        await self.db.refresh(db_key)
        return db_key

    async def get_by_hash(self, key_hash: str) -> Optional[APIKeyModel]:
        """Get API key by hash.

        Args:
            key_hash: Hashed API key

        Returns:
            APIKeyModel if found, None otherwise
        """
        result = await self.db.execute(
            select(APIKeyModel).where(APIKeyModel.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, key_id: str) -> Optional[APIKeyModel]:
        """Get API key by ID.

        Args:
            key_id: API key ID

        Returns:
            APIKeyModel if found, None otherwise
        """
        result = await self.db.execute(
            select(APIKeyModel).where(APIKeyModel.key_id == key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_id(self, client_id: str) -> List[APIKeyModel]:
        """Get all API keys for a client.

        Args:
            client_id: Client ID

        Returns:
            List of APIKeyModel
        """
        result = await self.db.execute(
            select(APIKeyModel).where(APIKeyModel.client_id == client_id)
        )
        return list(result.scalars().all())

    async def list_all(self) -> List[APIKeyModel]:
        """List all API keys.

        Returns:
            List of APIKeyModel
        """
        result = await self.db.execute(select(APIKeyModel))
        return list(result.scalars().all())

    async def update_last_used(self, key_id: str, last_used: datetime) -> bool:
        """Update last used timestamp.

        Args:
            key_id: API key ID
            last_used: Last used timestamp

        Returns:
            True if updated, False otherwise
        """
        result = await self.db.execute(
            update(APIKeyModel)
            .where(APIKeyModel.key_id == key_id)
            .values(last_used=last_used)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke(self, key_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: API key ID

        Returns:
            True if revoked, False otherwise
        """
        result = await self.db.execute(
            update(APIKeyModel)
            .where(APIKeyModel.key_id == key_id)
            .values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def delete(self, key_id: str) -> bool:
        """Delete an API key.

        Args:
            key_id: API key ID

        Returns:
            True if deleted, False otherwise
        """
        result = await self.db.execute(
            delete(APIKeyModel).where(APIKeyModel.key_id == key_id)
        )
        await self.db.commit()
        return result.rowcount > 0

