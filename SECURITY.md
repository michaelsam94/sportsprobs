# Backend Security Implementation

## Overview

Comprehensive security implementation with API key authentication, per-client rate limiting, IP throttling, and abuse prevention.

## Features

### 1. API Key Authentication

- Secure API key generation
- Hashed storage (SHA-256)
- Key expiration support
- Per-key rate limits
- Key revocation

### 2. Per-Client Rate Limiting

- Individual rate limits per API key
- Per-minute and per-hour limits
- Redis-backed (with memory fallback)
- Automatic tracking

### 3. IP Throttling

- Per-IP request tracking
- Automatic blocking of abusive IPs
- Configurable thresholds
- Temporary blocks with auto-expiry

### 4. Abuse Prevention

- Suspicious activity detection
- Automatic IP blocking
- Request pattern analysis
- Configurable block duration

## API Key Management

### Create API Key (Admin)

```bash
POST /api/v1/admin/api-keys
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "Mobile App Production",
  "client_id": "mobile-app-prod",
  "rate_limit_per_minute": 100,
  "rate_limit_per_hour": 5000,
  "expires_days": 365
}
```

**Response:**
```json
{
  "api_key": "sk_abc123...",
  "key_info": {
    "key_id": "xyz789",
    "name": "Mobile App Production",
    "client_id": "mobile-app-prod",
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 5000,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "expires_at": "2025-01-01T00:00:00"
  }
}
```

⚠️ **Important**: The plain API key is only shown once. Store it securely!

### List API Keys (Admin)

```bash
GET /api/v1/admin/api-keys
Authorization: Bearer <admin-token>

# Filter by client
GET /api/v1/admin/api-keys?client_id=mobile-app-prod
```

### Revoke API Key (Admin)

```bash
DELETE /api/v1/admin/api-keys/{key_id}
Authorization: Bearer <admin-token>
```

## Using API Keys

### Authentication Methods

**Method 1: Authorization Header**
```bash
curl -H "Authorization: ApiKey sk_abc123..." \
     http://localhost:8000/api/v1/protected
```

**Method 2: X-API-Key Header**
```bash
curl -H "X-API-Key: sk_abc123..." \
     http://localhost:8000/api/v1/protected
```

**Method 3: Bearer Token (also supported)**
```bash
curl -H "Authorization: Bearer sk_abc123..." \
     http://localhost:8000/api/v1/protected
```

## Protected Endpoints

### Example Protected Endpoint

```bash
GET /api/v1/example/protected
Authorization: ApiKey <your-api-key>
```

**Response:**
```json
{
  "message": "This is a protected endpoint. Your API key is valid!",
  "client_id": "mobile-app-prod",
  "api_key_name": "Mobile App Production",
  "rate_limit_per_minute": 100,
  "rate_limit_per_hour": 5000
}
```

## IP Management (Admin)

### Get IP Status

```bash
GET /api/v1/admin/ip-status/{ip_address}
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "ip_address": "192.168.1.1",
  "is_blocked": false,
  "requests_last_hour": 45,
  "requests_last_minute": 2,
  "suspicious_count": 0
}
```

### Unblock IP

```bash
POST /api/v1/admin/ip-unblock/{ip_address}
Authorization: Bearer <admin-token>
```

### List Blocked IPs

```bash
GET /api/v1/admin/blocked-ips
Authorization: Bearer <admin-token>
```

## Security Middleware

The security middleware automatically:

1. **Extracts API key** from request headers
2. **Validates API key** against stored keys
3. **Checks IP throttling** limits
4. **Enforces per-client rate limits**
5. **Tracks suspicious activity**
6. **Blocks abusive IPs**

### Excluded Paths

The following paths are excluded from API key requirements:
- `/` - Root endpoint
- `/health` - Health check
- `/docs` - Swagger UI
- `/openapi.json` - OpenAPI schema
- `/redoc` - ReDoc documentation

## Rate Limiting

### Per-Client Limits

Each API key has individual rate limits:
- `rate_limit_per_minute`: Requests per minute
- `rate_limit_per_hour`: Requests per hour

### IP-Based Limits

Global IP limits (applied to all requests):
- 100 requests per minute
- 1000 requests per hour

### Abuse Prevention

IPs are automatically blocked after:
- 5 suspicious activities
- Block duration: 60 minutes (configurable)

## Error Responses

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "API key required"
}
```

### 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "message": "Client rate limit exceeded",
  "retry_after": 60
}
```

## Configuration

### Environment Variables

```env
# Admin token for security endpoints
ADMIN_TOKEN=your-admin-token-here

# Debug mode (disables API key requirement)
DEBUG=False
```

### Development Mode

When `DEBUG=True`, API key authentication is optional. This allows:
- Testing without API keys
- Development convenience
- Swagger UI access

**⚠️ Never use DEBUG=True in production!**

## Security Best Practices

1. **Store API keys securely**
   - Never commit keys to version control
   - Use environment variables or secret management
   - Rotate keys regularly

2. **Use appropriate rate limits**
   - Set limits based on client needs
   - Monitor usage patterns
   - Adjust as needed

3. **Monitor suspicious activity**
   - Check IP status regularly
   - Review blocked IPs
   - Investigate abuse patterns

4. **Key expiration**
   - Set expiration dates for keys
   - Rotate keys before expiration
   - Revoke compromised keys immediately

5. **IP management**
   - Review blocked IPs
   - Unblock legitimate IPs
   - Monitor for false positives

## Implementation Details

### API Key Storage

- Keys are hashed using SHA-256
- Plain keys are never stored
- Keys are stored in `config/api_keys.json`

### Rate Limiting

- Primary: Redis (if available)
- Fallback: In-memory tracking
- Per-client and per-IP tracking

### IP Throttling

- In-memory tracking
- Automatic cleanup of old data
- Configurable thresholds

## Example Usage

### Python Client

```python
import requests

api_key = "sk_abc123..."
headers = {"Authorization": f"ApiKey {api_key}"}

response = requests.get(
    "http://localhost:8000/api/v1/example/protected",
    headers=headers
)

print(response.json())
```

### JavaScript/TypeScript Client

```typescript
const apiKey = "sk_abc123...";

const response = await fetch(
  "http://localhost:8000/api/v1/example/protected",
  {
    headers: {
      "Authorization": `ApiKey ${apiKey}`,
    },
  }
);

const data = await response.json();
console.log(data);
```

## Monitoring

### Key Metrics

- API key usage per client
- Rate limit hits
- Blocked IPs
- Suspicious activity patterns

### Logging

All security events are logged:
- Invalid API key attempts
- Rate limit violations
- IP blocking events
- Key usage

## Future Enhancements

- [ ] JWT token support
- [ ] OAuth 2.0 integration
- [ ] Webhook notifications for security events
- [ ] Advanced analytics dashboard
- [ ] Machine learning for abuse detection
- [ ] Geographic IP filtering
- [ ] DDoS protection integration

