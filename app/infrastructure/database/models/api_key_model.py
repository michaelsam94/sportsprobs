"""API key database model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index

from app.infrastructure.database.base import Base


class APIKeyModel(Base):
    """API key database model."""

    __tablename__ = "api_keys"

    key_id = Column(String(50), primary_key=True, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256 hash
    name = Column(String(100), nullable=False)
    client_id = Column(String(100), nullable=False, index=True)
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_hour = Column(Integer, default=1000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_api_keys_client_id", "client_id"),
        Index("idx_api_keys_is_active", "is_active"),
        Index("idx_api_keys_key_hash", "key_hash"),
    )

