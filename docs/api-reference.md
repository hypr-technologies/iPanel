# API Reference

iPanel provides a comprehensive REST API for programmatic access to all panel features. This document describes the available endpoints, authentication methods, and usage examples.

## Base URL

All API requests should be made to:
```
https://your-domain.com/api/v1
```

## Authentication

### API Keys

iPanel uses API keys for authentication. You can generate API keys from the web interface:

1. Go to **Settings** → **API Keys**
2. Click **Generate New Key**
3. Set permissions and expiration
4. Copy the generated key

### Using API Keys

Include the API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://your-domain.com/api/v1/sites
```

## Rate Limiting

- **Rate Limit**: 1000 requests per hour per API key
- **Burst Limit**: 100 requests per minute
- **Headers**: Rate limit information is included in response headers

## Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Responses

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid domain name",
    "details": {}
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Site Management

### List Sites

```http
GET /api/v1/sites
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Results per page (default: 20)
- `status` (optional): Filter by status (active, inactive, suspended)

**Response:**
```json
{
  "success": true,
  "data": {
    "sites": [
      {
        "id": 1,
        "domain": "example.com",
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### Create Site

```http
POST /api/v1/sites
```

**Request Body:**
```json
{
  "domain": "newsite.com",
  "php_version": "8.1",
  "ssl_enabled": true,
  "backup_enabled": true
}
```

### Get Site Details

```http
GET /api/v1/sites/{id}
```

### Update Site

```http
PUT /api/v1/sites/{id}
```

### Delete Site

```http
DELETE /api/v1/sites/{id}
```

## Database Management

### List Databases

```http
GET /api/v1/databases
```

### Create Database

```http
POST /api/v1/databases
```

**Request Body:**
```json
{
  "name": "myapp_db",
  "type": "mysql",
  "username": "dbuser",
  "password": "secure_password"
}
```

### Database Operations

```http
POST /api/v1/databases/{id}/backup
POST /api/v1/databases/{id}/restore
DELETE /api/v1/databases/{id}
```

## File Manager

### List Files

```http
GET /api/v1/files
```

**Parameters:**
- `path` (required): Directory path
- `recursive` (optional): Include subdirectories

### Upload File

```http
POST /api/v1/files/upload
```

**Request:** Multipart form data with file and path

### Download File

```http
GET /api/v1/files/download
```

**Parameters:**
- `path` (required): File path

### File Operations

```http
POST /api/v1/files/copy
POST /api/v1/files/move
DELETE /api/v1/files
```

## SSL Certificates

### List Certificates

```http
GET /api/v1/ssl
```

### Request Certificate

```http
POST /api/v1/ssl/request
```

**Request Body:**
```json
{
  "domain": "example.com",
  "email": "admin@example.com",
  "provider": "letsencrypt"
}
```

### Renew Certificate

```http
POST /api/v1/ssl/{id}/renew
```

## System Information

### Server Stats

```http
GET /api/v1/system/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu_usage": 25.5,
    "memory_usage": 45.2,
    "disk_usage": 60.1,
    "load_average": [0.5, 0.8, 1.2],
    "uptime": 86400
  }
}
```

### System Services

```http
GET /api/v1/system/services
POST /api/v1/system/services/{service}/restart
POST /api/v1/system/services/{service}/stop
POST /api/v1/system/services/{service}/start
```

## Backups

### List Backups

```http
GET /api/v1/backups
```

### Create Backup

```http
POST /api/v1/backups
```

**Request Body:**
```json
{
  "type": "full",
  "sites": [1, 2, 3],
  "databases": [1, 2],
  "compression": true
}
```

### Restore Backup

```http
POST /api/v1/backups/{id}/restore
```

## User Management

### List Users

```http
GET /api/v1/users
```

### Create User

```http
POST /api/v1/users
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "role": "user"
}
```

### Update User

```http
PUT /api/v1/users/{id}
```

### Delete User

```http
DELETE /api/v1/users/{id}
```

## Webhooks

### List Webhooks

```http
GET /api/v1/webhooks
```

### Create Webhook

```http
POST /api/v1/webhooks
```

**Request Body:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["site.created", "backup.completed"],
  "secret": "webhook_secret"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or expired |
| `INSUFFICIENT_PERMISSIONS` | API key lacks required permissions |
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

## SDK and Libraries

### Official Libraries

- **Python**: `pip install ipanel-api`
- **Node.js**: `npm install ipanel-api`
- **PHP**: `composer require hypr/ipanel-api`

### Usage Example (Python)

```python
from ipanel_api import IPanel

# Initialize client
client = IPanel(
    base_url="https://your-domain.com",
    api_key="your-api-key"
)

# List sites
sites = client.sites.list()

# Create new site
site = client.sites.create({
    "domain": "newsite.com",
    "php_version": "8.1"
})

# Get site details
site_details = client.sites.get(site.id)
```

## Testing

### Postman Collection

Download our Postman collection for API testing:
- [iPanel API Collection](https://docs.infuze.cloud/ipanel/postman-collection.json)

### OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- [OpenAPI Spec](https://docs.infuze.cloud/ipanel/openapi.json)

---

**Need Help?**
- [API Forum](https://forum.hypr.tech/c/api)
- [GitHub Issues](https://github.com/hypr-technologies/iPanel/issues)
- [Documentation](https://docs.infuze.cloud/ipanel)
