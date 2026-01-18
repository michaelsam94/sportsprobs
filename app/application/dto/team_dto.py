"""Team DTOs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TeamBaseDTO(BaseModel):
    """Base team DTO."""

    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=10)
    sport: str = Field(..., min_length=1, max_length=50)
    league: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    logo_url: Optional[str] = Field(None, max_length=500)


class TeamCreateDTO(TeamBaseDTO):
    """DTO for creating a team."""

    pass


class TeamUpdateDTO(BaseModel):
    """DTO for updating a team."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=10)
    sport: Optional[str] = Field(None, min_length=1, max_length=50)
    league: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    logo_url: Optional[str] = Field(None, max_length=500)


class TeamResponseDTO(TeamBaseDTO):
    """DTO for team response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

