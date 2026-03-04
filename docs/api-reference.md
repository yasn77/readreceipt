# API Reference

Complete API documentation for the Read Receipt system.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Public Endpoints](#public-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)

## Overview

The Read Receipt API is a RESTful HTTP API that provides access to all system functionality.

**Base URL:**
- Development: `http://localhost:5000`
- Production: `https://readreceipt.yourdomain.com`

**API Version:** v1 (current)

**Response Format:** JSON

**Character Encoding:** UTF-8

### API Conventions

- All endpoints return JSON responses
- Successful responses include appropriate HTTP status codes
- Error responses include an `error` field with a descriptive message
- Timestamps are in ISO 8601 format
- All endpoints are case-sensitive

### Request/Response Example

**Request:**
```http
GET /api/admin/recipients HTTP/1.1
Host: localhost:5000
Authorization: Bearer your-admin-token
Content-Type: application/json
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245

[
  {
    "id": 1,
    "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "description": "John Doe",
    "email": "john@example.com"
  }
]
```

## Authentication

### Token Authentication

Admin and analytics endpoints require authentication using a bearer token.

**Obtaining a Token:**

The admin token is set via the `ADMIN_TOKEN` environment variable.

```bash
export ADMIN_TOKEN=your-secure-token
```

**Using the Token:**

Include the token in the `Authorization` header:

```http
Authorization: Bearer your-admin-token
```

### Authentication Endpoint

#### Login

Authenticate with the admin token.

**Endpoint:**
```http
POST /api/admin/login
```

**Request:**
```json
{
  "token": "your-admin-token"
}
```

**Response (200 OK):**
```json
{
  "status": "authenticated"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid token"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"token": "your-admin-token"}'
```

**JavaScript Example:**
```javascript
const response = await fetch('/api/admin/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ token: 'your-admin-token' })
});

const data = await response.json();
if (response.ok) {
  localStorage.setItem('adminToken', data.token);
}
```

**Python Example:**
```python
import requests

response = requests.post('http://localhost:5000/api/admin/login', json={
    'token': 'your-admin-token'
})

if response.status_code == 200:
    print("Authentication successful")
```

## Public Endpoints

Public endpoints do not require authentication.

### Root Endpoint

Health check endpoint.

**Endpoint:**
```http
GET /
```

**Response:** Empty string (200 OK)

**Purpose:** Verify server is running

**cURL Example:**
```bash
curl -I http://localhost:5000/
# HTTP/1.1 200 OK
```

### Generate Tracking UUID

Generate a new tracking UUID and optionally create a recipient record.

**Endpoint:**
```http
GET /new-uuid
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `description` | string | No | Human-readable description |
| `email` | string | No | Recipient email address |

**Request Example:**
```http
GET /new-uuid?description=John%20Doe&email=john@example.com
```

**Response (200 OK):**
```html
<p>550e8400-e29b-41d4-a716-446655440000</p>

John Doe john@example.com
```

**Side Effects:**
- Creates a new recipient record in the database
- Returns the generated UUID

**cURL Example:**
```bash
curl "http://localhost:5000/new-uuid?description=Test%20User&email=test@example.com"
```

**Python Example:**
```python
import requests

response = requests.get('http://localhost:5000/new-uuid', params={
    'description': 'Test User',
    'email': 'test@example.com'
})

print(response.text)  # Contains UUID
```

### Tracking Pixel Endpoint

Returns a 1x1 transparent PNG and logs the tracking event.

**Endpoint:**
```http
GET /img/<uuid>
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `uuid` | string | Tracking UUID from recipient |

**Response (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: image/png
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Expires: -1

<1x1 transparent PNG>
```

**Response (404 Not Found):**
```json
{
  "error": "Recipient not found"
}
```

**Headers Sent:**
- `Content-Type: image/png`
- `Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0`
- `Pragma: no-cache`
- `Expires: -1`

**Data Logged:**
- Timestamp
- IP address (from Cloudflare headers if available)
- Country (from Cloudflare headers)
- User agent
- All request headers
- Referrer

**Special Handling:**
- Gmail image proxy requests are detected and not double-counted

**cURL Example:**
```bash
curl -I "http://localhost:5000/img/550e8400-e29b-41d4-a716-446655440000"
```

## Admin Endpoints

All admin endpoints require authentication.

### Recipients

#### List Recipients

Retrieve all recipients.

**Endpoint:**
```http
GET /api/admin/recipients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "description": "John Doe",
    "email": "john@example.com"
  },
  {
    "id": 2,
    "r_uuid": "660e8400-e29b-41d4-a716-446655440001",
    "description": "Jane Smith",
    "email": "jane@example.com"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer your-token"
```

#### Create Recipient

Create a new recipient.

**Endpoint:**
```http
POST /api/admin/recipients
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "description": "John Doe"
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email format, max 100 chars |
| `description` | string | No | Max 200 chars |

**Response (201 Created):**
```json
{
  "id": 1,
  "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "description": "John Doe",
  "email": "john@example.com"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Email is required"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "description": "John Doe"
  }'
```

**JavaScript Example:**
```javascript
const response = await fetch('/api/admin/recipients', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'john@example.com',
    description: 'John Doe'
  })
});

const recipient = await response.json();
```

#### Get Recipient

(Future endpoint - currently use List and filter client-side)

#### Update Recipient

Update an existing recipient.

**Endpoint:**
```http
PUT /api/admin/recipients/<id>
Authorization: Bearer <token>
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Recipient ID |

**Request Body (all fields optional):**
```json
{
  "email": "newemail@example.com",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Updated description",
  "email": "newemail@example.com"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Recipient not found"
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:5000/api/admin/recipients/1 \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description"
  }'
```

#### Delete Recipient

Delete a recipient.

**Endpoint:**
```http
DELETE /api/admin/recipients/<id>
Authorization: Bearer <token>
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Recipient ID |

**Response (200 OK):**
```json
{
  "status": "deleted"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Recipient not found"
}
```

**Note:** Deleting a recipient does NOT delete associated tracking events.

**cURL Example:**
```bash
curl -X DELETE http://localhost:5000/api/admin/recipients/1 \
  -H "Authorization: Bearer your-token"
```

### Settings

#### Get Settings

Retrieve current application settings.

**Endpoint:**
```http
GET /api/admin/settings
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "tracking_enabled": true,
  "allowed_domains": "https://mail.google.com,https://outlook.live.com",
  "log_level": "INFO"
}
```

**cURL Example:**
```bash
curl http://localhost:5000/api/admin/settings \
  -H "Authorization: Bearer your-token"
```

#### Update Settings

Update application settings (in-memory for current version).

**Endpoint:**
```http
PUT /api/admin/settings
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "tracking_enabled": true,
  "allowed_domains": "https://mail.google.com",
  "log_level": "DEBUG"
}
```

**Response (200 OK):**
```json
{
  "status": "updated",
  "settings": {
    "tracking_enabled": true,
    "allowed_domains": "https://mail.google.com",
    "log_level": "DEBUG"
  }
}
```

**Note:** Settings are currently stored in-memory and reset on server restart.

**cURL Example:**
```bash
curl -X PUT http://localhost:5000/api/admin/settings \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "log_level": "DEBUG"
  }'
```

### Dashboard

#### Get Dashboard Statistics

Retrieve dashboard statistics.

**Endpoint:**
```http
GET /api/admin/stats
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "total_recipients": 150,
  "total_events": 1250,
  "events_today": 45,
  "unique_opens": 98,
  "recent_events": [
    {
      "email": 1,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "email": 5,
      "timestamp": "2024-01-15T09:15:00Z"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `total_recipients` | integer | Total number of recipients |
| `total_events` | integer | Total tracking events |
| `events_today` | integer | Events in last 24 hours |
| `unique_opens` | integer | Unique recipients who opened emails |
| `recent_events` | array | Last 5 tracking events |

**cURL Example:**
```bash
curl http://localhost:5000/api/admin/stats \
  -H "Authorization: Bearer your-token"
```

## Analytics Endpoints

All analytics endpoints require authentication.

### Summary

#### Get Analytics Summary

Retrieve summary statistics.

**Endpoint:**
```http
GET /api/analytics/summary
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "total_events": 1250,
  "unique_recipients": 98,
  "avg_daily_opens": 17.86,
  "top_country": "United States"
}
```

**cURL Example:**
```bash
curl http://localhost:5000/api/analytics/summary \
  -H "Authorization: Bearer your-token"
```

### Events

#### Get Time-Series Events

Retrieve time-series event data.

**Endpoint:**
```http
GET /api/analytics/events
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | string | `7d` | Time range (e.g., `7d`, `30d`, `90d`) |

**Response (200 OK):**
```json
[
  {
    "date": "2024-01-10",
    "count": 15
  },
  {
    "date": "2024-01-11",
    "count": 23
  },
  {
    "date": "2024-01-12",
    "count": 18
  }
]
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/analytics/events?range=30d" \
  -H "Authorization: Bearer your-token"
```

### Recipients

#### Get Top Recipients

Retrieve top recipients by number of opens.

**Endpoint:**
```http
GET /api/analytics/recipients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "recipient_id": 1,
    "count": 45
  },
  {
    "recipient_id": 5,
    "count": 32
  }
]
```

**cURL Example:**
```bash
curl http://localhost:5000/api/analytics/recipients \
  -H "Authorization: Bearer your-token"
```

### Geographic

#### Get Geographic Distribution

Retrieve geographic distribution of opens.

**Endpoint:**
```http
GET /api/analytics/geo
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "country": "United States",
    "count": 450
  },
  {
    "country": "United Kingdom",
    "count": 230
  },
  {
    "country": "Germany",
    "count": 180
  },
  {
    "country": "Unknown",
    "count": 50
  }
]
```

**cURL Example:**
```bash
curl http://localhost:5000/api/analytics/geo \
  -H "Authorization: Bearer your-token"
```

### Clients

#### Get Email Client Breakdown

Retrieve breakdown by email client.

**Endpoint:**
```http
GET /api/analytics/clients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "name": "Gmail",
    "value": 650
  },
  {
    "name": "Outlook",
    "value": 320
  },
  {
    "name": "Apple Mail",
    "value": 180
  },
  {
    "name": "Unknown",
    "value": 100
  }
]
```

**Detected Clients:**
- Gmail (including GmailImageProxy)
- Outlook
- Apple Mail
- Yahoo Mail
- Thunderbird
- Other (parsed from user agent)
- Unknown (parsing failed)

**cURL Example:**
```bash
curl http://localhost:5000/api/analytics/clients \
  -H "Authorization: Bearer your-token"
```

### Export

#### Export Analytics Data

Export all tracking data as CSV.

**Endpoint:**
```http
GET /api/analytics/export
Authorization: Bearer <token>
```

**Response (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename=analytics_export.csv

ID,Recipient ID,Timestamp,Country,User Agent
1,1,2024-01-15T10:30:00,US,Mozilla/5.0...
2,1,2024-01-15T11:45:00,GB,Mozilla/5.0...
```

**CSV Columns:**
1. `ID` - Tracking event ID
2. `Recipient ID` - Associated recipient ID
3. `Timestamp` - ISO 8601 timestamp
4. `Country` - Country code or name
5. `User Agent` - Full user agent string

**cURL Example:**
```bash
curl http://localhost:5000/api/analytics/export \
  -H "Authorization: Bearer your-token" \
  -o analytics_export.csv
```

**JavaScript Example:**
```javascript
const response = await fetch('/api/analytics/export', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'analytics_export.csv';
a.click();
```

## Error Handling

### HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

### Error Response Format

All error responses follow this format:

```json
{
  "error": "Descriptive error message"
}
```

### Common Errors

#### 400 Bad Request

**Missing Required Field:**
```json
{
  "error": "Email is required"
}
```

**Invalid Format:**
```json
{
  "error": "Invalid email format"
}
```

#### 401 Unauthorized

**Missing Token:**
```json
{
  "error": "Authentication required"
}
```

**Invalid Token:**
```json
{
  "error": "Invalid token"
}
```

#### 404 Not Found

**Resource Not Found:**
```json
{
  "error": "Recipient not found"
}
```

**Endpoint Not Found:**
```json
{
  "error": "Endpoint not found"
}
```

#### 500 Internal Server Error

**Server Error:**
```json
{
  "error": "Internal server error"
}
```

**Database Error:**
```json
{
  "error": "Database error occurred"
}
```

## Rate Limiting

### Current Implementation

The current version does not implement rate limiting.

### Recommendations for Production

**Via Reverse Proxy (nginx):**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

**Via Cloudflare:**
- Enable rate limiting in Cloudflare dashboard
- Set appropriate thresholds for your use case

**Application-Level (Future):**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route("/api/admin/recipients")
@limiter.limit("100 per minute")
def get_recipients():
    # ...
```

### Best Practices

- Implement rate limiting in production
- Use appropriate limits for your traffic
- Return `429 Too Many Requests` when limit exceeded
- Include `Retry-After` header

## Code Examples

### Python Client

```python
import requests

class ReadReceiptClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def get_recipients(self):
        response = self.session.get(f'{self.base_url}/api/admin/recipients')
        response.raise_for_status()
        return response.json()

    def create_recipient(self, email, description=''):
        response = self.session.post(
            f'{self.base_url}/api/admin/recipients',
            json={'email': email, 'description': description}
        )
        response.raise_for_status()
        return response.json()

    def get_analytics_summary(self):
        response = self.session.get(f'{self.base_url}/api/analytics/summary')
        response.raise_for_status()
        return response.json()

    def export_analytics(self, filename='analytics.csv'):
        response = self.session.get(f'{self.base_url}/api/analytics/export')
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)

# Usage
client = ReadReceiptClient('http://localhost:5000', 'your-token')
recipients = client.get_recipients()
summary = client.get_analytics_summary()
```

### JavaScript Client

```javascript
class ReadReceiptClient {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Request failed');
    }

    return response.json();
  }

  async getRecipients() {
    return this.request('/api/admin/recipients');
  }

  async createRecipient(email, description = '') {
    return this.request('/api/admin/recipients', {
      method: 'POST',
      body: JSON.stringify({ email, description })
    });
  }

  async deleteRecipient(id) {
    return this.request(`/api/admin/recipients/${id}`, {
      method: 'DELETE'
    });
  }

  async getAnalyticsSummary() {
    return this.request('/api/analytics/summary');
  }

  async getAnalyticsEvents(range = '7d') {
    return this.request(`/api/analytics/events?range=${range}`);
  }

  async exportAnalytics() {
    const response = await fetch(`${this.baseURL}/api/analytics/export`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.blob();
  }
}

// Usage
const client = new ReadReceiptClient('http://localhost:5000', 'your-token');
const recipients = await client.getRecipients();
const summary = await client.getAnalyticsSummary();
```

### cURL Examples

```bash
# Set variables
BASE_URL="http://localhost:5000"
TOKEN="your-admin-token"

# Login
curl -X POST $BASE_URL/api/admin/login \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"

# List recipients
curl $BASE_URL/api/admin/recipients \
  -H "Authorization: Bearer $TOKEN"

# Create recipient
curl -X POST $BASE_URL/api/admin/recipients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "description": "John Doe"}'

# Update recipient
curl -X PUT $BASE_URL/api/admin/recipients/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated"}'

# Delete recipient
curl -X DELETE $BASE_URL/api/admin/recipients/1 \
  -H "Authorization: Bearer $TOKEN"

# Get stats
curl $BASE_URL/api/admin/stats \
  -H "Authorization: Bearer $TOKEN"

# Get analytics summary
curl $BASE_URL/api/analytics/summary \
  -H "Authorization: Bearer $TOKEN"

# Get time-series data
curl "$BASE_URL/api/analytics/events?range=30d" \
  -H "Authorization: Bearer $TOKEN"

# Export analytics
curl $BASE_URL/api/analytics/export \
  -H "Authorization: Bearer $TOKEN" \
  -o analytics.csv
```

## Next Steps

- [Admin Guide](admin-guide.md) - Using the admin dashboard
- [Architecture](architecture.md) - System design
- [Deployment](deployment.md) - Production deployment

---

**Need help?** See [Troubleshooting](troubleshooting.md) or open an issue on GitHub.
