# Security Fixes Documentation

## Overview

This document details the two critical security fixes implemented in the Read Receipt application:

1. **CSRF Protection Enforcement** - Issue #101
2. **Cookie-Based Authentication** - Issue #101 (localStorage replacement)

---

## Critical Issue #1: CSRF Protection Not Enforced

### Problem
Line 122 in `app.py` had `app.config["WTF_CSRF_CHECK_DEFAULT"] = False`, which disabled CSRF protection on all state-changing endpoints.

### Solution

#### Backend Changes (`app.py`)

1. **Enabled CSRF Protection by Default**
   ```python
   app.config["WTF_CSRF_CHECK_DEFAULT"] = True  # Was False
   ```

2. **Configured CSRF Header Support**
   ```python
   app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken", "X-CSRF-Token"]
   ```

3. **Exempted Login Endpoint**
   - Login is exempt from CSRF (`@csrf.exempt`) as it's token-based authentication with no prior session
   - This is the correct pattern for initial authentication endpoints

4. **All State-Changing Endpoints Protected**
   - POST, PUT, DELETE endpoints now require CSRF tokens
   - CSRF tokens can be provided via:
     - `X-CSRFToken` header
     - `X-CSRF-Token` header

### Testing

- Added `TestCSRFProtection` class in `tests/test_security.py`
- Tests verify CSRF is enabled and properly configured
- Login endpoint correctly exempt from CSRF

---

## Critical Issue #2: localStorage Still Used for Tokens

### Problem
Frontend stored JWT tokens in localStorage, making them vulnerable to XSS attacks. Any malicious script could steal authentication tokens.

### Solution

#### Backend Changes (`app.py`)

1. **Login Endpoint - Sets httpOnly Cookie**
   ```python
   response = make_response(jsonify({"status": "authenticated", ...}))
   response.set_cookie(
       'auth_token',
       jwt_token,
       httponly=True,      # JavaScript cannot access
       secure=True,        # Only sent over HTTPS
       samesite='Strict',  # Prevents CSRF
       max_age=86400,      # 24 hours
       path='/'
   )
   ```

2. **Logout Endpoint - Clears Cookie**
   ```python
   response = make_response(jsonify({"status": "logged out"}))
   response.delete_cookie('auth_token', path='/')
   ```

3. **Token Refresh - Sets New Cookie**
   - Returns new httpOnly cookie instead of token in body

4. **Authentication Decorator - Checks Cookie First**
   ```python
   def require_auth(view):
       # Check cookie first (preferred)
       token = request.cookies.get("auth_token")
       
       # Fall back to Authorization header
       if not token:
           auth_header = request.headers.get("Authorization")
           # ... extract token from header
   ```

#### Frontend Changes (`admin-dashboard/src/`)

1. **API Module (`api/api.js`)**
   - Configured axios with `withCredentials: true`
   - Removed all localStorage calls for tokens
   - Added CSRF token header support for state-changing requests
   - Logout now calls backend endpoint instead of just clearing localStorage

2. **Login Page (`pages/Login.jsx`)**
   - Removed `setStoredToken()` call
   - Relies on backend setting httpOnly cookie

3. **App Component (`App.jsx`)**
   - Removed `getStoredToken()` check
   - Checks authentication via API call (cookies sent automatically)

4. **All Pages (Dashboard, Recipients, Settings, Analytics)**
   - Updated logout to call `adminApi.logout()` backend endpoint
   - Removed direct `clearAuth()` calls

### Security Benefits

| Aspect | Before (localStorage) | After (httpOnly Cookies) |
|--------|----------------------|--------------------------|
| XSS Token Theft | ✅ Possible | ❌ Impossible |
| CSRF Protection | Manual | Automatic (SameSite=Strict) |
| HTTPS Enforcement | Manual | Automatic (Secure flag) |
| JavaScript Access | ✅ Full access | ❌ No access |

### Cookie Configuration

```
auth_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=86400
```

- **HttpOnly**: Prevents JavaScript access (XSS protection)
- **Secure**: Only sent over HTTPS (man-in-the-middle protection)
- **SameSite=Strict**: Prevents cross-site request forgery
- **Path=/**: Available to all endpoints
- **Max-Age=86400**: 24-hour expiration (configurable via JWT_TOKEN_EXPIRY_HOURS)

---

## Testing

### Running Tests

```bash
# All tests
mise run test

# Security tests only
mise run test -- tests/test_security.py -v

# Cookie authentication tests
mise run test -- tests/test_security.py::TestCookieBasedAuthentication -v

# CSRF protection tests
mise run test -- tests/test_security.py::TestCSRFProtection -v
```

### Test Coverage

New test classes added:
- `TestCSRFProtection` - 3 tests
- `TestCookieBasedAuthentication` - 6 tests

Key tests:
- ✅ `test_csrf_protection_enabled` - Verifies CSRF is enabled
- ✅ `test_login_sets_auth_cookie` - Verifies httpOnly, Secure, SameSite flags
- ✅ `test_login_does_not_return_token_in_body` - Verifies token not in response
- ✅ `test_auth_cookie_used_for_authentication` - Verifies cookie-based auth works
- ✅ `test_logout_clears_auth_cookie` - Verifies logout clears cookie
- ✅ `test_token_refresh_sets_new_cookie` - Verifies refresh sets new cookie

---

## Migration Notes

### For API Clients

If you have API clients using the Authorization header, they will continue to work. The `require_auth` decorator checks:
1. Cookie first (preferred for browser clients)
2. Authorization header (for API clients, mobile apps, etc.)

### For Browser Extension

The Chrome/Firefox extensions will need to:
1. Update to send `withCredentials: true` in requests
2. Expect cookies instead of tokens in responses
3. Include CSRF tokens in state-changing requests

---

## Security Headers

All responses include these security headers:

```
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
```

---

## Compliance

These fixes address:
- **OWASP Top 10 2021 - A01: Broken Access Control** - Proper authentication
- **OWASP Top 10 2021 - A02: Cryptographic Failures** - Secure token storage
- **OWASP Top 10 2021 - A03: Injection** - CSRF protection
- **OWASP Top 10 2021 - A07: Identification and Authentication Failures** - Session management

---

## Future Improvements

1. **Redis-backed Token Blacklist** - Currently in-memory, should use Redis for production
2. **Refresh Token Rotation** - Implement rotating refresh tokens for enhanced security
3. **CSRF Token per Session** - Generate unique CSRF tokens per user session
4. **Cookie Domain Restriction** - Set explicit domain for cookies in production

---

## References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [MDN HttpOnly Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/stable/csrf.html)
