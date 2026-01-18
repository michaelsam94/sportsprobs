"""Decorator-based caching for FastAPI endpoints."""

import hashlib
import json
import logging
from typing import Callable, Optional, Any, Dict
from functools import wraps
from inspect import signature

from app.infrastructure.cache.cache_manager import cache_manager, CacheType

logger = logging.getLogger(__name__)


def cache_response(
    cache_type: CacheType = CacheType.API_RESPONSE,
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    include_query_params: bool = True,
    include_path_params: bool = True,
    include_request_body: bool = False,
):
    """Decorator to cache FastAPI endpoint responses.

    Args:
        cache_type: Type of cache to use
        ttl: Time to live in seconds (uses default if None)
        key_prefix: Optional prefix for cache key
        include_query_params: Include query parameters in cache key
        include_path_params: Include path parameters in cache key
        include_request_body: Include request body in cache key

    Example:
        @router.get("/teams")
        @cache_response(cache_type=CacheType.API_RESPONSE, ttl=300)
        async def get_teams(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and parameters
            cache_key_parts = [func.__name__]

            # Include path parameters
            if include_path_params:
                sig = signature(func)
                for param_name, param_value in zip(sig.parameters, args):
                    if param_name not in ['request', 'db', 'service']:
                        cache_key_parts.append(f"{param_name}:{param_value}")

            # Include query parameters from kwargs
            if include_query_params:
                query_params = {
                    k: v for k, v in kwargs.items()
                    if k not in ['request', 'db', 'service', 'skip', 'limit']
                    and not k.startswith('_')
                }
                if query_params:
                    cache_key_parts.append(json.dumps(query_params, sort_keys=True))

            # Include request body if needed
            if include_request_body and 'request' in kwargs:
                # This would need request body parsing - simplified for now
                pass

            # Generate cache key hash
            cache_key_string = "_".join(str(p) for p in cache_key_parts)
            cache_key = hashlib.md5(cache_key_string.encode()).hexdigest()

            # Try to get from cache
            cached_value = await cache_manager.get(
                cache_type=cache_type,
                key=cache_key,
                prefix=key_prefix,
            )

            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache the result
            await cache_manager.set(
                cache_type=cache_type,
                key=cache_key,
                value=result,
                ttl=ttl,
                prefix=key_prefix,
            )

            return result

        return wrapper
    return decorator


def cache_live_matches(
    ttl: int = 60,
    key_prefix: str = "live",
):
    """Decorator specifically for live matches caching.

    Args:
        ttl: Time to live in seconds (default: 60)
        key_prefix: Key prefix (default: "live")

    Example:
        @router.get("/matches/live")
        @cache_live_matches(ttl=30)
        async def get_live_matches(...):
            ...
    """
    return cache_response(
        cache_type=CacheType.LIVE_MATCHES,
        ttl=ttl,
        key_prefix=key_prefix,
    )


def cache_historical_data(
    ttl: int = 3600,
    key_prefix: Optional[str] = None,
):
    """Decorator specifically for historical data caching.

    Args:
        ttl: Time to live in seconds (default: 3600)
        key_prefix: Optional key prefix

    Example:
        @router.get("/historical/standings")
        @cache_historical_data(ttl=1800)
        async def get_standings(...):
            ...
    """
    return cache_response(
        cache_type=CacheType.HISTORICAL_DATA,
        ttl=ttl,
        key_prefix=key_prefix,
    )


def invalidate_cache(
    cache_type: CacheType,
    key_pattern: Optional[str] = None,
    key_prefix: Optional[str] = None,
):
    """Decorator to invalidate cache after function execution.

    Args:
        cache_type: Type of cache to invalidate
        key_pattern: Pattern to match keys (None = all)
        key_prefix: Optional key prefix

    Example:
        @router.post("/matches")
        @invalidate_cache(cache_type=CacheType.LIVE_MATCHES)
        async def create_match(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            if key_pattern:
                await cache_manager.delete_pattern(
                    cache_type=cache_type,
                    pattern=key_pattern,
                )
            else:
                await cache_manager.clear(cache_type=cache_type)

            logger.info(f"Cache invalidated for {cache_type.value} after {func.__name__}")
            return result

        return wrapper
    return decorator

