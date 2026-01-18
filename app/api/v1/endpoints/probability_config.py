"""Admin endpoints for probability model configuration."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.auth import verify_admin_token
from app.application.dto.probability_config_dto import (
    ProbabilityConfigResponseDTO,
    ProbabilityConfigCreateDTO,
    ProbabilityConfigUpdateDTO,
)
from app.infrastructure.config.probability_config_service import config_service

router = APIRouter()


@router.get("", response_model=List[ProbabilityConfigResponseDTO], tags=["admin", "probability-config"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_all_configs(
    request,
    authorization: Optional[str] = Header(None),
):
    """Get all probability model configurations (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        configs = config_service.get_all_configs()
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configurations: {str(e)}",
        )


@router.get("/active", response_model=ProbabilityConfigResponseDTO, tags=["admin", "probability-config"])
async def get_active_config(
    authorization: Optional[str] = Header(None),
):
    """Get active probability model configuration."""
    verify_admin_token(authorization)
    
    try:
        config = config_service.get_config()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active configuration found",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active configuration: {str(e)}",
        )


@router.get("/{version}", response_model=ProbabilityConfigResponseDTO, tags=["admin", "probability-config"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_config_by_version(
    request,
    version: str,
    authorization: Optional[str] = Header(None),
):
    """Get probability model configuration by version (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        config = config_service.get_config(version=version)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration version {version} not found",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}",
        )


@router.post("", response_model=ProbabilityConfigResponseDTO, status_code=201, tags=["admin", "probability-config"])
@limiter.limit("10/minute")
async def create_config(
    request,
    config_data: ProbabilityConfigCreateDTO,
    authorization: Optional[str] = Header(None),
):
    """Create a new probability model configuration (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        # Validate configuration
        from app.application.dto.probability_config_dto import ProbabilityConfigDTO, ModelWeightsDTO, ThresholdsDTO, FeatureFlagsDTO
        
        # Create full config for validation
        full_config = ProbabilityConfigDTO(
            version=config_data.version,
            model_weights=config_data.model_weights or ModelWeightsDTO(),
            thresholds=config_data.thresholds or ThresholdsDTO(),
            feature_flags=config_data.feature_flags or FeatureFlagsDTO(),
            description=config_data.description,
            is_active=config_data.is_active,
        )
        
        errors = config_service.validate_config(full_config)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"validation_errors": errors},
            )
        
        config = config_service.create_config(config_data)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}",
        )


@router.put("/{version}", response_model=ProbabilityConfigResponseDTO, tags=["admin", "probability-config"])
@limiter.limit("10/minute")
async def update_config(
    request,
    version: str,
    config_data: ProbabilityConfigUpdateDTO,
    authorization: Optional[str] = Header(None),
):
    """Update a probability model configuration (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        # Get current config
        current_config = config_service.get_config(version=version)
        if not current_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration version {version} not found",
            )
        
        # Merge updates
        from app.application.dto.probability_config_dto import ProbabilityConfigDTO, ModelWeightsDTO, ThresholdsDTO, FeatureFlagsDTO
        
        updated_config = ProbabilityConfigDTO(
            version=config_data.version or current_config.version,
            model_weights=config_data.model_weights or current_config.model_weights,
            thresholds=config_data.thresholds or current_config.thresholds,
            feature_flags=config_data.feature_flags or current_config.feature_flags,
            description=config_data.description if config_data.description is not None else current_config.description,
            is_active=config_data.is_active if config_data.is_active is not None else current_config.is_active,
        )
        
        # Validate
        errors = config_service.validate_config(updated_config)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"validation_errors": errors},
            )
        
        config = config_service.update_config(version, config_data)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.delete("/{version}", status_code=204, tags=["admin", "probability-config"])
@limiter.limit("10/minute")
async def delete_config(
    request,
    version: str,
    authorization: Optional[str] = Header(None),
):
    """Delete a probability model configuration (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        deleted = config_service.delete_config(version)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration version {version} not found",
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}",
        )


@router.post("/{version}/activate", response_model=ProbabilityConfigResponseDTO, tags=["admin", "probability-config"])
@limiter.limit("10/minute")
async def activate_config(
    request,
    version: str,
    authorization: Optional[str] = Header(None),
):
    """Activate a probability model configuration (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        config = config_service.activate_config(version)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate configuration: {str(e)}",
        )


@router.post("/validate", tags=["admin", "probability-config"])
@limiter.limit("10/minute")
async def validate_config(
    request,
    config_data: ProbabilityConfigCreateDTO,
    authorization: Optional[str] = Header(None),
):
    """Validate a probability model configuration (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        from app.application.dto.probability_config_dto import ProbabilityConfigDTO, ModelWeightsDTO, ThresholdsDTO, FeatureFlagsDTO
        
        full_config = ProbabilityConfigDTO(
            version=config_data.version,
            model_weights=config_data.model_weights or ModelWeightsDTO(),
            thresholds=config_data.thresholds or ThresholdsDTO(),
            feature_flags=config_data.feature_flags or FeatureFlagsDTO(),
            description=config_data.description,
            is_active=config_data.is_active,
        )
        
        errors = config_service.validate_config(full_config)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}",
        )

