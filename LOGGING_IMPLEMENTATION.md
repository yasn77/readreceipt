# Structured JSON Logging Implementation

## Summary

This document summarises the structured JSON logging implementation for the Read Receipt application.

## Deliverables

### 1. Logging Module (`utils/logging.py`)

A comprehensive logging module providing:

- **JSON Formatter** (`RedactingJsonFormatter`): Custom JSON formatter with sensitive data redaction
- **Structured Logger** (`StructuredLogger`): Wrapper for consistent structured logging
- **Request ID Middleware** (`RequestIDMiddleware`): Automatic request ID generation and tracking
- **Performance Logging**: Tools for monitoring slow operations

Key features:
- Automatic request ID generation (UUID per request)
- Sensitive data redaction (passwords, tokens, API keys)
- Configurable log levels and formats
- Performance monitoring with thresholds

### 2. Updated Application (`app.py`)

Changes made:
- Import structured logging utilities
- Replace `print()` statements with structured logging
- Add logging to key endpoints (login, CRUD operations)
- Configure logging on application startup
- Include request context in all log entries

### 3. Request ID Middleware

The middleware:
- Generates unique `request_id` (UUID) for each request
- Stores ID in Flask's `g` object for access throughout request lifecycle
- Adds `X-Request-ID` header to all responses
- Logs request start/end with timing information

### 4. Tests (`tests/test_logging.py`)

Comprehensive test suite covering:
- JSON formatter redaction (5 tests)
- Structured logger functionality (3 tests)
- Middleware behaviour (3 tests)
- Log configuration (4 tests)
- Performance logging (4 tests)
- Endpoint logging integration (5 tests)
- Sensitive data redaction (3 tests)

All 27 tests passing.

### 5. Documentation (`docs/logging.md`)

Complete documentation including:
- Configuration options
- Log format examples
- Sensitive data redaction
- Performance logging
- Integration with ELK stack, Fluentd, Datadog, Splunk
- Log parsing examples (jq, Python, grep)
- Best practices
- Troubleshooting guide

## Configuration

### Environment Variables

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_LEVEL=INFO

# Log format: json or text
export LOG_FORMAT=json

# Additional fields to redact (comma-separated)
export LOG_REDACT_FIELDS=custom_secret,api_token
```

### Application Configuration

```python
app.config["LOG_LEVEL"] = os.environ.get("LOG_LEVEL", "INFO")
app.config["LOG_FORMAT"] = os.environ.get("LOG_FORMAT", "json")
app.config["LOG_REDACT_FIELDS"] = os.environ.get("LOG_REDACT_FIELDS", "").split(",")
```

## Usage Examples

### Basic Logging

```python
from utils.logging import get_logger

logger = get_logger(__name__)

# Simple log
logger.info("User logged in")

# Log with context
logger.info(
    "User action",
    user="john@example.com",
    action="create_recipient",
    result="success"
)
```

### Performance Logging

```python
from utils.logging import timed_operation

@timed_operation("database_query", threshold_ms=100)
def get_data():
    # Function will be timed and logged if slow
    return data
```

## Log Format Example

```json
{
  "timestamp": "2026-03-05T10:30:00.000000+00:00",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "logging_module": "app",
  "logging_function": "send_img",
  "status_code": 200,
  "duration_ms": 45.2,
  "path": "/img/abc123"
}
```

## Sensitive Data Redaction

Automatically redacted fields:
- `password`
- `token`
- `api_key`
- `secret`
- `authorization`
- `cookie`
- `session_id`
- `credentials`
- `auth`

Example:
```json
{
  "message": "Login attempt",
  "token": "[REDACTED]",
  "user": "john"
}
```

## Testing

Run the logging tests:

```bash
source venv/bin/activate
python -m pytest tests/test_logging.py -v
```

Run all tests:

```bash
python -m pytest tests/ -v
```

## Integration with Log Aggregation

### ELK Stack

Configure Logstash to parse JSON logs:

```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "readreceipt-logs-%{+YYYY.MM.dd}"
  }
}
```

### Parsing with jq

```bash
# Filter errors
cat app.log | jq 'select(.level == "ERROR")'

# Find slow operations
cat app.log | jq 'select(.duration_ms > 100)'

# Extract request IDs
cat app.log | jq -r '.request_id'
```

## Dependencies

Added to `requirements.txt`:
```
python-json-logger==2.0.7
```

## Files Modified

1. `requirements.txt` - Added python-json-logger dependency
2. `app.py` - Integrated structured logging
3. `utils/logging.py` - New logging module (created)
4. `tests/test_logging.py` - New test suite (created)
5. `docs/logging.md` - New documentation (created)
6. `docs/index.md` - Updated to include logging docs

## Verification

Test the implementation:

```bash
# Run with JSON logging
LOG_FORMAT=json LOG_LEVEL=INFO python app.py

# Make a request and check logs
curl http://localhost:5000/new-uuid?description=Test

# Check response headers for X-Request-ID
curl -i http://localhost:5000/
```

Expected output:
- JSON-formatted log entries
- `X-Request-ID` header in responses
- Sensitive data redacted in logs
- Request timing information included
