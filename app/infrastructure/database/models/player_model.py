"""Player database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class PlayerModel(Base):
    """Player database model."""

    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    position = Column(String(50), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    jersey_number = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    nationality = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    team = relationship("TeamModel", back_populates="players")

