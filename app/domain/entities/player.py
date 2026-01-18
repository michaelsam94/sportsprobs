"""Player domain entity."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Player:
    """Player domain entity."""

    id: Optional[int] = None
    name: str = ""
    position: str = ""
    team_id: Optional[int] = None
    jersey_number: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.name:
            raise ValueError("Player name is required")

