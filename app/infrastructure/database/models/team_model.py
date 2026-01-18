"""Team database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class TeamModel(Base):
    """Team database model."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(10), nullable=True, unique=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    conference = Column(String(50), nullable=True, index=True)
    division = Column(String(50), nullable=True, index=True)
    founded_year = Column(Integer, nullable=True)
    logo_url = Column(String(500), nullable=True)
    stadium_name = Column(String(200), nullable=True)
    stadium_capacity = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    league = relationship("LeagueModel", back_populates="teams")
    players = relationship("PlayerModel", back_populates="team", cascade="all, delete-orphan")
    home_matches = relationship(
        "MatchModel",
        foreign_keys="MatchModel.home_team_id",
        back_populates="home_team",
        cascade="all, delete-orphan"
    )
    away_matches = relationship(
        "MatchModel",
        foreign_keys="MatchModel.away_team_id",
        back_populates="away_team",
        cascade="all, delete-orphan"
    )
    match_stats = relationship("MatchStatModel", back_populates="team", cascade="all, delete-orphan")
    historical_results = relationship("HistoricalResultModel", back_populates="team", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_team_league_active", "league_id", "is_active"),
        Index("idx_team_conference_division", "conference", "division"),
        Index("idx_team_league_name", "league_id", "name"),
    )
