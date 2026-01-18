"""Match database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class MatchModel(Base):
    """Match database model."""

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    season = Column(Integer, nullable=False, index=True)
    week = Column(Integer, nullable=True, index=True)  # For leagues with weeks
    round = Column(Integer, nullable=True, index=True)  # For tournaments
    match_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="scheduled", nullable=False, index=True)
    # Status values: scheduled, live, finished, cancelled, postponed
    
    # Scores
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    home_score_overtime = Column(Integer, nullable=True)
    away_score_overtime = Column(Integer, nullable=True)
    
    # Venue information
    venue = Column(String(200), nullable=True, index=True)
    attendance = Column(Integer, nullable=True)
    weather_conditions = Column(String(100), nullable=True)
    temperature = Column(Numeric(5, 2), nullable=True)
    
    # Match metadata
    is_playoff = Column(Boolean, default=False, nullable=False, index=True)
    is_neutral_venue = Column(Boolean, default=False, nullable=False)
    referee = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    league = relationship("LeagueModel", back_populates="matches")
    home_team = relationship("TeamModel", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("TeamModel", foreign_keys=[away_team_id], back_populates="away_matches")
    match_stats = relationship("MatchStatModel", back_populates="match", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_match_league_season", "league_id", "season"),
        Index("idx_match_league_date", "league_id", "match_date"),
        Index("idx_match_teams", "home_team_id", "away_team_id"),
        Index("idx_match_season_status", "season", "status"),
        Index("idx_match_date_status", "match_date", "status"),
        Index("idx_match_team_season", "home_team_id", "season"),
        Index("idx_match_away_team_season", "away_team_id", "season"),
    )
