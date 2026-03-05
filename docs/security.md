# Security Documentation

This document outlines the security measures implemented in the Read Receipt application.

## Table of Contents

- [Security Headers](#security-headers)
- [Content Security Policy (CSP)](#content-security-policy)
- [Cross-Origin Resource Sharing (CORS)](#cross-origin-resource-sharing)
- [Rate Limiting](#rate-limiting)
- [Input Validation and Sanitisation](#input-validation-and-sanitisation)
- [Extension Security](#extension-security)
- [Best Practices](#best-practices)

## Security Headers

All HTTP responses include the following security headers via the `@app.after_request` decorator:

### Header Summary

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | See [CSP section](#content-security-policy) | Prevents XSS and data injection attacks |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Enforces HTTPS for 1 year |
| `X-Frame-Options` | `DENY` | Prevents clickjacking attacks |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filtering (legacy) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer information |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=()` | Restricts browser features |

### Implementation

```python
@app.after_request
def add_security_headers(response: Any) -> Any:
    """Add security headers to all responses."""
    response.headers["Content-Security-Policy"] = "default-src 'self'; ..."
    response.headers["Strict-Transport-Security"] = "max-age=31536000; ..."
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), ..."
    return response
```

## Content Security Policy

The CSP policy restricts resource loading to prevent XSS and data injection attacks:

```
default-src 'self'
script-src 'self'
style-src 'self' 'unsafe-inline'
img-src 'self' data: https:
font-src 'self'
connect-src 'self'
frame-ancestors 'none'
base-uri 'self'
form-action 'self'
```

### Policy Breakdown

- `default-src 'self'`: Only load resources from the same origin
- `script-src 'self'`: Only execute scripts from the same origin (no inline scripts)
- `style-src 'self' 'unsafe-inline'`: Allow styles from same origin and inline styles (required for some functionality)
- `img-src 'self' data: https:`: Allow images from same origin, data URIs, and HTTPS sources
- `frame-ancestors 'none'`: Prevent the page from being embedded in frames
- `base-uri 'self'`: Prevent base tag injection attacks
- `form-action 'self'`: Only allow form submissions to the same origin

## Cross-Origin Resource Sharing

CORS is configured to restrict API access to authorised origins only:

```python
allowed_origins = os.environ.get(
    "EXTENSION_ALLOWED_ORIGINS", "https://mail.google.com"
).split(",")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)
```

### Configuration

- **Environment Variable**: `EXTENSION_ALLOWED_ORIGINS`
- **Default**: `https://mail.google.com`
- **Format**: Comma-separated list of allowed origins
- **Example**: `EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.live.com`

## Rate Limiting

Rate limiting is implemented using Flask-Limiter to prevent brute-force and DoS attacks:

### Rate Limits by Endpoint Type

| Endpoint Type | Rate Limit | Endpoints |
|--------------|------------|-----------|
| Login | 5 per minute | `/api/admin/login` |
| Admin | 30 per minute | `/api/admin/*` |
| Analytics (Public) | 60 per minute | `/api/analytics/*` |
| Default | 120 per minute | All other endpoints |

### Implementation

```python
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)

@app.route("/api/admin/login", methods=["POST"])
@limiter.limit("5 per minute")
def admin_login() -> Any:
    ...
```

### Configuration

- **Storage**: In-memory (use Redis for production)
- **Key Function**: Remote IP address
- **Default Limit**: 120 requests per minute

## Input Validation and Sanitisation

All user inputs are validated and sanitised to prevent injection attacks:

### Validation Rules

1. **Email Validation**
   - Required for recipient creation
   - Maximum length: 254 characters
   - Format: RFC 5322 compliant regex pattern
   - Sanitised with bleach

2. **Description Validation**
   - Maximum length: 200 characters
   - Must be string type
   - Sanitised with bleach

3. **Token Validation**
   - Maximum length: 256 characters
   - Must be string type
   - Sanitised with bleach

4. **Settings Validation**
   - Only allowed keys: `tracking_enabled`, `log_level`
   - Type checking for each setting
   - Log level restricted to valid values

### Sanitisation

All string inputs are sanitised using the `bleach` library:

```python
import bleach

# Clean HTML tags and attributes
email = bleach.clean(email, tags=[], strip=True)
description = bleach.clean(description, tags=[], strip=True)
```

## Extension Security

### Content Security Policy

Browser extension manifests include CSP directives:

**Manifest V3 (Chrome/Edge):**
```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; style-src 'self'; img-src 'self' data: https:; connect-src 'self' https://mail.google.com"
  }
}
```

**Manifest V2 (Firefox):**
```json
{
  "content_security_policy": "script-src 'self'; object-src 'self'; style-src 'self'; img-src 'self' data: https:; connect-src 'self' https://mail.google.com"
}
```

### Permissions

The extension requests minimal permissions:

- `tabs`: Access browser tabs for webmail integration
- `storage`: Store configuration locally
- `activeTab`: Access the active tab when user interacts

### Host Permissions

Restricted to specific webmail domains:

- `https://mail.google.com/*`
- `https://outlook.live.com/*`
- `https://*.yahoo.com/*`

## Best Practices

### For Developers

1. **Never disable security headers** - All headers serve a purpose
2. **Use environment variables** for sensitive configuration
3. **Validate all inputs** - Never trust user input
4. **Use parameterised queries** - SQLAlchemy ORM handles this
5. **Keep dependencies updated** - Use `uv update` regularly
6. **Run security tests** - Include security tests in CI/CD

### For Administrators

1. **Change default tokens** - Set `ADMIN_TOKEN` in production
2. **Configure CORS properly** - Only allow trusted origins
3. **Use HTTPS** - HSTS is enabled but requires HTTPS
4. **Monitor rate limits** - Adjust based on traffic patterns
5. **Review logs regularly** - Check for suspicious activity
6. **Backup data** - Regular database backups

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADMIN_TOKEN` | Admin authentication token | `admin` | Yes (change in production) |
| `EXTENSION_ALLOWED_ORIGINS` | CORS allowed origins | `https://mail.google.com` | Yes |
| `SECRET_KEY` | Flask secret key | Random | Yes (set in production) |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `RETRY_MAX_ATTEMPTS` | Database retry attempts | `5` | No |

## Security Testing

Run security tests with:

```bash
python -m pytest tests/ -v -k security
```

### Test Coverage

- Security headers presence
- CORS configuration
- Rate limiting enforcement
- Input validation
- XSS prevention
- SQL injection prevention

## Incident Response

In case of a security incident:

1. **Identify** - Review logs for suspicious activity
2. **Contain** - Block suspicious IPs, rotate tokens
3. **Eradicate** - Fix the vulnerability
4. **Recover** - Restore from backup if needed
5. **Document** - Record the incident and lessons learned

## Compliance

This application follows security best practices aligned with:

- OWASP Top 10
- CWE/SANS Top 25
- NIST Cybersecurity Framework

## Contact

For security concerns, please report through the project's security policy.
