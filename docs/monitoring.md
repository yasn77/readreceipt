# Monitoring and Metrics

This document describes the Prometheus metrics exposed by the Read Receipt application and how to configure monitoring with Prometheus and Grafana.

## Overview

The application exposes metrics via the `/metrics` endpoint in Prometheus format. These metrics include:

- **Automatic HTTP metrics** (provided by `prometheus-flask-exporter`)
- **Custom business metrics** (tracking events, recipients, etc.)
- **Health check endpoint** at `/metrics/health`

## Setting Up Prometheus

### 1. Prometheus Configuration

Add the following scrape configuration to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'readreceipt'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### 2. Running Prometheus

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

### 3. Verify Metrics Endpoint

Test that metrics are being exposed:

```bash
curl http://localhost:5000/metrics
```

Expected output should include metrics like:

```
# HELP readreceipt_http_requests_total Total HTTP requests
# TYPE readreceipt_http_requests_total counter
readreceipt_http_requests_total{endpoint="/img/<this_uuid>",method="GET",status="200"} 1.0
```

## Available Metrics

### HTTP Metrics (Automatic)

| Metric Name | Type | Description |
|-------------|------|-------------|
| `readreceipt_http_requests_total` | Counter | Total HTTP requests by endpoint, method, and status |
| `readreceipt_http_request_duration_seconds` | Histogram | Request latency in seconds |
| `readreceipt_http_requests_in_progress` | Gauge | Number of requests currently being processed |

### Custom Business Metrics

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `tracking_events_total` | Counter | Total number of tracking events recorded | `recipient_id`, `country` |
| `tracking_events_unique_recipients` | Gauge | Number of unique recipients with tracking events | None |
| `recipients_total` | Gauge | Total number of recipients in the system | None |
| `tracking_event_processing_seconds` | Histogram | Time spent processing tracking events | None |

### Health Check Metrics

The `/metrics/health` endpoint returns JSON with:

```json
{
  "status": "healthy",
  "database": "connected",
  "metrics_count": 42,
  "timestamp": "2026-03-05T10:00:00"
}
```

## Setting Up Grafana

### 1. Running Grafana

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v $(pwd)/grafana-data:/var/lib/grafana \
  grafana/grafana:latest
```

### 2. Add Prometheus Data Source

1. Navigate to `http://localhost:3000` (default credentials: `admin`/`admin`)
2. Go to **Configuration** → **Data Sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Set URL to `http://prometheus:9090` (or your Prometheus URL)
6. Click **Save & Test**

### 3. Import Dashboard

Import the provided Grafana dashboard from `docs/grafana-dashboard.json`:

1. Go to **Dashboards** → **Import**
2. Upload the JSON file or paste the JSON content
3. Select the Prometheus data source
4. Click **Import**

## Example PromQL Queries

### Request Rate

```promql
# Requests per second over the last 5 minutes
rate(readreceipt_http_requests_total[5m])

# Requests per minute by endpoint
sum by (endpoint) (rate(readreceipt_http_requests_total[1m])) * 60
```

### Error Rate

```promql
# Error rate (5xx responses)
sum by (endpoint) (rate(readreceipt_http_requests_total{status=~"5.."}[5m]))

# Error percentage
sum(rate(readreceipt_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(readreceipt_http_requests_total[5m])) * 100
```

### Latency

```promql
# Average request duration
rate(readreceipt_http_request_duration_seconds_sum[5m])
/
rate(readreceipt_http_request_duration_seconds_count[5m])

# 95th percentile latency
histogram_quantile(0.95,
  sum(rate(readreceipt_http_request_duration_seconds_bucket[5m])) by (le)
)

# 99th percentile latency
histogram_quantile(0.99,
  sum(rate(readreceipt_http_request_duration_seconds_bucket[5m])) by (le)
)
```

### Business Metrics

```promql
# Total tracking events
sum(tracking_events_total)

# Tracking events by country
sum by (country) (tracking_events_total)

# Unique recipients
tracking_events_unique_recipients

# Total recipients
recipients_total

# Average processing time
rate(tracking_event_processing_seconds_sum[5m])
/
rate(tracking_event_processing_seconds_count[5m])
```

## Alert Rules

Add these alert rules to your Prometheus configuration or a separate rules file:

```yaml
groups:
  - name: readreceipt_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(readreceipt_http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(readreceipt_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(readreceipt_http_request_duration_seconds_bucket[5m])) by (le)
          ) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }}s"

      # Database disconnected
      - alert: DatabaseDisconnected
        expr: up{job="readreceipt"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Read Receipt application is down"
          description: "The application has been down for more than 1 minute"

      # No tracking events
      - alert: NoTrackingEvents
        expr: increase(tracking_events_total[1h]) == 0
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "No tracking events in the last hour"
          description: "No tracking events have been recorded in the last hour"
```

## Troubleshooting

### Metrics Not Showing

1. Verify the `/metrics` endpoint is accessible:
   ```bash
   curl http://localhost:5000/metrics
   ```

2. Check Prometheus targets:
   - Navigate to `http://localhost:9090/targets`
   - Ensure the `readreceipt` target is `UP`

3. Check application logs for errors

### Grafana Dashboard Not Working

1. Verify Prometheus data source is configured correctly
2. Check that the dashboard JSON is compatible with your Grafana version
3. Ensure Prometheus is scraping metrics correctly

### High Cardinality Issues

If you experience high cardinality issues with the `tracking_events_total` metric:

1. Consider reducing the cardinality of the `recipient_id` label
2. Use recording rules to pre-aggregate metrics
3. Implement metric relabeling in Prometheus configuration

## Best Practices

1. **Scrape Interval**: Use a 15-second scrape interval for most metrics
2. **Retention**: Configure appropriate retention periods in Prometheus
3. **Alerting**: Set up alerts for critical metrics (error rate, latency, availability)
4. **Dashboarding**: Create dashboards for different stakeholders (ops, business, development)
5. **Documentation**: Keep this documentation up to date as metrics evolve
