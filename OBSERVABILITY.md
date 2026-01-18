# Observability Implementation

## Overview

Comprehensive observability solution with structured logging, error tracking, request tracing, and performance metrics.

## Features

### 1. Structured Logging

- **JSON format** for easy parsing
- **Structured fields**: timestamp, level, logger, module, function, line
- **Request context**: request_id, client_id, ip_address, endpoint
- **Exception tracking**: Full stack traces
- **Configurable**: Log level and format

### 2. Request Tracing

- **Correlation IDs**: Unique request ID per request
- **Request ID headers**: `X-Request-ID` in responses
- **Response time headers**: `X-Response-Time-MS`
- **End-to-end tracing**: Track requests across services

### 3. Performance Metrics

- **Request metrics**: Endpoint, method, status code, response time
- **Endpoint statistics**: Total requests, success/failure counts
- **Response time percentiles**: P50, P95, P99
- **Client tracking**: Per-client metrics
- **Real-time collection**: Automatic metric collection

### 4. Error Tracking

- **Error records**: Type, message, stack trace
- **Context capture**: Endpoint, request ID, client info
- **Error aggregation**: Counts by type, endpoint, status code
- **Recent errors**: Last N errors with full context

## Logging Setup

### Configuration

Logging is automatically configured in `main.py`:

```python
setup_logging(
    level="INFO",  # or "DEBUG" in development
    json_format=True,  # JSON format for production
)
```

### Log Format

**JSON Format (Production):**
```json
{
  "timestamp": "2024-01-01T12:00:00.000000",
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
  "ip_address": "192.168.1.1"
}
```

**Plain Text Format (Development):**
```
2024-01-01 12:00:00 - app.core.observability_middleware - INFO - Request started: GET /api/v1/players
```

## Request Tracing

### Request ID

Every request gets a unique correlation ID:

```python
# Automatically added to request state
request.state.request_id = "550e8400-e29b-41d4-a716-446655440000"

# Added to response headers
response.headers["X-Request-ID"] = request_id
response.headers["X-Response-Time-MS"] = "45.23"
```

### Using Request ID in Logs

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.info(
    "Processing request",
    extra={
        "request_id": request.state.request_id,
        "custom_field": "value",
    }
)
```

## Performance Metrics

### Automatic Collection

Metrics are automatically collected for all requests:
- Endpoint path
- HTTP method
- Status code
- Response time (milliseconds)
- Client ID (if available)
- IP address

### Metrics Endpoints

**Get Metrics (Public):**
```bash
GET /api/v1/observability/metrics
GET /api/v1/observability/metrics?endpoint=/api/v1/players
GET /api/v1/observability/metrics?method=GET
```

**Response:**
```json
{
  "summary": {
    "total_requests": 1250,
    "total_endpoints": 15,
    "avg_response_time_ms": 45.23,
    "status_code_distribution": {
      "2xx": 1100,
      "4xx": 100,
      "5xx": 50
    }
  },
  "endpoints": {
    "GET:/api/v1/players": {
      "endpoint": "/api/v1/players",
      "method": "GET",
      "total_requests": 500,
      "successful_requests": 480,
      "failed_requests": 20,
      "response_time_ms": {
        "min": 12.5,
        "max": 250.0,
        "avg": 45.23,
        "p50": 42.1,
        "p95": 120.5,
        "p99": 200.3
      },
      "last_request_at": "2024-01-01T12:00:00"
    }
  }
}
```

**Get Recent Metrics (Admin):**
```bash
GET /api/v1/observability/metrics/recent?limit=100
Authorization: Bearer <admin-token>
```

## Error Tracking

### Automatic Error Capture

Errors are automatically captured with:
- Error type and message
- Stack trace
- Request context (endpoint, method, request ID)
- Client information
- Timestamp

### Error Endpoints

**Get Recent Errors (Admin):**
```bash
GET /api/v1/observability/errors?limit=100
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "recent_errors": [
    {
      "error_type": "ValueError",
      "error_message": "Invalid input",
      "endpoint": "/api/v1/players",
      "method": "POST",
      "status_code": 400,
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "mobile-app-prod",
      "ip_address": "192.168.1.1",
      "timestamp": "2024-01-01T12:00:00",
      "context": {
        "query_params": {},
        "path_params": {}
      }
    }
  ],
  "summary": {
    "total_errors": 50,
    "error_types": {
      "ValueError": 20,
      "NotFoundError": 15,
      "APIError": 15
    },
    "errors_by_endpoint": {
      "/api/v1/players": 30,
      "/api/v1/teams": 20
    },
    "errors_by_status_code": {
      "400": 20,
      "404": 15,
      "500": 15
    }
  }
}
```

**Get Error Summary (Admin):**
```bash
GET /api/v1/observability/errors/summary
Authorization: Bearer <admin-token>
```

## Example Logs

### Request Start

```json
{
  "timestamp": "2024-01-01T12:00:00.123456",
  "level": "INFO",
  "logger": "app.core.observability_middleware",
  "message": "Request started: GET /api/v1/players",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "endpoint": "/api/v1/players",
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1",
  "query_params": {"skip": "0", "limit": "10"}
}
```

### Request Completion

```json
{
  "timestamp": "2024-01-01T12:00:00.168789",
  "level": "INFO",
  "logger": "app.core.observability_middleware",
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

### Error Log

```json
{
  "timestamp": "2024-01-01T12:00:00.200000",
  "level": "ERROR",
  "logger": "app.core.observability_middleware",
  "message": "Request failed: POST /api/v1/players",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "endpoint": "/api/v1/players",
  "error_type": "ValueError",
  "error_message": "Player name is required",
  "response_time_ms": 12.5,
  "client_id": "mobile-app-prod",
  "ip_address": "192.168.1.1",
  "exception": "Traceback (most recent call last):\n  ..."
}
```

## Integration

### Using in Endpoints

```python
from app.core.logging_config import get_logger
from fastapi import Request

logger = get_logger(__name__)

@router.get("/example")
async def example_endpoint(request: Request):
    # Log with request context
    logger.info(
        "Processing example request",
        extra={
            "request_id": request.state.request_id,
            "custom_data": "value",
        }
    )
    
    # Your logic here
    return {"message": "success"}
```

### Manual Error Tracking

```python
from app.infrastructure.observability.error_tracker import error_tracker

try:
    # Your code
    pass
except Exception as e:
    await error_tracker.record_error(
        error=e,
        endpoint=request.url.path,
        method=request.method,
        request_id=request.state.request_id,
        context={"additional": "data"},
    )
    raise
```

## Monitoring Endpoints

### Health Check

```bash
GET /api/v1/observability/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "metrics": {
    "total_requests": 1250,
    "endpoints_tracked": 15
  },
  "errors": {
    "total_errors": 50,
    "error_types": 3
  }
}
```

## Configuration

### Environment Variables

```env
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json or text
LOG_FILE=logs/app.log  # Optional log file
```

### Metrics Limits

- **Max metrics in memory**: 10,000 (configurable)
- **Max response times per endpoint**: 1,000 (for percentiles)
- **Max errors in memory**: 1,000 (configurable)

## Best Practices

1. **Use structured logging**
   - Always include request_id in logs
   - Add relevant context to log extra fields
   - Use appropriate log levels

2. **Monitor metrics**
   - Check response time percentiles
   - Monitor error rates
   - Track endpoint usage

3. **Error handling**
   - Let middleware capture errors automatically
   - Add context when manually tracking errors
   - Review error summaries regularly

4. **Performance**
   - Monitor P95 and P99 response times
   - Identify slow endpoints
   - Optimize based on metrics

## Log Aggregation

### JSON Logs for Log Aggregation Tools

The JSON format is compatible with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (Grafana)
- **CloudWatch Logs** (AWS)
- **Datadog**
- **Splunk**

### Example Logstash Configuration

```ruby
input {
  file {
    path => "/var/log/app/app.log"
    codec => "json"
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "sports-api-%{+YYYY.MM.dd}"
  }
}
```

## Future Enhancements

- [ ] Distributed tracing (OpenTelemetry)
- [ ] APM integration (New Relic, Datadog)
- [ ] Custom metrics (business metrics)
- [ ] Alerting based on metrics
- [ ] Log retention policies
- [ ] Metrics export (Prometheus format)
- [ ] Real-time dashboards

