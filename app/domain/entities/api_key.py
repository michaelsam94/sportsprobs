"""API key domain entity."""

from typing import Optional, Dict
from datetime import datetime

from app.infrastructure.database.models.api_key_model import APIKeyModel


class APIKey:
    """API key domain entity."""

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

    @classmethod
    def from_model(cls, model: APIKeyModel) -> "APIKey":
        """Create APIKey from database model."""
        return cls(
            key_id=model.key_id,
            key_hash=model.key_hash,
            name=model.name,
            client_id=model.client_id,
            rate_limit_per_minute=model.rate_limit_per_minute,
            rate_limit_per_hour=model.rate_limit_per_hour,
            is_active=model.is_active,
            created_at=model.created_at,
            last_used=model.last_used,
            expires_at=model.expires_at,
        )

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

