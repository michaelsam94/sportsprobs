# API Proxy Layer Documentation

## Overview

The API proxy layer provides a secure, cached, and resilient interface to external third-party APIs. It hides API keys, normalizes responses, implements caching, handles rate limits, and provides retry/fallback logic.

## Architecture

```
Client Request
    ↓
FastAPI Router (proxy.py)
    ↓
Proxy Service (proxy_service.py)
    ↓
Cache Service (cache_service.py) ← Check cache first
    ↓
API Client (api_client.py)
    ↓
External API (Sports Data API)
```

## Key Features

### 1. **Hide Third-Party API Keys**
- API keys are stored in environment variables
- Keys are never exposed to clients
- Keys are injected server-side only

### 2. **Normalize Responses**
- Converts different API response formats to consistent structure
- Handles variations in field names (e.g., `PlayerID` vs `id`)
- Returns standardized format:
  ```json
  {
    "success": true,
    "data": [...],
    "count": 10,
    "source": "external_api"
  }
  ```

### 3. **Cache Responses**
- **Redis**: Primary cache (if available)
- **In-Memory**: Fallback cache (if Redis unavailable)
- Configurable TTL per endpoint
- Automatic cache key generation from endpoint + parameters

### 4. **Handle API Rate Limits**
- Tracks request times per minute
- Automatically waits when rate limit approached
- Handles 429 responses with exponential backoff
- Respects `Retry-After` headers

### 5. **Retry and Fallback Logic**
- Exponential backoff retry (1s, 2s, 4s...)
- Configurable max retries (default: 3)
- Falls back to cached data on API errors
- Handles connection errors gracefully

## Components

### 1. API Client (`app/infrastructure/external/api_client.py`)

Base HTTP client with:
- Rate limiting enforcement
- Retry logic with exponential backoff
- Error handling
- Connection pooling

**Key Methods:**
- `get(endpoint, params)` - GET request
- `post(endpoint, json_data)` - POST request
- `_check_rate_limit()` - Rate limit enforcement
- `_make_request()` - Request with retry logic

### 2. Sports Data Client (`app/infrastructure/external/sports_data_client.py`)

Specialized client for Sports Data API:
- `get_players(sport, team, season)`
- `get_teams(sport, season)`
- `get_schedules(sport, season, week)`
- `get_player_stats(sport, player_id, season)`

### 3. Cache Service (`app/infrastructure/cache/cache_service.py`)

Caching layer:
- Redis support (primary)
- In-memory fallback
- Automatic key generation
- TTL management

**Key Methods:**
- `get(endpoint, params)` - Get cached data
- `set(endpoint, data, params, ttl)` - Cache data
- `delete(endpoint, params)` - Invalidate cache
- `clear()` - Clear all cache

### 4. Proxy Service (`app/application/services/proxy_service.py`)

Orchestration layer:
- Combines API client + cache
- Normalizes responses
- Implements fallback logic
- Error handling

**Key Methods:**
- `get_players(sport, team, season, use_cache, cache_ttl)`
- `get_teams(sport, season, use_cache, cache_ttl)`
- `get_schedules(sport, season, week, use_cache, cache_ttl)`
- `_normalize_*_response()` - Response normalization

### 5. Proxy Router (`app/api/v1/endpoints/proxy.py`)

FastAPI endpoints:
- `GET /api/v1/proxy/players`
- `GET /api/v1/proxy/teams`
- `GET /api/v1/proxy/schedules`
- `DELETE /api/v1/proxy/cache`

## Usage Examples

### Get Players

```bash
# Basic request
GET /api/v1/proxy/players?sport=nfl

# With filters
GET /api/v1/proxy/players?sport=nfl&team=DAL&season=2023

# Disable cache
GET /api/v1/proxy/players?sport=nfl&use_cache=false

# Custom cache TTL (in seconds)
GET /api/v1/proxy/players?sport=nfl&cache_ttl=600
```

### Get Teams

```bash
GET /api/v1/proxy/teams?sport=nba&season=2023
```

### Get Schedules

```bash
GET /api/v1/proxy/schedules?sport=nfl&season=2023&week=1
```

### Clear Cache

```bash
DELETE /api/v1/proxy/cache
```

## Response Format

All proxy endpoints return a normalized format:

```json
{
  "success": true,
  "data": [
    {
      "id": "12345",
      "name": "John Doe",
      "position": "QB",
      ...
    }
  ],
  "count": 1,
  "source": "external_api"
}
```

## Error Handling

### API Errors
- **429 Rate Limit**: Automatically retries with backoff
- **5xx Server Errors**: Retries up to max_retries
- **4xx Client Errors**: Returns error immediately
- **Connection Errors**: Retries with exponential backoff

### Fallback Behavior
- On API error, attempts to return cached data
- Logs warning when serving stale cache
- Returns 502 Bad Gateway if no cache available

## Configuration

### Environment Variables

```env
# External API
SPORTS_DATA_API_KEY=your-api-key-here
SPORTS_DATA_API_URL=https://api.sportsdata.io/v3

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300

# Proxy Settings
PROXY_RETRY_MAX_ATTEMPTS=3
PROXY_RETRY_DELAY=1.0
```

### Cache TTL Defaults
- Players: 5 minutes (300s)
- Teams: 10 minutes (600s)
- Schedules: 5 minutes (300s)

## Rate Limiting

The proxy layer implements two levels of rate limiting:

1. **Client Rate Limiting** (FastAPI level)
   - Per IP address
   - Configurable via `RATE_LIMIT_PER_MINUTE`

2. **API Rate Limiting** (API Client level)
   - Tracks requests to external API
   - Automatically throttles to stay within limits
   - Handles 429 responses gracefully

## Security Features

1. **API Key Protection**
   - Keys stored in environment variables
   - Never exposed in responses
   - Server-side only

2. **Input Validation**
   - Query parameter validation
   - Type checking
   - Range validation (e.g., cache_ttl)

3. **Error Message Sanitization**
   - Doesn't expose internal API details
   - Generic error messages to clients

## Performance Optimizations

1. **Caching**
   - Reduces external API calls
   - Faster response times
   - Lower API costs

2. **Connection Pooling**
   - Reuses HTTP connections
   - Reduces connection overhead

3. **Async Operations**
   - Non-blocking I/O
   - Better concurrency

## Monitoring & Logging

The proxy layer logs:
- Cache hits/misses
- API errors
- Rate limit events
- Retry attempts
- Fallback to cache

## Future Enhancements

- [ ] Circuit breaker pattern
- [ ] Request queuing for rate limits
- [ ] Cache warming strategies
- [ ] Multiple API provider fallback
- [ ] Response compression
- [ ] Request/response logging
- [ ] Metrics and analytics

