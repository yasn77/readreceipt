# Security Documentation

This document describes the security measures implemented in the ReadReceipt application as part of Epic #111 (DevSecOps Code-Level Security Remediation).

## Implemented Security Controls

### 1. Security Headers (Issue #106)

All HTTP responses include the following security headers:

- **Content-Security-Policy (CSP)**: Restricts resource loading to prevent XSS attacks
  - `default-src 'self'`
  - `frame-ancestors 'none'` (prevents clickjacking)
  - `base-uri 'self'`, `form-action 'self'`

- **X-Frame-Options**: `DENY` - Prevents clickjacking attacks

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing

- **Strict-Transport-Security (HSTS)**: Enforces HTTPS with `max-age=31536000; includeSubDomains; preload`

- **X-XSS-Protection**: `1; mode=block` - Legacy XSS filter

- **Referrer-Policy**: `strict-origin-when-cross-origin` - Controls referrer information

- **Permissions-Policy**: Disables unnecessary browser features (geolocation, microphone, camera, etc.)

### 2. Rate Limiting (Issue #105)

Rate limits are enforced to prevent DoS and abuse:

- **Default limits**: 1000 requests per day, 100 per hour
- **Tracking endpoint** (`/img/<uuid>`): 30 requests per minute
- **Admin login** (`/api/admin/login`): 5 requests per minute
- **All admin endpoints**: Stricter rate limiting applied

Configuration supports Redis for distributed rate limiting (set `REDIS_URL` environment variable).

### 3. Input Validation and Sanitization (Issue #107)

All user inputs are validated and sanitized:

- **Email validation**: RFC 5322 compliant pattern matching, max 254 characters
- **Description fields**: HTML stripped using `bleach`, max 500 characters
- **JSON payloads**: Maximum 100KB request size
- **HTTP headers**: Maximum 1024 characters per header value
- **User-Agent**: Truncated to 512 characters
- **Query parameters**: Sanitized and length-bounded
- **Range parameters**: Validated format (`\d+d`), limited to 1-365 days

### 4. Hardened Logging (Issue #108)

Logging is configured to prevent sensitive data leakage:

- **Automatic redaction** of sensitive patterns:
  - Passwords and credentials
  - API keys and tokens
  - Bearer tokens
  - Email addresses
  - IP addresses in request details

- **Safe headers logging**: Excludes `Authorization`, `Cookie`, `X-API-Key`, etc.

- **SensitiveDataFilter**: Applied to all log handlers

- **Access logs**: IP addresses and sensitive request data not stored in application logs

### 5. IAM/Roles and Audit Logging (Issue #109)

Role-based access control with comprehensive audit trail:

- **Admin authentication**: Required for all `/api/admin/*` and `/api/analytics/*` endpoints

- **Token-based auth**: Bearer token or cookie-based authentication

- **Role verification**: Checks for `admin` role before allowing access

- **Audit logging** for all admin actions:
  - Admin login attempts (success/failure)
  - Recipient CRUD operations (create, update, delete)
  - Settings changes
  - Analytics exports

- **Audit log format**:
  ```json
  {
    "timestamp": "ISO 8601 timestamp",
    "action": "function name",
    "user_token": "partial token for traceability",
    "remote_addr": "client IP",
    "endpoint": "API path",
    "method": "HTTP method",
    "details": "action-specific details"
  }
  ```

### 6. CI Security Hardening (Issue #110)

Automated security scanning in CI/CD pipeline:

- **Dependency scanning**: Weekly scans with `safety` to detect vulnerable dependencies
- **Static code analysis**: `bandit` security scanner on all Python code
- **Container scanning**: `Trivy` filesystem scans for vulnerabilities
- **Dependency review**: PR-level dependency review with license checks
- **Scheduled scans**: Weekly full security scans (Sundays at 00:00 UTC)

## Security Configuration

### Environment Variables

```bash
# Admin authentication
ADMIN_TOKEN=<strong_random_token>

# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:password@host/dbname

# Rate limiting (optional, uses memory by default)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Secret key for sessions
SECRET_KEY=<strong_random_secret>

# Extension allowed origins
EXTENSION_ALLOWED_ORIGINS=https://your-extension-id.chrome.extension
```

## Security Best Practices

### Deployment

1. **Use HTTPS**: Always deploy behind HTTPS with valid TLS certificates
2. **Set strong ADMIN_TOKEN**: Use a cryptographically secure random token
3. **Configure Redis**: For production deployments, use Redis for rate limiting
4. **Monitor logs**: Set up alerting for failed admin login attempts
5. **Regular updates**: Keep dependencies updated via Renovate or Dependabot

### Development

1. **Never commit secrets**: Use environment variables or secret management tools
2. **Run security scans locally**: `safety check`, `bandit -r .`
3. **Test authentication**: Ensure admin endpoints are properly protected
4. **Review audit logs**: Check audit trail in staging environments

## Compliance Notes

These security measures align with:

- **OWASP Top 10**: Addresses injection, broken authentication, sensitive data exposure, XSS
- **CIS Benchmarks**: Security headers, access control principles
- **GDPR**: Data minimization in logging, PII redaction

## Related Issues

- #105: Rate limiting implementation
- #106: Security headers
- #107: Input validation
- #108: Log hardening
- #109: IAM/Roles and audit logging
- #110: CI security scanning
- #111: Epic - DevSecOps Code-Level Security Remediation

## Security Testing

To verify security controls:

```bash
# Check security headers
curl -I https://your-domain.com/img/test-uuid

# Test rate limiting
for i in {1..40}; do curl -s https://your-domain.com/img/test-uuid; done

# Test admin authentication
curl -X POST https://your-domain.com/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"token": "wrong"}'

# Run local security scans
safety check -r requirements.txt
bandit -r app.py security.py
```
