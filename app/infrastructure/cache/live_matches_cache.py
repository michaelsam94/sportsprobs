"""Specialized cache for live matches."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.infrastructure.cache.cache_manager import cache_manager, CacheType

logger = logging.getLogger(__name__)


class LiveMatchesCache:
    """Cache manager for live matches with automatic refresh."""

    CACHE_KEY = "live_matches"
    DEFAULT_TTL = 60  # 1 minute

    @staticmethod
    async def get_live_matches(
        league_id: Optional[int] = None,
        sport: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached live matches.

        Args:
            league_id: Optional league ID filter
            sport: Optional sport filter

        Returns:
            List of live matches or None if not cached
        """
        cache_key = LiveMatchesCache.CACHE_KEY
        if league_id:
            cache_key = f"{cache_key}:league:{league_id}"
        elif sport:
            cache_key = f"{cache_key}:sport:{sport}"

        cached = await cache_manager.get(
            cache_type=CacheType.LIVE_MATCHES,
            key=cache_key,
        )

        if cached:
            logger.debug(f"Live matches cache hit: {cache_key}")
            return cached

        logger.debug(f"Live matches cache miss: {cache_key}")
        return None

    @staticmethod
    async def set_live_matches(
        matches: List[Dict[str, Any]],
        league_id: Optional[int] = None,
        sport: Optional[str] = None,
        ttl: int = DEFAULT_TTL,
    ):
        """Cache live matches.

        Args:
            matches: List of match dictionaries
            league_id: Optional league ID filter
            sport: Optional sport filter
            ttl: Time to live in seconds
        """
        cache_key = LiveMatchesCache.CACHE_KEY
        if league_id:
            cache_key = f"{cache_key}:league:{league_id}"
        elif sport:
            cache_key = f"{cache_key}:sport:{sport}"

        await cache_manager.set(
            cache_type=CacheType.LIVE_MATCHES,
            key=cache_key,
            value=matches,
            ttl=ttl,
        )

        logger.info(f"Live matches cached: {cache_key} ({len(matches)} matches)")

    @staticmethod
    async def invalidate_live_matches(
        league_id: Optional[int] = None,
        sport: Optional[str] = None,
    ):
        """Invalidate live matches cache.

        Args:
            league_id: Optional league ID filter
            sport: Optional sport filter
        """
        if league_id:
            cache_key = f"{LiveMatchesCache.CACHE_KEY}:league:{league_id}"
            await cache_manager.delete(
                cache_type=CacheType.LIVE_MATCHES,
                key=cache_key,
            )
        elif sport:
            cache_key = f"{LiveMatchesCache.CACHE_KEY}:sport:{sport}"
            await cache_manager.delete(
                cache_type=CacheType.LIVE_MATCHES,
                key=cache_key,
            )
        else:
            await cache_manager.delete_pattern(
                cache_type=CacheType.LIVE_MATCHES,
                pattern=f"{LiveMatchesCache.CACHE_KEY}*",
            )

        logger.info(f"Live matches cache invalidated: league_id={league_id}, sport={sport}")

    @staticmethod
    async def update_match_status(
        match_id: int,
        status: str,
        scores: Optional[Dict[str, int]] = None,
    ):
        """Update a specific match in live matches cache.

        Args:
            match_id: Match ID to update
            status: New status
            scores: Optional scores dictionary
        """
        # Get all cached live matches
        cached_matches = await LiveMatchesCache.get_live_matches()

        if cached_matches:
            # Find and update the match
            for match in cached_matches:
                if match.get("id") == match_id:
                    match["status"] = status
                    if scores:
                        match.update(scores)
                    match["updated_at"] = datetime.utcnow().isoformat()

                    # Re-cache with updated data
                    await LiveMatchesCache.set_live_matches(cached_matches)
                    logger.info(f"Updated match {match_id} in live matches cache")
                    break

