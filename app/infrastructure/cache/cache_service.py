"""Cache service for API responses."""

import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, using in-memory cache")

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Cache service for storing API responses."""

    def __init__(self):
        """Initialize cache service."""
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.use_redis = REDIS_AVAILABLE and settings.REDIS_URL

    async def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if not self.use_redis:
            return None

        if self.redis_client is None:
            try:
                self.redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.use_redis = False
                return None

        return self.redis_client

    def _generate_key(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key from endpoint and parameters."""
        key_data = {"endpoint": endpoint}
        if params:
            key_data["params"] = sorted(params.items())

        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"api_cache:{key_hash}"

    async def get(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached response.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_key(endpoint, params)

        if self.use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    cached_data = await redis_client.get(cache_key)
                    if cached_data:
                        return json.loads(cached_data)
                except Exception as e:
                    logger.error(f"Redis get error: {e}")
        else:
            # In-memory cache
            if cache_key in self.memory_cache:
                cached_item = self.memory_cache[cache_key]
                # Check expiration
                if datetime.utcnow() < cached_item["expires_at"]:
                    return cached_item["data"]
                else:
                    # Remove expired item
                    del self.memory_cache[cache_key]

        return None

    async def set(
        self,
        endpoint: str,
        data: Dict[str, Any],
        params: Dict[str, Any] = None,
        ttl_seconds: int = 300,
    ):
        """Cache response.

        Args:
            endpoint: API endpoint
            data: Response data to cache
            params: Request parameters
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        cache_key = self._generate_key(endpoint, params)
        cache_data = json.dumps(data)

        if self.use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    await redis_client.setex(cache_key, ttl_seconds, cache_data)
                except Exception as e:
                    logger.error(f"Redis set error: {e}")
        else:
            # In-memory cache
            self.memory_cache[cache_key] = {
                "data": data,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
            }

            # Clean up old entries if cache gets too large
            if len(self.memory_cache) > 1000:
                now = datetime.utcnow()
                expired_keys = [
                    k for k, v in self.memory_cache.items()
                    if v["expires_at"] < now
                ]
                for key in expired_keys:
                    del self.memory_cache[key]

    async def delete(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
    ):
        """Delete cached response.

        Args:
            endpoint: API endpoint
            params: Request parameters
        """
        cache_key = self._generate_key(endpoint, params)

        if self.use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    await redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
        else:
            # In-memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]

    async def clear(self):
        """Clear all cached responses."""
        if self.use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    keys = await redis_client.keys("api_cache:*")
                    if keys:
                        await redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis clear error: {e}")
        else:
            # In-memory cache
            self.memory_cache.clear()

    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


# Global cache service instance
cache_service = CacheService()

