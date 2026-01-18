"""Specialized cache for historical data."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.infrastructure.cache.cache_manager import cache_manager, CacheType

logger = logging.getLogger(__name__)


class HistoricalDataCache:
    """Cache manager for historical data with longer TTL."""

    DEFAULT_TTL = 3600  # 1 hour

    @staticmethod
    def _generate_key(
        data_type: str,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
        season: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate cache key for historical data.

        Args:
            data_type: Type of historical data (standings, stats, etc.)
            league_id: Optional league ID
            team_id: Optional team ID
            season: Optional season
            **kwargs: Additional parameters

        Returns:
            Cache key string
        """
        key_parts = [data_type]
        
        if league_id:
            key_parts.append(f"league:{league_id}")
        if team_id:
            key_parts.append(f"team:{team_id}")
        if season:
            key_parts.append(f"season:{season}")
        
        # Add any additional parameters
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        
        return "_".join(str(p) for p in key_parts)

    @staticmethod
    async def get_standings(
        league_id: int,
        season: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached league standings.

        Args:
            league_id: League ID
            season: Season year

        Returns:
            List of team standings or None
        """
        cache_key = HistoricalDataCache._generate_key(
            "standings",
            league_id=league_id,
            season=season,
        )

        cached = await cache_manager.get(
            cache_type=CacheType.HISTORICAL_DATA,
            key=cache_key,
        )

        if cached:
            logger.debug(f"Standings cache hit: {cache_key}")
            return cached

        logger.debug(f"Standings cache miss: {cache_key}")
        return None

    @staticmethod
    async def set_standings(
        standings: List[Dict[str, Any]],
        league_id: int,
        season: int,
        ttl: int = DEFAULT_TTL,
    ):
        """Cache league standings.

        Args:
            standings: List of team standings
            league_id: League ID
            season: Season year
            ttl: Time to live in seconds
        """
        cache_key = HistoricalDataCache._generate_key(
            "standings",
            league_id=league_id,
            season=season,
        )

        await cache_manager.set(
            cache_type=CacheType.HISTORICAL_DATA,
            key=cache_key,
            value=standings,
            ttl=ttl,
        )

        logger.info(f"Standings cached: {cache_key} ({len(standings)} teams)")

    @staticmethod
    async def get_team_stats(
        team_id: int,
        season: int,
        period_type: str = "season",
    ) -> Optional[Dict[str, Any]]:
        """Get cached team statistics.

        Args:
            team_id: Team ID
            season: Season year
            period_type: Period type (season, month, week)

        Returns:
            Team statistics dictionary or None
        """
        cache_key = HistoricalDataCache._generate_key(
            "team_stats",
            team_id=team_id,
            season=season,
            period_type=period_type,
        )

        cached = await cache_manager.get(
            cache_type=CacheType.HISTORICAL_DATA,
            key=cache_key,
        )

        if cached:
            logger.debug(f"Team stats cache hit: {cache_key}")
            return cached

        logger.debug(f"Team stats cache miss: {cache_key}")
        return None

    @staticmethod
    async def set_team_stats(
        stats: Dict[str, Any],
        team_id: int,
        season: int,
        period_type: str = "season",
        ttl: int = DEFAULT_TTL,
    ):
        """Cache team statistics.

        Args:
            stats: Team statistics dictionary
            team_id: Team ID
            season: Season year
            period_type: Period type
            ttl: Time to live in seconds
        """
        cache_key = HistoricalDataCache._generate_key(
            "team_stats",
            team_id=team_id,
            season=season,
            period_type=period_type,
        )

        await cache_manager.set(
            cache_type=CacheType.HISTORICAL_DATA,
            key=cache_key,
            value=stats,
            ttl=ttl,
        )

        logger.info(f"Team stats cached: {cache_key}")

    @staticmethod
    async def invalidate_league_data(
        league_id: int,
        season: Optional[int] = None,
    ):
        """Invalidate all cached data for a league.

        Args:
            league_id: League ID
            season: Optional season (invalidates all seasons if None)
        """
        if season:
            pattern = f"*league:{league_id}*season:{season}*"
        else:
            pattern = f"*league:{league_id}*"

        await cache_manager.delete_pattern(
            cache_type=CacheType.HISTORICAL_DATA,
            pattern=pattern,
        )

        logger.info(f"Historical data cache invalidated: league_id={league_id}, season={season}")

    @staticmethod
    async def invalidate_team_data(
        team_id: int,
        season: Optional[int] = None,
    ):
        """Invalidate all cached data for a team.

        Args:
            team_id: Team ID
            season: Optional season (invalidates all seasons if None)
        """
        if season:
            pattern = f"*team:{team_id}*season:{season}*"
        else:
            pattern = f"*team:{team_id}*"

        await cache_manager.delete_pattern(
            cache_type=CacheType.HISTORICAL_DATA,
            pattern=pattern,
        )

        logger.info(f"Historical data cache invalidated: team_id={team_id}, season={season}")

