# Redis Caching Implementation

## Overview

Comprehensive Redis caching implementation for FastAPI with support for:
- Live matches cache (short TTL)
- Historical data cache (long TTL)
- API response caching
- TTL control
- Decorator-based caching
- Automatic fallback to in-memory cache

## Architecture

```
FastAPI Endpoint
    ↓
Cache Decorator
    ↓
Cache Manager
    ↓
Redis Client (with connection pooling)
    ↓
Redis Server
    ↓
Fallback: In-Memory Cache
```

## Components

### 1. Redis Client (`redis_client.py`)

- Connection pooling (max 50 connections)
- Health checks
- Automatic reconnection
- Graceful fallback to memory cache

### 2. Cache Manager (`cache_manager.py`)

- Unified interface for all cache types
- TTL management
- Pattern-based deletion
- Memory cache fallback

### 3. Cache Decorators (`decorators.py`)

- `@cache_response` - General purpose caching
- `@cache_live_matches` - Live matches (60s TTL)
- `@cache_historical_data` - Historical data (3600s TTL)
- `@invalidate_cache` - Cache invalidation

### 4. Specialized Caches

- **LiveMatchesCache** - Live matches with auto-refresh
- **HistoricalDataCache** - Standings, team stats, etc.

## Usage Examples

### 1. Decorator-Based Caching

```python
from app.infrastructure.cache.decorators import cache_response, CacheType

@router.get("/teams")
@cache_response(cache_type=CacheType.API_RESPONSE, ttl=300)
async def get_teams(...):
    # Response automatically cached for 5 minutes
    return teams
```

### 2. Live Matches Cache

```python
from app.infrastructure.cache.live_matches_cache import LiveMatchesCache

# Get cached live matches
matches = await LiveMatchesCache.get_live_matches(league_id=1)

# Cache live matches
await LiveMatchesCache.set_live_matches(matches, league_id=1, ttl=60)

# Invalidate when match status changes
await LiveMatchesCache.invalidate_live_matches(league_id=1)
```

### 3. Historical Data Cache

```python
from app.infrastructure.cache.historical_cache import HistoricalDataCache

# Cache league standings
await HistoricalDataCache.set_standings(
    standings=standings_data,
    league_id=1,
    season=2023,
    ttl=3600,
)

# Get cached standings
standings = await HistoricalDataCache.get_standings(
    league_id=1,
    season=2023,
)

# Invalidate when standings update
await HistoricalDataCache.invalidate_league_data(league_id=1, season=2023)
```

### 4. Manual Cache Management

```python
from app.infrastructure.cache.cache_manager import cache_manager, CacheType

# Set cache
await cache_manager.set(
    cache_type=CacheType.API_RESPONSE,
    key="my_key",
    value={"data": "value"},
    ttl=300,
)

# Get cache
cached = await cache_manager.get(
    cache_type=CacheType.API_RESPONSE,
    key="my_key",
)

# Delete cache
await cache_manager.delete(
    cache_type=CacheType.API_RESPONSE,
    key="my_key",
)

# Clear all cache of a type
await cache_manager.clear(cache_type=CacheType.API_RESPONSE)
```

## Cache Types

### 1. LIVE_MATCHES
- **Default TTL**: 60 seconds
- **Use Case**: Live match data that changes frequently
- **Example**: Current scores, match status

### 2. HISTORICAL_DATA
- **Default TTL**: 3600 seconds (1 hour)
- **Use Case**: Historical statistics, standings
- **Example**: League tables, team season stats

### 3. API_RESPONSE
- **Default TTL**: 300 seconds (5 minutes)
- **Use Case**: General API responses
- **Example**: Team lists, player lists

### 4. GENERAL
- **Default TTL**: 300 seconds (5 minutes)
- **Use Case**: General purpose caching
- **Example**: Configuration, reference data

## TTL Control

### Per Cache Type

```python
# Use default TTL for cache type
await cache_manager.set(
    cache_type=CacheType.LIVE_MATCHES,
    key="key",
    value=data,
)

# Override TTL
await cache_manager.set(
    cache_type=CacheType.LIVE_MATCHES,
    key="key",
    value=data,
    ttl=120,  # 2 minutes instead of default 60s
)
```

### In Decorators

```python
@cache_response(
    cache_type=CacheType.API_RESPONSE,
    ttl=600,  # 10 minutes
)
async def my_endpoint(...):
    ...
```

## Cache Invalidation

### Automatic Invalidation

```python
@router.post("/matches")
@invalidate_cache(cache_type=CacheType.LIVE_MATCHES)
async def create_match(...):
    # Cache automatically invalidated after function execution
    ...
```

### Manual Invalidation

```python
# Invalidate specific key
await cache_manager.delete(
    cache_type=CacheType.LIVE_MATCHES,
    key="live_matches:league:1",
)

# Invalidate pattern
await cache_manager.delete_pattern(
    cache_type=CacheType.LIVE_MATCHES,
    pattern="live_matches:league:*",
)

# Clear all of a type
await cache_manager.clear(cache_type=CacheType.LIVE_MATCHES)
```

## Integration with Endpoints

### Example: Live Matches Endpoint

```python
@router.get("/matches/live")
async def get_live_matches(...):
    from app.infrastructure.cache.live_matches_cache import LiveMatchesCache
    
    # Check cache
    cached = await LiveMatchesCache.get_live_matches(league_id=league_id)
    if cached:
        return cached
    
    # Fetch from database
    matches = await service.get_live_matches()
    
    # Cache result
    await LiveMatchesCache.set_live_matches(matches, league_id=league_id)
    
    return matches
```

### Example: Standings Endpoint

```python
@router.get("/standings")
@cache_historical_data(ttl=1800)
async def get_standings(league_id: int, season: int):
    # Response automatically cached for 30 minutes
    return await service.get_standings(league_id, season)
```

## Cache Management API

### Get Cache Stats

```bash
GET /api/v1/cache/stats
GET /api/v1/cache/stats?cache_type=live_matches
```

### Clear Cache

```bash
DELETE /api/v1/cache/clear
DELETE /api/v1/cache/clear?cache_type=live_matches
```

### Cache Health

```bash
GET /api/v1/cache/health
```

## Configuration

### Environment Variables

```env
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Cache settings
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
```

### Connection Pooling

- **Max Connections**: 50
- **Health Check Interval**: 30 seconds
- **Retry on Timeout**: Enabled
- **Decode Responses**: True (automatic JSON handling)

## Performance Considerations

### 1. Connection Pooling
- Reuses connections for better performance
- Limits connection overhead
- Handles concurrent requests efficiently

### 2. Memory Fallback
- Automatic fallback if Redis unavailable
- No service interruption
- Limited to 1000 entries to prevent memory issues

### 3. TTL Strategy
- Short TTL for live data (60s)
- Medium TTL for API responses (5min)
- Long TTL for historical data (1hr)
- Configurable per use case

### 4. Pattern-Based Operations
- Efficient key scanning
- Batch deletion
- Reduced Redis operations

## Monitoring

### Health Checks

```python
from app.infrastructure.cache.redis_client import redis_client

# Check Redis availability
is_healthy = await redis_client.health_check()
```

### Cache Statistics

- Cache hit/miss rates (via logging)
- TTL remaining (via `get_ttl()`)
- Redis connection status

## Best Practices

1. **Use Appropriate Cache Types**
   - Live matches → `LIVE_MATCHES`
   - Standings → `HISTORICAL_DATA`
   - API responses → `API_RESPONSE`

2. **Set Appropriate TTLs**
   - Live data: 30-60 seconds
   - Frequently changing: 5 minutes
   - Historical data: 1 hour+

3. **Invalidate on Updates**
   - Use `@invalidate_cache` decorator
   - Or manually invalidate after writes

4. **Monitor Cache Performance**
   - Check cache hit rates
   - Monitor Redis memory usage
   - Adjust TTLs based on usage patterns

5. **Handle Cache Misses Gracefully**
   - Always have fallback to database
   - Cache results after fetching

## Error Handling

- **Redis Unavailable**: Automatically falls back to memory cache
- **Connection Errors**: Logged and handled gracefully
- **Invalid Keys**: Returns None (cache miss)
- **Serialization Errors**: Logged and handled

## Future Enhancements

- [ ] Cache warming strategies
- [ ] Cache compression for large values
- [ ] Distributed cache invalidation
- [ ] Cache metrics and analytics
- [ ] Cache versioning
- [ ] Cache preloading

