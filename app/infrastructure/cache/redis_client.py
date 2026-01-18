"""Redis client setup and connection management."""

import logging
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client singleton with connection pooling."""

    _instance: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None

    @classmethod
    async def get_client(cls) -> Optional[Redis]:
        """Get or create Redis client instance."""
        if cls._instance is None:
            try:
                # Create connection pool
                cls._pool = ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=50,
                    decode_responses=True,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                
                # Create Redis client from pool
                cls._instance = Redis(connection_pool=cls._pool)
                
                # Test connection
                await cls._instance.ping()
                logger.info("Redis connection established successfully")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Falling back to in-memory cache")
                cls._instance = None
                cls._pool = None

        return cls._instance

    @classmethod
    async def close(cls):
        """Close Redis connection and pool."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
        
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None
        logger.info("Redis connection closed")

    @classmethod
    async def health_check(cls) -> bool:
        """Check if Redis is available."""
        try:
            client = await cls.get_client()
            if client:
                await client.ping()
                return True
        except Exception:
            pass
        return False


# Global Redis client instance
redis_client = RedisClient()

