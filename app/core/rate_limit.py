"""Rate limiting utilities."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

# Global limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter


def rate_limit_decorator(limit: str = None):
    """Create a rate limit decorator."""
    if limit is None:
        limit = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    
    def decorator(func):
        return limiter.limit(limit)(func)
    return decorator

