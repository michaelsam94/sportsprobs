# Example Observability Logs

## Structured Logging Examples

### 1. Request Start Log

```json
{
  "timestamp": "2024-01-01T12:00:00.123456",
  "level": "INFO",
  "logger": "app.core.observability_middleware",
  "module": "observability_middleware",
  "function": "dispatch",
  "line": 45,
  "message": "Request started: GET /api/v1/players",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "endpoint": "/api/v1/players",
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1",
  "query_params": {
    "skip": "0",
    "limit": "10"
  }
}
```

### 2. Successful Request Completion

```json
{
  "timestamp": "2024-01-01T12:00:00.168789",
  "level": "INFO",
  "logger": "app.core.observability_middleware",
  "module": "observability_middleware",
  "function": "dispatch",
  "line": 78,
  "message": "Request completed: GET /api/v1/players - 200",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "endpoint": "/api/v1/players",
  "status_code": 200,
  "response_time_ms": 45.33,
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1"
}
```

### 3. Error Log

```json
{
  "timestamp": "2024-01-01T12:00:00.200000",
  "level": "ERROR",
  "logger": "app.core.observability_middleware",
  "module": "observability_middleware",
  "function": "dispatch",
  "line": 95,
  "message": "Request failed: POST /api/v1/players",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "endpoint": "/api/v1/players",
  "error_type": "ValueError",
  "error_message": "Player name is required",
  "response_time_ms": 12.5,
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1",
  "exception": "Traceback (most recent call last):\n  File \"app/api/v1/endpoints/players.py\", line 45, in create_player\n    raise ValueError(\"Player name is required\")\nValueError: Player name is required"
}
```

### 4. Server Error (5xx)

```json
{
  "timestamp": "2024-01-01T12:00:00.250000",
  "level": "ERROR",
  "logger": "app.core.observability_middleware",
  "module": "observability_middleware",
  "function": "dispatch",
  "line": 85,
  "message": "Server error: GET /api/v1/teams - 500",
  "request_id": "660e8400-e29b-41d4-a716-446655440001",
  "method": "GET",
  "endpoint": "/api/v1/teams",
  "status_code": 500,
  "response_time_ms": 120.5,
  "client_id": "web-app-prod",
  "ip_address": "192.168.1.2"
}
```

### 5. Application Log with Context

```json
{
  "timestamp": "2024-01-01T12:00:00.300000",
  "level": "INFO",
  "logger": "app.application.services.player_service",
  "module": "player_service",
  "function": "create_player",
  "line": 25,
  "message": "Creating new player: John Doe",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_name": "John Doe",
  "team_id": 1
}
```

### 6. Warning Log

```json
{
  "timestamp": "2024-01-01T12:00:00.350000",
  "level": "WARNING",
  "logger": "app.infrastructure.cache.cache_service",
  "module": "cache_service",
  "function": "get",
  "line": 58,
  "message": "Cache miss for key: players:league:1",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "cache_key": "players:league:1"
}
```

## Metrics Examples

### Endpoint Statistics

```json
{
  "GET:/api/v1/players": {
    "endpoint": "/api/v1/players",
    "method": "GET",
    "total_requests": 1250,
    "successful_requests": 1200,
    "failed_requests": 50,
    "response_time_ms": {
      "min": 12.5,
      "max": 450.0,
      "avg": 45.23,
      "p50": 42.1,
      "p95": 120.5,
      "p99": 200.3
    },
    "last_request_at": "2024-01-01T12:00:00"
  }
}
```

### Summary Statistics

```json
{
  "summary": {
    "total_requests": 5000,
    "total_endpoints": 15,
    "avg_response_time_ms": 52.45,
    "status_code_distribution": {
      "2xx": 4500,
      "4xx": 400,
      "5xx": 100
    },
    "endpoints_tracked": 15
  }
}
```

## Error Tracking Examples

### Error Record

```json
{
  "error_type": "NotFoundError",
  "error_message": "Player not found with id: 999",
  "endpoint": "/api/v1/players/999",
  "method": "GET",
  "status_code": 404,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1",
  "timestamp": "2024-01-01T12:00:00",
  "context": {
    "query_params": {},
    "path_params": {
      "player_id": "999"
    }
  }
}
```

### Error Summary

```json
{
  "total_errors": 150,
  "error_types": {
    "NotFoundError": 80,
    "ValueError": 40,
    "APIError": 30
  },
  "errors_by_endpoint": {
    "/api/v1/players": 100,
    "/api/v1/teams": 30,
    "/api/v1/matches": 20
  },
  "errors_by_status_code": {
    "404": 80,
    "400": 40,
    "500": 30
  }
}
```

## Request Tracing

### Request Flow

```
Request: GET /api/v1/players?skip=0&limit=10
Request-ID: 550e8400-e29b-41d4-a716-446655440000

1. ObservabilityMiddleware: Request started
   → Log: "Request started: GET /api/v1/players"
   → Generate request_id
   → Start timer

2. SecurityMiddleware: API key validation
   → Log: "API key validated for client: mobile-app-prod"

3. Endpoint Handler: Process request
   → Log: "Fetching players from database"
   → Log: "Returning 10 players"

4. ObservabilityMiddleware: Request completed
   → Log: "Request completed: GET /api/v1/players - 200"
   → Record metrics
   → Add X-Request-ID header
   → Add X-Response-Time-MS header
```

### Response Headers

```
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time-MS: 45.33
```

## Log Aggregation

### ELK Stack Example

Logs are automatically in JSON format, ready for Elasticsearch:

```bash
# Index logs in Elasticsearch
curl -X POST "localhost:9200/sports-api-logs/_doc" \
  -H "Content-Type: application/json" \
  -d @log_entry.json
```

### Grafana Loki Example

Loki can parse JSON logs directly:

```yaml
# Loki configuration
clients:
  - url: http://loki:3100/loki/api/v1/push
    labels:
      job: sports-api
```

### CloudWatch Logs

AWS CloudWatch automatically parses JSON logs:

```json
{
  "timestamp": "2024-01-01T12:00:00.123456",
  "level": "INFO",
  "message": "Request started",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Performance Monitoring

### Slow Request Detection

Logs automatically include response times:

```json
{
  "level": "WARNING",
  "message": "Slow request detected",
  "endpoint": "/api/v1/matches",
  "response_time_ms": 1250.5,
  "threshold_ms": 1000.0
}
```

### High Error Rate Detection

Error tracking aggregates errors:

```json
{
  "level": "ERROR",
  "message": "High error rate detected",
  "endpoint": "/api/v1/players",
  "error_rate": 0.15,
  "threshold": 0.10,
  "errors_last_hour": 150,
  "requests_last_hour": 1000
}
```

