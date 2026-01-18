"""Simple authentication/authorization utilities.

Note: This is a basic implementation. For production, use proper
authentication (JWT, OAuth, etc.) and authorization frameworks.
"""

from typing import Optional
from fastapi import Header, HTTPException, status


def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify admin authorization token.

    Args:
        authorization: Authorization header value

    Returns:
        True if authorized

    Raises:
        HTTPException: If not authorized
    """
    from app.core.config import settings

    # In production, use proper JWT validation
    # For now, check against a simple token from settings
    admin_token = getattr(settings, 'ADMIN_TOKEN', None)

    if not admin_token:
        # If no admin token configured, allow access (development mode)
        return True

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token != admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )

    return True

