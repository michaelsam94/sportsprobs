# API Proxy Layer - Example Usage

## Quick Start

The API proxy layer is now integrated into your FastAPI backend. Here's how to use it:

## Example Endpoints

### 1. Get Players from External API

```bash
# Basic request
curl "http://localhost:8000/api/v1/proxy/players?sport=nfl"

# With filters
curl "http://localhost:8000/api/v1/proxy/players?sport=nfl&team=DAL&season=2023"

# Disable cache (force fresh data)
curl "http://localhost:8000/api/v1/proxy/players?sport=nfl&use_cache=false"

# Custom cache TTL (10 minutes)
curl "http://localhost:8000/api/v1/proxy/players?sport=nfl&cache_ttl=600"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "12345",
      "name": "John Doe",
      "first_name": "John",
      "last_name": "Doe",
      "position": "QB",
      "team": "DAL",
      "jersey_number": 4,
      "height": 75,
      "weight": 220,
      "date_of_birth": "1990-01-15",
      "nationality": "USA"
    }
  ],
  "count": 1,
  "source": "external_api"
}
```

### 2. Get Teams from External API

```bash
curl "http://localhost:8000/api/v1/proxy/teams?sport=nba&season=2023"
```

### 3. Get Schedules/Matches from External API

```bash
curl "http://localhost:8000/api/v1/proxy/schedules?sport=nfl&season=2023&week=1"
```

### 4. Clear Cache

```bash
curl -X DELETE "http://localhost:8000/api/v1/proxy/cache"
```

## Features Demonstrated

### ✅ Hide Third-Party API Keys
- API keys are stored in `.env` file
- Never exposed in API responses
- Server-side only access

### ✅ Normalize Responses
- Converts different API formats to consistent structure
- Handles field name variations (e.g., `PlayerID` vs `id`)
- Standardized response format

### ✅ Cache Responses
- Automatic caching of responses
- Configurable TTL per request
- Redis support (if available)
- In-memory fallback

### ✅ Handle API Rate Limits
- Automatic rate limit tracking
- Respects external API limits
- Handles 429 responses gracefully
- Exponential backoff retry

### ✅ Retry and Fallback Logic
- Automatic retries on failures
- Falls back to cached data on errors
- Connection error handling
- Configurable retry attempts

## Configuration

Add to your `.env` file:

```env
# External API Configuration
SPORTS_DATA_API_KEY=your-actual-api-key-here
SPORTS_DATA_API_URL=https://api.sportsdata.io/v3

# Cache Configuration (optional - uses in-memory if not set)
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300

# Proxy Settings
PROXY_RETRY_MAX_ATTEMPTS=3
PROXY_RETRY_DELAY=1.0
```

## Architecture Flow

```
Client Request
    ↓
FastAPI Router (/api/v1/proxy/*)
    ↓
Proxy Service (orchestration)
    ↓
Cache Check → Cache Hit? Return cached data
    ↓ (cache miss)
API Client (with rate limiting & retries)
    ↓
External API
    ↓
Normalize Response
    ↓
Cache Response
    ↓
Return to Client
```

## Error Handling

The proxy handles various error scenarios:

1. **Rate Limit (429)**: Automatically retries with backoff
2. **Server Errors (5xx)**: Retries up to max_retries
3. **Client Errors (4xx)**: Returns error immediately
4. **Connection Errors**: Retries with exponential backoff
5. **API Failures**: Falls back to cached data if available

## Testing

Test the proxy endpoints using the interactive API docs:

1. Start the server: `uvicorn app.main:app --reload`
2. Visit: `http://localhost:8000/docs`
3. Navigate to the "proxy" tag
4. Try the endpoints with different parameters

## Next Steps

1. **Add Authentication**: Protect proxy endpoints with API keys or JWT
2. **Add More Providers**: Extend to support multiple external APIs
3. **Add Metrics**: Track cache hit rates, API call counts
4. **Add Webhooks**: Notify on cache invalidation
5. **Add Circuit Breaker**: Prevent cascading failures

