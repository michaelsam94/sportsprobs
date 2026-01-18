"""Player DTOs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PlayerBaseDTO(BaseModel):
    """Base player DTO."""

    name: str = Field(..., min_length=1, max_length=100)
    position: Optional[str] = Field(None, max_length=50)
    team_id: Optional[int] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = Field(None, max_length=100)


class PlayerCreateDTO(PlayerBaseDTO):
    """DTO for creating a player."""

    pass


class PlayerUpdateDTO(BaseModel):
    """DTO for updating a player."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, max_length=50)
    team_id: Optional[int] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = Field(None, max_length=100)


class PlayerResponseDTO(PlayerBaseDTO):
    """DTO for player response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

