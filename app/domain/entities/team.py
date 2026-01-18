"""Team domain entity."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Team:
    """Team domain entity."""

    id: Optional[int] = None
    name: str = ""
    code: Optional[str] = None
    sport: str = ""
    league: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    founded_year: Optional[int] = None
    logo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.name:
            raise ValueError("Team name is required")
        if not self.sport:
            raise ValueError("Sport is required")

