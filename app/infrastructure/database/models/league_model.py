"""League database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class LeagueModel(Base):
    """League database model."""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    sport = Column(String(50), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    season_start_month = Column(Integer, nullable=True)  # 1-12
    season_end_month = Column(Integer, nullable=True)  # 1-12
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    teams = relationship("TeamModel", back_populates="league", cascade="all, delete-orphan")
    matches = relationship("MatchModel", back_populates="league", cascade="all, delete-orphan")
    historical_results = relationship("HistoricalResultModel", back_populates="league", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_league_sport_active", "sport", "is_active"),
        Index("idx_league_country_sport", "country", "sport"),
    )

