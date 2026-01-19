"""Security management endpoints (Admin only)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.auth import verify_admin_token
from app.core.dependencies import get_db, get_api_key_service
from app.infrastructure.security.api_key_service import APIKey, APIKeyService
from app.infrastructure.security.ip_throttle import ip_throttle_service

router = APIRouter()


class APIKeyCreateDTO(BaseModel):
    """DTO for creating API key."""

    name: str = Field(..., description="Key name/description")
    client_id: str = Field(..., description="Client identifier")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=10000)
    expires_days: Optional[int] = Field(None, ge=1, description="Days until expiration")


class APIKeyResponseDTO(BaseModel):
    """DTO for API key response."""

    key_id: str
    name: str
    client_id: str
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    is_active: bool
    created_at: str
    last_used: Optional[str] = None
    expires_at: Optional[str] = None


class APIKeyCreateResponseDTO(BaseModel):
    """DTO for API key creation response (includes plain key)."""

    api_key: str  # Plain text key (only shown once)
    key_info: APIKeyResponseDTO


@router.post("/api-keys", response_model=APIKeyCreateResponseDTO, status_code=201, tags=["admin", "security"])
@limiter.limit("10/minute")
async def create_api_key(
    request: Request,
    key_data: APIKeyCreateDTO,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key (Admin only)."""
    verify_admin_token(authorization)

    try:
        api_key_service = get_api_key_service(db)
        plain_key, api_key = await api_key_service.create_key(
            name=key_data.name,
            client_id=key_data.client_id,
            rate_limit_per_minute=key_data.rate_limit_per_minute,
            rate_limit_per_hour=key_data.rate_limit_per_hour,
            expires_days=key_data.expires_days,
        )

        return APIKeyCreateResponseDTO(
            api_key=plain_key,
            key_info=APIKeyResponseDTO(
                key_id=api_key.key_id,
                name=api_key.name,
                client_id=api_key.client_id,
                rate_limit_per_minute=api_key.rate_limit_per_minute,
                rate_limit_per_hour=api_key.rate_limit_per_hour,
                is_active=api_key.is_active,
                created_at=api_key.created_at.isoformat(),
                last_used=api_key.last_used.isoformat() if api_key.last_used else None,
                expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.get("/api-keys", response_model=List[APIKeyResponseDTO], tags=["admin", "security"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def list_api_keys(
    request: Request,
    client_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (Admin only)."""
    verify_admin_token(authorization)

    try:
        api_key_service = get_api_key_service(db)
        if client_id:
            keys = await api_key_service.get_keys_by_client(client_id)
        else:
            keys = await api_key_service.list_keys()

        return [
            APIKeyResponseDTO(
                key_id=key.key_id,
                name=key.name,
                client_id=key.client_id,
                rate_limit_per_minute=key.rate_limit_per_minute,
                rate_limit_per_hour=key.rate_limit_per_hour,
                is_active=key.is_active,
                created_at=key.created_at.isoformat(),
                last_used=key.last_used.isoformat() if key.last_used else None,
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
            )
            for key in keys
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        )


@router.delete("/api-keys/{key_id}", status_code=204, tags=["admin", "security"])
@limiter.limit("10/minute")
async def revoke_api_key(
    request: Request,
    key_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key (Admin only)."""
    verify_admin_token(authorization)

    try:
        api_key_service = get_api_key_service(db)
        deleted = await api_key_service.revoke_key(key_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} not found",
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}",
        )


@router.get("/ip-status/{ip_address}", tags=["admin", "security"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_ip_status(
    request: Request,
    ip_address: str,
    authorization: Optional[str] = Header(None),
):
    """Get IP address status (Admin only)."""
    verify_admin_token(authorization)

    try:
        status_info = ip_throttle_service.get_ip_status(ip_address)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get IP status: {str(e)}",
        )


@router.post("/ip-unblock/{ip_address}", tags=["admin", "security"])
@limiter.limit("10/minute")
async def unblock_ip(
    request: Request,
    ip_address: str,
    authorization: Optional[str] = Header(None),
):
    """Unblock an IP address (Admin only)."""
    verify_admin_token(authorization)

    try:
        unblocked = await ip_throttle_service.unblock_ip(ip_address)
        if not unblocked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IP {ip_address} is not blocked",
            )
        return {"message": f"IP {ip_address} unblocked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock IP: {str(e)}",
        )


@router.get("/blocked-ips", tags=["admin", "security"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_blocked_ips(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Get list of blocked IP addresses (Admin only)."""
    verify_admin_token(authorization)

    try:
        blocked_ips = ip_throttle_service.get_blocked_ips()
        return {"blocked_ips": blocked_ips, "count": len(blocked_ips)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blocked IPs: {str(e)}",
        )

