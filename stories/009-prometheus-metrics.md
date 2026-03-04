# Story: Prometheus Metrics

## Description
As a system operator, I want Prometheus metrics exposed, so that I can monitor application performance and set up alerts.

## Acceptance Criteria
- [ ] `/metrics` endpoint available
- [ ] Request count metric
- [ ] Request latency histogram
- [ ] Error rate metric
- [ ] Active users metric
- [ ] Database connection pool metrics
- [ ] Custom business metrics (tracking events count)

## Technical Notes
- Use prometheus-flask-exporter
- Define custom metrics for business logic
- Add labels for dimensions (endpoint, method, status)
- Configure appropriate buckets for histograms
- Document all metrics

## Metrics to Expose
1. **HTTP Metrics** (automatic)
   - `http_requests_total`
   - `http_request_duration_seconds`
   - `http_requests_in_progress`

2. **Business Metrics** (custom)
   - `tracking_events_total`
   - `tracking_events_unique_recipients`
   - `recipients_total`

3. **System Metrics** (automatic)
   - Process CPU/memory
   - Thread count

## Example Query
```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

## Definition of Done
- [ ] `/metrics` endpoint working
- [ ] All metrics exposed
- [ ] Grafana dashboard created (optional)
- [ ] Alert rules documented (optional)
- [ ] Documentation updated
- [ ] PR reviewed and approved
