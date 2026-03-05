# Retry Logic with Exponential Backoff

## Overview

The Read Receipt application implements server-side retry logic with exponential backoff to handle transient database failures gracefully. This ensures that temporary issues (such as database connection timeouts, deadlocks, or brief network interruptions) do not result in permanent data loss.

## How It Works

### Retry Decorator

The `retry_with_backoff` decorator wraps database operations and automatically retries them when they fail. The retry strategy uses:

1. **Exponential Backoff**: Each retry waits progressively longer (2s, 4s, 8s, 16s, 30s)
2. **Jitter**: Random variation (±25%) is added to prevent thundering herd problems
3. **Maximum Attempts**: Operations are retried up to 5 times by default
4. **Maximum Delay**: No single wait exceeds 30 seconds

### Dead Letter Queue

When an operation fails after all retry attempts, it is logged to the `FailedEvent` table (dead letter queue) for later analysis and manual intervention. This ensures:

- No data is silently lost
- Failed operations can be reviewed and reprocessed
- System health can be monitored via failed event counts

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRY_MAX_ATTEMPTS` | `5` | Maximum number of retry attempts |
| `RETRY_BASE_DELAY` | `2` | Base delay in seconds for exponential backoff |
| `RETRY_MAX_DELAY` | `30` | Maximum delay between retries in seconds |
| `RETRY_JITTER` | `true` | Whether to add random jitter to delays |

### Application Configuration

```python
app.config["RETRY_MAX_ATTEMPTS"] = int(os.environ.get("RETRY_MAX_ATTEMPTS", "5"))
app.config["RETRY_BASE_DELAY"] = float(os.environ.get("RETRY_BASE_DELAY", "2"))
app.config["RETRY_MAX_DELAY"] = float(os.environ.get("RETRY_MAX_DELAY", "30"))
app.config["RETRY_JITTER"] = os.environ.get("RETRY_JITTER", "true").lower() == "true"
```

## Usage

### Basic Decorator Usage

```python
from utils.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def database_operation():
    db.session.commit()
```

### Using commit_with_retry Helper

The application provides a `commit_with_retry` helper function that integrates with the dead letter queue:

```python
from app import commit_with_retry

# Simple usage
db.session.add(entity)
commit_with_retry("entity_insert", entity_id=entity.id)

# With metadata for debugging
commit_with_retry(
    "tracking_insert",
    entity_id=tracking_id,
    metadata={"user_agent": "Gmail", "country": "US"}
)
```

### Manual Retry Configuration

```python
from utils.retry import create_retry_decorator

retry_decorator = create_retry_decorator(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    jitter=True,
    exceptions=(OperationalError, TimeoutError),  # Only retry specific exceptions
)

@retry_decorator
def my_function():
    ...
```

## Dead Letter Queue

### FailedEvent Model

```python
class FailedEvent(db.Model):
    id = db.Column("failed_event_id", db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50))  # e.g., 'tracking_insert'
    entity_id = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text)
    error_details = db.Column(db.JSON)
    retry_count = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    metadata = db.Column(db.JSON, nullable=True)
```

### Logging Failed Events

```python
from app import log_failed_event

log_failed_event(
    operation_type="tracking_insert",
    error_message="Database connection timeout",
    error_details={"exception_type": "OperationalError"},
    retry_count=5,
    entity_id=123,
    metadata={"user_agent": "Gmail"}
)
```

### Querying Failed Events

```python
# Get all failed events
failed_events = FailedEvent.query.all()

# Get failed events by operation type
tracking_failures = FailedEvent.query.filter_by(
    operation_type="tracking_insert"
).all()

# Get recent failures
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)
recent_failures = FailedEvent.query.filter(
    FailedEvent.timestamp >= yesterday
).all()
```

## Backoff Calculation

The delay for each retry attempt is calculated as:

```
delay = min(base_delay * 2^(attempt - 1), max_delay)
```

With jitter (default):
```
delay += random.uniform(-jitter_range, jitter_range)
where jitter_range = delay * 0.25
```

### Example Delays (base_delay=2s, max_delay=30s, no jitter)

| Attempt | Delay |
|---------|-------|
| 1 | 2s |
| 2 | 4s |
| 3 | 8s |
| 4 | 16s |
| 5 | 30s (capped) |

Total maximum wait time: ~60 seconds

## Operations with Retry Logic

The following database operations are wrapped with retry logic:

1. **Tracking Insert**: When a tracking pixel is loaded
2. **Recipient Insert**: When creating new recipients
3. **Recipient Update**: When updating recipient details
4. **Recipient Delete**: When deleting recipients

## Monitoring

### Logging

Retry attempts are logged at WARNING level with details about:
- Function being retried
- Attempt number
- Exception that triggered the retry

Failed operations (after all retries) are logged at ERROR level with full stack traces.

### Metrics

Monitor the following for retry-related issues:

1. **FailedEvent count**: Increasing count indicates persistent database issues
2. **Retry log frequency**: High frequency suggests transient instability
3. **Database connection errors**: May indicate need for connection pool tuning

## Testing

Run the retry tests:

```bash
python -m pytest tests/test_retry.py -v
```

Key test scenarios:
- Successful operation without retries
- Operation succeeds after retries
- Operation fails after max attempts
- Dead letter queue captures failures
- Exponential backoff timing
- Configuration from environment variables

## Troubleshooting

### High Retry Rate

If retries are frequent:
1. Check database connection pool settings
2. Review database server logs for issues
3. Consider increasing `RETRY_BASE_DELAY`
4. Investigate network connectivity

### Failed Events Accumulating

If FailedEvent records are accumulating:
1. Review error messages for patterns
2. Check database server health
3. Consider manual intervention for critical failures
4. Implement automated alerting on failed event count

### Adjusting Retry Parameters

For more aggressive retry:
```
RETRY_MAX_ATTEMPTS=10
RETRY_BASE_DELAY=1
```

For less aggressive retry:
```
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=5
RETRY_MAX_DELAY=60
```

## Dependencies

- **tenacity==8.2.3**: Retry library providing the core retry logic

## See Also

- [Architecture Documentation](architecture.md)
- [Deployment Guide](deployment.md)
- [Monitoring and Metrics](admin-guide.md)
