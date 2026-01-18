"""DTOs for probability model configuration."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ModelWeightsDTO(BaseModel):
    """Model weights configuration."""

    home_advantage: float = Field(default=0.3, ge=0.0, le=1.0, description="Home advantage factor")
    form_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Recent form weight")
    head_to_head_weight: float = Field(default=0.1, ge=0.0, le=1.0, description="Head-to-head weight")
    league_position_weight: float = Field(default=0.1, ge=0.0, le=1.0, description="League position weight")
    goals_for_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Goals for weight")
    goals_against_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Goals against weight")

    @field_validator('*')
    @classmethod
    def validate_weights(cls, v):
        """Validate weight values."""
        if not isinstance(v, (int, float)):
            raise ValueError("Weight must be a number")
        return float(v)


class ThresholdsDTO(BaseModel):
    """Thresholds configuration."""

    min_goals_for_avg: float = Field(default=0.0, ge=0.0, description="Minimum goals for average")
    max_goals_for_avg: float = Field(default=10.0, ge=0.0, description="Maximum goals for average")
    min_goals_against_avg: float = Field(default=0.0, ge=0.0, description="Minimum goals against average")
    max_goals_against_avg: float = Field(default=10.0, ge=0.0, description="Maximum goals against average")
    min_league_avg_goals: float = Field(default=0.5, ge=0.0, description="Minimum league average goals")
    max_league_avg_goals: float = Field(default=5.0, ge=0.0, description="Maximum league average goals")
    min_home_advantage: float = Field(default=0.0, ge=0.0, description="Minimum home advantage")
    max_home_advantage: float = Field(default=1.0, ge=0.0, description="Maximum home advantage")
    probability_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Confidence threshold for probabilities")

    @field_validator('*')
    @classmethod
    def validate_thresholds(cls, v):
        """Validate threshold values."""
        if not isinstance(v, (int, float)):
            raise ValueError("Threshold must be a number")
        return float(v)


class FeatureFlagsDTO(BaseModel):
    """Feature flags configuration."""

    enable_form_factor: bool = Field(default=False, description="Enable recent form factor")
    enable_head_to_head: bool = Field(default=False, description="Enable head-to-head history")
    enable_league_position: bool = Field(default=False, description="Enable league position factor")
    enable_weather_adjustment: bool = Field(default=False, description="Enable weather adjustments")
    enable_injury_adjustment: bool = Field(default=False, description="Enable injury adjustments")
    enable_motivation_factor: bool = Field(default=False, description="Enable motivation factor")
    use_weighted_averages: bool = Field(default=False, description="Use weighted averages for recent matches")
    enable_advanced_xg: bool = Field(default=False, description="Enable advanced xG calculation")


class ProbabilityConfigDTO(BaseModel):
    """Complete probability model configuration."""

    version: str = Field(..., description="Configuration version")
    model_weights: ModelWeightsDTO = Field(default_factory=ModelWeightsDTO)
    thresholds: ThresholdsDTO = Field(default_factory=ThresholdsDTO)
    feature_flags: FeatureFlagsDTO = Field(default_factory=FeatureFlagsDTO)
    description: Optional[str] = Field(None, description="Configuration description")
    is_active: bool = Field(default=False, description="Whether this configuration is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        """Validate version format."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Version must be a non-empty string")
        return v.strip()


class ProbabilityConfigCreateDTO(BaseModel):
    """DTO for creating a new configuration."""

    version: str = Field(..., description="Configuration version")
    model_weights: Optional[ModelWeightsDTO] = None
    thresholds: Optional[ThresholdsDTO] = None
    feature_flags: Optional[FeatureFlagsDTO] = None
    description: Optional[str] = None
    is_active: bool = Field(default=False, description="Whether to activate this configuration")


class ProbabilityConfigUpdateDTO(BaseModel):
    """DTO for updating a configuration."""

    version: Optional[str] = None
    model_weights: Optional[ModelWeightsDTO] = None
    thresholds: Optional[ThresholdsDTO] = None
    feature_flags: Optional[FeatureFlagsDTO] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProbabilityConfigResponseDTO(ProbabilityConfigDTO):
    """Response DTO for configuration."""

    pass

