"""Example protected endpoint demonstrating security features."""

from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.dependencies import get_api_key, get_client_id
from app.infrastructure.security.api_key_service import APIKey

router = APIRouter()


class ProtectedResponse(BaseModel):
    """Response model for protected endpoint."""

    message: str
    client_id: str
    api_key_name: str
    rate_limit_per_minute: int
    rate_limit_per_hour: int


@router.get("/protected", response_model=ProtectedResponse, tags=["example"])
async def protected_endpoint(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    client_id: str = Depends(get_client_id),
):
    """Example protected endpoint requiring API key authentication.

    This endpoint demonstrates:
    - API key authentication (required)
    - Per-client rate limiting (from API key settings)
    - IP throttling (automatic via middleware)
    - Abuse prevention (automatic via middleware)

    Headers required:
    - Authorization: ApiKey <your-api-key>
    OR
    - X-API-Key: <your-api-key>

    Example:
        curl -H "Authorization: ApiKey sk_..." http://localhost:8000/api/v1/protected
    """
    return ProtectedResponse(
        message="This is a protected endpoint. Your API key is valid!",
        client_id=client_id,
        api_key_name=api_key.name,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
    )


@router.get("/protected/stats", tags=["example"])
async def protected_stats_endpoint(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
):
    """Another protected endpoint showing request statistics.

    This endpoint shows:
    - Client information from API key
    - Rate limit information
    - Request metadata
    """
    return {
        "client_id": api_key.client_id,
        "api_key_name": api_key.name,
        "rate_limits": {
            "per_minute": api_key.rate_limit_per_minute,
            "per_hour": api_key.rate_limit_per_hour,
        },
        "key_created_at": api_key.created_at.isoformat(),
        "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
        "client_ip": getattr(request.state, "client_ip", "unknown"),
    }

