# Story: Structured JSON Logging

## Description
As a developer, I want structured JSON logs, so that I can easily parse, search, and analyze application logs in production.

## Acceptance Criteria
- [ ] All logs output as JSON
- [ ] Request ID included in all log entries
- [ ] Log levels properly used (DEBUG, INFO, WARNING, ERROR)
- [ ] Sensitive data redacted
- [ ] Log format consistent across application
- [ ] Performance logging for slow operations

## Technical Notes
- Use python-json-logger or structlog
- Add correlation IDs (request_id) to all logs
- Include timestamp, level, module, function
- Add custom fields for context
- Configure log levels via environment variable

## Log Entry Format
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "request_id": "abc-123-def",
  "module": "app",
  "function": "send_img",
  "message": "Tracking pixel sent",
  "recipient_uuid": "xyz-789",
  "ip_country": "US",
  "response_time_ms": 45
}
```

## Implementation Areas
1. **Flask App**
   - Configure JSON logging on startup
   - Add request ID middleware
   - Log all requests and responses

2. **Error Handling**
   - Log exceptions with stack traces
   - Include context in error logs

3. **Performance**
   - Log slow queries
   - Log response times

## Definition of Done
- [ ] All logs in JSON format
- [ ] Request IDs working
- [ ] Sensitive data redacted
- [ ] Log aggregation tested (e.g., ELK stack)
- [ ] Documentation updated
- [ ] PR reviewed and approved
