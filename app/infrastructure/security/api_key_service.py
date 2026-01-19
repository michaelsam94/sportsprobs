"""API key management service with PostgreSQL storage."""

import secrets
import hashlib
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.api_key_repository import APIKeyRepository
from app.domain.entities.api_key import APIKey

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys with PostgreSQL storage."""

    def __init__(self, db: AsyncSession):
        """Initialize API key service.

        Args:
            db: Database session
        """
        self.db = db
        self.repository = APIKeyRepository(db)

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _generate_key() -> str:
        """Generate a new API key."""
        return f"sk_{secrets.token_urlsafe(32)}"

    async def create_key(
        self,
        name: str,
        client_id: str,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        expires_days: Optional[int] = None,
    ) -> tuple[str, APIKey]:
        """Create a new API key.

        Args:
            name: Key name/description
            client_id: Client identifier
            rate_limit_per_minute: Rate limit per minute
            rate_limit_per_hour: Rate limit per hour
            expires_days: Days until expiration (None = no expiration)

        Returns:
            Tuple of (plain_text_key, APIKey object)
        """
        # Generate key
        plain_key = self._generate_key()
        key_hash = self._hash_key(plain_key)
        key_id = secrets.token_urlsafe(16)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # Create API key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            client_id=client_id,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            expires_at=expires_at,
        )

        # Save to database
        await self.repository.create(api_key)

        logger.info(f"Created API key: {key_id} for client: {client_id}")
        return plain_key, api_key

    async def validate_key(self, api_key: str) -> Optional[APIKey]:
        """Validate an API key.

        Args:
            api_key: Plain text API key

        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self._hash_key(api_key)

        # Get from database
        db_key = await self.repository.get_by_hash(key_hash)
        if not db_key:
            logger.warning("API key validation failed - key not found")
            return None

        # Check if active
        if not db_key.is_active:
            logger.warning(f"Inactive API key used: {db_key.key_id}")
            return None

        # Check expiration
        if db_key.expires_at and datetime.utcnow() > db_key.expires_at:
            logger.warning(f"Expired API key used: {db_key.key_id}")
            return None

        # Update last used
        await self.repository.update_last_used(db_key.key_id, datetime.utcnow())

        return APIKey.from_model(db_key)

    async def get_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        db_key = await self.repository.get_by_id(key_id)
        if db_key:
            return APIKey.from_model(db_key)
        return None

    async def get_keys_by_client(self, client_id: str) -> List[APIKey]:
        """Get all keys for a client."""
        db_keys = await self.repository.get_by_client_id(client_id)
        return [APIKey.from_model(key) for key in db_keys]

    async def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        result = await self.repository.revoke(key_id)
        if result:
            logger.info(f"Revoked API key: {key_id}")
        return result

    async def delete_key(self, key_id: str) -> bool:
        """Delete an API key."""
        result = await self.repository.delete(key_id)
        if result:
            logger.info(f"Deleted API key: {key_id}")
        return result

    async def list_keys(self) -> List[APIKey]:
        """List all API keys."""
        db_keys = await self.repository.list_all()
        return [APIKey.from_model(key) for key in db_keys]


def get_api_key_service(db: AsyncSession) -> APIKeyService:
    """Dependency to get API key service."""
    return APIKeyService(db)
