# Logging Configuration

The Read Receipt application uses structured JSON logging for production environments, with support for text-based logging during development.

## Overview

The logging system provides:

- **Structured JSON output** for easy parsing by log aggregation systems
- **Request ID tracking** for correlating logs across requests
- **Sensitive data redaction** for passwords, tokens, and API keys
- **Performance monitoring** for slow operations
- **Configurable log levels** via environment variables

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `LOG_FORMAT` | Output format (`json` or `text`) | `json` |
| `LOG_REDACT_FIELDS` | Comma-separated list of additional fields to redact | `` |

### Application Configuration

```python
app.config["LOG_LEVEL"] = os.environ.get("LOG_LEVEL", "INFO")
app.config["LOG_FORMAT"] = os.environ.get("LOG_FORMAT", "json")
app.config["LOG_REDACT_FIELDS"] = os.environ.get("LOG_REDACT_FIELDS", "").split(",")
```

## Log Format

### JSON Format (Production)

Each log entry is a JSON object with the following structure:

```json
{
  "timestamp": "2026-03-05T10:30:00.000000",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "module": "app",
  "function": "send_img",
  "status_code": 200,
  "duration_ms": 45.2
}
```

### Standard Fields

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 formatted timestamp |
| `level` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `message` | Human-readable log message |
| `request_id` | Unique UUID for request correlation |
| `module` | Python module name |
| `function` | Function name (when available) |

### Contextual Fields

Additional fields may be included based on the log context:

| Field | Description |
|-------|-------------|
| `user` | User identifier |
| `action` | Action being performed |
| `result` | Outcome of the action |
| `duration_ms` | Operation duration in milliseconds |
| `recipient_id` | Database recipient ID |
| `recipient_uuid` | Public recipient UUID |
| `status_code` | HTTP status code |

## Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic information, fast operations |
| `INFO` | Normal operational messages, request completion |
| `WARNING` | Unexpected but handled situations, slow operations |
| `ERROR` | Error conditions that prevent operation completion |
| `CRITICAL` | Severe errors requiring immediate attention |

## Sensitive Data Redaction

The logging system automatically redacts sensitive fields:

### Default Redacted Fields

- `password`
- `token`
- `api_key`
- `secret`
- `authorization`
- `cookie`
- `session_id`
- `credentials`
- `auth`

### Example

Input:
```python
logger.info("Login attempt", token="secret123", user="john")
```

Output:
```json
{
  "timestamp": "2026-03-05T10:30:00.000000",
  "level": "INFO",
  "message": "Login attempt",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "token": "[REDACTED]",
  "user": "john"
}
```

## Request ID Tracking

Every request is assigned a unique UUID that:

1. Is generated at the start of each request
2. Stored in Flask's `g` object for access throughout the request
3. Added to all log entries during that request
4. Included in the `X-Request-ID` response header

### Usage

```python
from flask import g
from utils.logging import get_logger

logger = get_logger(__name__)

@app.route("/example")
def example():
    # Request ID is automatically available
    logger.info("Processing request", request_id=g.request_id)
```

## Performance Logging

### Manual Performance Logging

```python
from utils.logging import log_performance

# Log operation with 100ms threshold
log_performance("database_query", duration_ms=150, threshold_ms=100)
```

### Timed Operation Decorator

```python
from utils.logging import timed_operation

@timed_operation("expensive_query", threshold_ms=100)
def get_data():
    # Function body
    return data
```

### Thresholds

| Operation Type | Threshold |
|----------------|-----------|
| Database queries | 100ms |
| API requests | 500ms |
| File operations | 200ms |

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

# Error logging
try:
    process_data()
except Exception as e:
    logger.error(
        "Processing failed",
        error=str(e),
        exc_info=True
    )
```

### Endpoint Logging

```python
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if not data:
        logger.warning("Invalid JSON in login request")
        return json.jsonify({"error": "Invalid JSON"}), 400

    token = data.get("token", "")
    if token == admin_token:
        logger.info("Admin login successful")
        return json.jsonify({"status": "authenticated"}), 200
    
    logger.warning("Admin login failed")
    return json.jsonify({"error": "Invalid token"}), 401
```

## Integration with Log Aggregation Systems

### ELK Stack (Elasticsearch, Logstash, Kibana)

#### Logstash Configuration

```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  if [type] == "readreceipt" {
    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }
    
    mutate {
      add_field => { "[@metadata][service]" => "readreceipt" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "readreceipt-logs-%{+YYYY.MM.dd}"
  }
}
```

#### Kibana Index Pattern

Create an index pattern: `readreceipt-logs-*`

Key fields to visualise:
- `level` - Log level distribution
- `request_id` - Request tracing
- `duration_ms` - Performance metrics
- `status_code` - HTTP response codes

### Fluentd Configuration

```xml
<source>
  @type tail
  path /var/log/readreceipt/*.log
  pos_file /var/log/fluentd/readreceipt.log.pos
  tag readreceipt
  <parse>
    @type json
  </parse>
</source>

<match readreceipt>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name readreceipt-logs
  type_name _doc
</match>
```

### Datadog

Configure the Datadog Agent to collect logs:

```yaml
# /etc/datadog-agent/conf.d/python.d/conf.yaml
init_config:

instances:
  - name: readreceipt
    type: json
    path: /var/log/readreceipt/app.log
```

### Splunk

1. Install Splunk Universal Forwarder
2. Configure inputs.conf:

```ini
[monitor:///var/log/readreceipt/*.log]
sourcetype = json
index = readreceipt
```

## Parsing Logs

### Using jq

```bash
# Filter by log level
cat app.log | jq 'select(.level == "ERROR")'

# Extract request IDs
cat app.log | jq -r '.request_id'

# Find slow operations
cat app.log | jq 'select(.duration_ms > 100)'

# Group by status code
cat app.log | jq -s 'group_by(.status_code) | map({status: .[0].status_code, count: length})'
```

### Using Python

```python
import json

with open('app.log') as f:
    for line in f:
        log_entry = json.loads(line)
        if log_entry['level'] == 'ERROR':
            print(f"Error: {log_entry['message']}")
```

### Using grep and awk

```bash
# Find all errors
grep '"level": "ERROR"' app.log

# Extract timestamps and messages
grep '"level": "ERROR"' app.log | awk -F'"' '{print $4, $8}'
```

## Development vs Production

### Development (Text Format)

```bash
export LOG_FORMAT=text
export LOG_LEVEL=DEBUG
```

Output:
```
2026-03-05 10:30:00 - app - INFO - Request completed
```

### Production (JSON Format)

```bash
export LOG_FORMAT=json
export LOG_LEVEL=INFO
```

Output:
```json
{"timestamp": "2026-03-05T10:30:00.000000", "level": "INFO", "message": "Request completed"}
```

## Best Practices

1. **Always use structured logging** - Include context in every log entry
2. **Use appropriate log levels** - Don't log everything as ERROR
3. **Include request IDs** - Essential for debugging in production
4. **Redact sensitive data** - Never log passwords, tokens, or PII
5. **Log performance metrics** - Track slow operations
6. **Avoid logging large payloads** - Summarise instead
7. **Use consistent field names** - Makes parsing and querying easier

## Troubleshooting

### Logs Not Appearing

1. Check `LOG_LEVEL` is set appropriately
2. Verify the logger is configured before use
3. Ensure handlers are attached to the root logger

### JSON Format Not Working

1. Verify `LOG_FORMAT=json` is set
2. Check that `python-json-logger` is installed
3. Ensure `configure_logging()` is called

### Request ID Missing

1. Verify `init_logging_middleware()` is called
2. Check that logging happens within request context
3. Ensure Flask's `g` object is accessible

### Sensitive Data Not Redacted

1. Add field name to `LOG_REDACT_FIELDS` environment variable
2. Verify field name matches exactly (case-insensitive matching)
3. Check `RedactingJsonFormatter` is being used
