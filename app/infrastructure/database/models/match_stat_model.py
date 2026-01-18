"""Match statistics database model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class MatchStatModel(Base):
    """Match statistics database model."""

    __tablename__ = "match_stats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # General statistics
    possession_percent = Column(Numeric(5, 2), nullable=True)
    total_shots = Column(Integer, default=0, nullable=False)
    shots_on_target = Column(Integer, default=0, nullable=False)
    shots_off_target = Column(Integer, default=0, nullable=False)
    corners = Column(Integer, default=0, nullable=False)
    fouls = Column(Integer, default=0, nullable=False)
    yellow_cards = Column(Integer, default=0, nullable=False)
    red_cards = Column(Integer, default=0, nullable=False)
    offsides = Column(Integer, default=0, nullable=False)
    
    # Football/Soccer specific
    passes_total = Column(Integer, default=0, nullable=False)
    passes_accurate = Column(Integer, default=0, nullable=False)
    pass_accuracy = Column(Numeric(5, 2), nullable=True)
    crosses_total = Column(Integer, default=0, nullable=False)
    crosses_accurate = Column(Integer, default=0, nullable=False)
    
    # Basketball specific
    field_goals_made = Column(Integer, default=0, nullable=False)
    field_goals_attempted = Column(Integer, default=0, nullable=False)
    three_pointers_made = Column(Integer, default=0, nullable=False)
    three_pointers_attempted = Column(Integer, default=0, nullable=False)
    free_throws_made = Column(Integer, default=0, nullable=False)
    free_throws_attempted = Column(Integer, default=0, nullable=False)
    rebounds_offensive = Column(Integer, default=0, nullable=False)
    rebounds_defensive = Column(Integer, default=0, nullable=False)
    rebounds_total = Column(Integer, default=0, nullable=False)
    assists = Column(Integer, default=0, nullable=False)
    steals = Column(Integer, default=0, nullable=False)
    blocks = Column(Integer, default=0, nullable=False)
    turnovers = Column(Integer, default=0, nullable=False)
    personal_fouls = Column(Integer, default=0, nullable=False)
    
    # American Football specific
    first_downs = Column(Integer, default=0, nullable=False)
    rushing_yards = Column(Integer, default=0, nullable=False)
    passing_yards = Column(Integer, default=0, nullable=False)
    total_yards = Column(Integer, default=0, nullable=False)
    penalties = Column(Integer, default=0, nullable=False)
    penalty_yards = Column(Integer, default=0, nullable=False)
    time_of_possession = Column(String(10), nullable=True)  # Format: "MM:SS"
    
    # Baseball specific
    hits = Column(Integer, default=0, nullable=False)
    runs = Column(Integer, default=0, nullable=False)
    errors = Column(Integer, default=0, nullable=False)
    strikeouts = Column(Integer, default=0, nullable=False)
    walks = Column(Integer, default=0, nullable=False)
    
    # Metadata
    is_home_team = Column(Boolean, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    match = relationship("MatchModel", back_populates="match_stats")
    team = relationship("TeamModel", back_populates="match_stats")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_match_stat_match_team", "match_id", "team_id"),
        Index("idx_match_stat_team_match", "team_id", "match_id"),
        Index("idx_match_stat_match_home", "match_id", "is_home_team"),
    )

