"""Advanced cache manager with TTL control and multiple cache types."""

import json
import hashlib
import logging
from typing import Optional, Any, Dict, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

from app.infrastructure.cache.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Cache type enumeration."""
    LIVE_MATCHES = "live_matches"
    HISTORICAL_DATA = "historical_data"
    API_RESPONSE = "api_response"
    GENERAL = "general"


class CacheManager:
    """Advanced cache manager with TTL control."""

    # Default TTL values (in seconds)
    DEFAULT_TTL = {
        CacheType.LIVE_MATCHES: 60,  # 1 minute for live data
        CacheType.HISTORICAL_DATA: 3600,  # 1 hour for historical data
        CacheType.API_RESPONSE: 300,  # 5 minutes for API responses
        CacheType.GENERAL: 300,  # 5 minutes default
    }

    def __init__(self):
        """Initialize cache manager."""
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(
        self,
        cache_type: CacheType,
        key: str,
        prefix: Optional[str] = None,
    ) -> str:
        """Generate cache key with type prefix."""
        parts = [cache_type.value]
        if prefix:
            parts.append(prefix)
        parts.append(key)
        return ":".join(parts)

    async def get(
        self,
        cache_type: CacheType,
        key: str,
        prefix: Optional[str] = None,
    ) -> Optional[Any]:
        """Get cached value.

        Args:
            cache_type: Type of cache
            key: Cache key
            prefix: Optional key prefix

        Returns:
            Cached value or None
        """
        cache_key = self._generate_key(cache_type, key, prefix)

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                cached_data = await client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # Fallback to memory cache
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if datetime.utcnow() < cached_item["expires_at"]:
                return cached_item["data"]
            else:
                del self.memory_cache[cache_key]

        return None

    async def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: Optional[str] = None,
    ):
        """Set cached value.

        Args:
            cache_type: Type of cache
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            prefix: Optional key prefix
        """
        cache_key = self._generate_key(cache_type, key, prefix)
        
        if ttl is None:
            ttl = self.DEFAULT_TTL.get(cache_type, self.DEFAULT_TTL[CacheType.GENERAL])

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                cache_data = json.dumps(value, default=str)
                await client.setex(cache_key, ttl, cache_data)
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # Fallback to memory cache
        self.memory_cache[cache_key] = {
            "data": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl),
        }

        # Clean up old entries
        if len(self.memory_cache) > 1000:
            now = datetime.utcnow()
            expired_keys = [
                k for k, v in self.memory_cache.items()
                if v["expires_at"] < now
            ]
            for key_to_delete in expired_keys:
                del self.memory_cache[key_to_delete]

    async def delete(
        self,
        cache_type: CacheType,
        key: str,
        prefix: Optional[str] = None,
    ):
        """Delete cached value.

        Args:
            cache_type: Type of cache
            key: Cache key
            prefix: Optional key prefix
        """
        cache_key = self._generate_key(cache_type, key, prefix)

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                await client.delete(cache_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        # Remove from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

    async def delete_pattern(
        self,
        cache_type: CacheType,
        pattern: str,
    ):
        """Delete all keys matching pattern.

        Args:
            cache_type: Type of cache
            pattern: Pattern to match (e.g., "league:*")
        """
        full_pattern = self._generate_key(cache_type, pattern)

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                keys = []
                async for key in client.scan_iter(match=full_pattern):
                    keys.append(key)
                if keys:
                    await client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis delete pattern error: {e}")

        # Remove from memory cache
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if k.startswith(full_pattern.replace("*", ""))
        ]
        for key in keys_to_delete:
            del self.memory_cache[key]

    async def clear(self, cache_type: Optional[CacheType] = None):
        """Clear cache.

        Args:
            cache_type: Optional cache type to clear (clears all if None)
        """
        if cache_type:
            pattern = f"{cache_type.value}:*"
        else:
            pattern = "*"

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                keys = []
                async for key in client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        # Clear memory cache
        if cache_type:
            keys_to_delete = [
                k for k in self.memory_cache.keys()
                if k.startswith(f"{cache_type.value}:")
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]
        else:
            self.memory_cache.clear()

    async def exists(
        self,
        cache_type: CacheType,
        key: str,
        prefix: Optional[str] = None,
    ) -> bool:
        """Check if key exists in cache.

        Args:
            cache_type: Type of cache
            key: Cache key
            prefix: Optional key prefix

        Returns:
            True if key exists
        """
        cache_key = self._generate_key(cache_type, key, prefix)

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                return bool(await client.exists(cache_key))
            except Exception as e:
                logger.error(f"Redis exists error: {e}")

        # Check memory cache
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if datetime.utcnow() < cached_item["expires_at"]:
                return True
            else:
                del self.memory_cache[cache_key]

        return False

    async def get_ttl(
        self,
        cache_type: CacheType,
        key: str,
        prefix: Optional[str] = None,
    ) -> Optional[int]:
        """Get remaining TTL for a key.

        Args:
            cache_type: Type of cache
            key: Cache key
            prefix: Optional key prefix

        Returns:
            Remaining TTL in seconds or None if key doesn't exist
        """
        cache_key = self._generate_key(cache_type, key, prefix)

        # Try Redis first
        client = await redis_client.get_client()
        if client:
            try:
                ttl = await client.ttl(cache_key)
                return ttl if ttl > 0 else None
            except Exception as e:
                logger.error(f"Redis TTL error: {e}")

        # Check memory cache
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            remaining = (cached_item["expires_at"] - datetime.utcnow()).total_seconds()
            return int(remaining) if remaining > 0 else None

        return None


# Global cache manager instance
cache_manager = CacheManager()

