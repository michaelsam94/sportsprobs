"""API key management service."""

import secrets
import hashlib
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class APIKey:
    """API key model."""

    def __init__(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        client_id: str,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        is_active: bool = True,
        created_at: datetime = None,
        last_used: datetime = None,
        expires_at: Optional[datetime] = None,
    ):
        self.key_id = key_id
        self.key_hash = key_hash
        self.name = name
        self.client_id = client_id
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_per_hour = rate_limit_per_hour
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.last_used = last_used
        self.expires_at = expires_at

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "client_id": self.client_id,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "APIKey":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            key_hash=data["key_hash"],
            name=data["name"],
            client_id=data["client_id"],
            rate_limit_per_minute=data.get("rate_limit_per_minute", 60),
            rate_limit_per_hour=data.get("rate_limit_per_hour", 1000),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
        )


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, storage_file: Optional[str] = None):
        """Initialize API key service.

        Args:
            storage_file: Path to JSON storage file
        """
        if storage_file is None:
            storage_dir = Path(__file__).parent.parent.parent / "config"
            storage_dir.mkdir(exist_ok=True)
            storage_file = str(storage_dir / "api_keys.json")
        
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, APIKey] = {}
        self._load_keys()

    def _load_keys(self):
        """Load API keys from storage."""
        if not self.storage_file.exists():
            logger.info(f"API keys file not found: {self.storage_file}")
            return

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._keys = {}
            for key_id, key_data in data.get("keys", {}).items():
                try:
                    self._keys[key_id] = APIKey.from_dict(key_data)
                except Exception as e:
                    logger.error(f"Error loading API key {key_id}: {e}")
                    continue

            logger.info(f"Loaded {len(self._keys)} API key(s)")
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")

    def _save_keys(self):
        """Save API keys to storage."""
        try:
            data = {
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "total_keys": len(self._keys),
                },
                "keys": {}
            }

            for key_id, key in self._keys.items():
                data["keys"][key_id] = key.to_dict()

            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._keys)} API key(s)")
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
            raise

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _generate_key() -> str:
        """Generate a new API key."""
        return f"sk_{secrets.token_urlsafe(32)}"

    def create_key(
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

        self._keys[key_id] = api_key
        self._save_keys()

        logger.info(f"Created API key: {key_id} for client: {client_id}")
        return plain_key, api_key

    def validate_key(self, api_key: str) -> Optional[APIKey]:
        """Validate an API key.

        Args:
            api_key: Plain text API key

        Returns:
            APIKey object if valid, None otherwise
        """
        # Reload keys from file to ensure we have the latest keys
        # This is important in multi-process/container environments
        self._load_keys()
        
        key_hash = self._hash_key(api_key)

        for key in self._keys.values():
            if key.key_hash == key_hash:
                # Check if active
                if not key.is_active:
                    logger.warning(f"Inactive API key used: {key.key_id}")
                    return None

                # Check expiration
                if key.expires_at and datetime.utcnow() > key.expires_at:
                    logger.warning(f"Expired API key used: {key.key_id}")
                    return None

                # Update last used
                key.last_used = datetime.utcnow()
                self._save_keys()

                return key

        logger.warning(f"API key validation failed - key not found")
        return None

    def get_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        return self._keys.get(key_id)

    def get_keys_by_client(self, client_id: str) -> List[APIKey]:
        """Get all keys for a client."""
        return [key for key in self._keys.values() if key.client_id == client_id]

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id not in self._keys:
            return False

        self._keys[key_id].is_active = False
        self._save_keys()
        logger.info(f"Revoked API key: {key_id}")
        return True

    def delete_key(self, key_id: str) -> bool:
        """Delete an API key."""
        if key_id not in self._keys:
            return False

        del self._keys[key_id]
        self._save_keys()
        logger.info(f"Deleted API key: {key_id}")
        return True

    def list_keys(self) -> List[APIKey]:
        """List all API keys."""
        return list(self._keys.values())


# Global API key service instance
api_key_service = APIKeyService()

