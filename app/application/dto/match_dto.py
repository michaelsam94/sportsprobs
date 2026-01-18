"""Match DTOs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MatchBaseDTO(BaseModel):
    """Base match DTO."""

    home_team_id: int = Field(..., gt=0)
    away_team_id: int = Field(..., gt=0)
    sport: str = Field(..., min_length=1, max_length=50)
    league: Optional[str] = Field(None, max_length=100)
    match_date: datetime
    status: str = Field(default="scheduled", max_length=20)
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)
    venue: Optional[str] = Field(None, max_length=200)
    attendance: Optional[int] = Field(None, ge=0)


class MatchCreateDTO(MatchBaseDTO):
    """DTO for creating a match."""

    pass


class MatchUpdateDTO(BaseModel):
    """DTO for updating a match."""

    home_team_id: Optional[int] = Field(None, gt=0)
    away_team_id: Optional[int] = Field(None, gt=0)
    sport: Optional[str] = Field(None, min_length=1, max_length=50)
    league: Optional[str] = Field(None, max_length=100)
    match_date: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=20)
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)
    venue: Optional[str] = Field(None, max_length=200)
    attendance: Optional[int] = Field(None, ge=0)


class MatchResponseDTO(MatchBaseDTO):
    """DTO for match response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

