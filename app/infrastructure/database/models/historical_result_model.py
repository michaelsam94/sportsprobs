"""Historical results database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class HistoricalResultModel(Base):
    """Historical results database model for aggregated statistics."""

    __tablename__ = "historical_results"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Time period
    season = Column(Integer, nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # 'season', 'month', 'week', 'custom'
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Match statistics
    matches_played = Column(Integer, default=0, nullable=False)
    matches_won = Column(Integer, default=0, nullable=False)
    matches_drawn = Column(Integer, default=0, nullable=False)
    matches_lost = Column(Integer, default=0, nullable=False)
    
    # Goals/Points
    goals_for = Column(Integer, default=0, nullable=False)
    goals_against = Column(Integer, default=0, nullable=False)
    goal_difference = Column(Integer, default=0, nullable=False)
    points = Column(Integer, default=0, nullable=False)  # League points
    
    # Home/Away split
    home_matches_played = Column(Integer, default=0, nullable=False)
    home_matches_won = Column(Integer, default=0, nullable=False)
    home_matches_drawn = Column(Integer, default=0, nullable=False)
    home_matches_lost = Column(Integer, default=0, nullable=False)
    home_goals_for = Column(Integer, default=0, nullable=False)
    home_goals_against = Column(Integer, default=0, nullable=False)
    
    away_matches_played = Column(Integer, default=0, nullable=False)
    away_matches_won = Column(Integer, default=0, nullable=False)
    away_matches_drawn = Column(Integer, default=0, nullable=False)
    away_matches_lost = Column(Integer, default=0, nullable=False)
    away_goals_for = Column(Integer, default=0, nullable=False)
    away_goals_against = Column(Integer, default=0, nullable=False)
    
    # Performance metrics
    win_percentage = Column(Numeric(5, 2), nullable=True)
    average_goals_for = Column(Numeric(5, 2), nullable=True)
    average_goals_against = Column(Numeric(5, 2), nullable=True)
    
    # Streaks
    current_win_streak = Column(Integer, default=0, nullable=False)
    current_loss_streak = Column(Integer, default=0, nullable=False)
    current_unbeaten_streak = Column(Integer, default=0, nullable=False)
    
    # League position
    league_position = Column(Integer, nullable=True, index=True)
    
    # Metadata
    last_updated_match_id = Column(Integer, ForeignKey("matches.id", ondelete="SET NULL"), nullable=True)
    is_final = Column(Boolean, default=False, nullable=False, index=True)  # True when period is complete
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    league = relationship("LeagueModel", back_populates="historical_results")
    team = relationship("TeamModel", back_populates="historical_results")
    last_updated_match = relationship("MatchModel", foreign_keys=[last_updated_match_id])

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_historical_league_season", "league_id", "season"),
        Index("idx_historical_team_season", "team_id", "season"),
        Index("idx_historical_league_team_season", "league_id", "team_id", "season"),
        Index("idx_historical_season_position", "season", "league_position"),
        Index("idx_historical_league_season_position", "league_id", "season", "league_position"),
        Index("idx_historical_period_type", "period_type", "season"),
    )

