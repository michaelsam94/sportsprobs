"""Match domain entity."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Match:
    """Match domain entity."""

    id: Optional[int] = None
    home_team_id: int = 0
    away_team_id: int = 0
    sport: str = ""
    league: Optional[str] = None
    match_date: datetime = None
    status: str = "scheduled"  # scheduled, live, finished, cancelled
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    attendance: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.home_team_id or not self.away_team_id:
            raise ValueError("Both home and away team IDs are required")
        if self.home_team_id == self.away_team_id:
            raise ValueError("Home and away teams must be different")
        if not self.sport:
            raise ValueError("Sport is required")
        if not self.match_date:
            raise ValueError("Match date is required")

