# Story #150: Cookie-Based Own-Open Filtering

## Acceptance Criteria

- [x] 1. Set 'rr_ignore_me' cookie when user views sent folder
- [x] 2. Tracking endpoint checks for cookie
- [x] 3. If cookie present, don't record tracking event
- [x] 4. Add toggle in UI to enable/disable
- [x] 5. Tests verify cookie filtering works

## Implementation Details

### Backend Changes (app.py)

1. **Modified `/img/<uuid>` endpoint**:
   - Check for `rr_ignore_me` cookie in request
   - Skip tracking event recording if cookie is present
   - Log when tracking is skipped due to cookie

2. **Added `/api/cookie/set` endpoint**:
   - POST endpoint to set the `rr_ignore_me` cookie
   - Cookie expires after 30 days
   - Secure, httponly, samesite=Lax for security

3. **Added `/api/cookie/clear` endpoint**:
   - POST endpoint to clear the `rr_ignore_me` cookie
   - Sets cookie with max_age=0 to expire immediately

4. **Updated `/api/admin/settings` endpoint**:
   - Added `cookie_filtering_enabled` field
   - Controlled by `COOKIE_FILTERING_ENABLED` environment variable

### Frontend Changes (admin-dashboard/src/pages/Settings.jsx)

1. **Added cookie filtering toggle**:
   - Checkbox to enable/disable cookie-based filtering
   - Calls `/api/cookie/set` when enabled
   - Calls `/api/cookie/clear` when disabled
   - Shows user-friendly message about the feature

2. **Added explanatory text**:
   - Help text explaining what the feature does
   - Clarifies it prevents false positives from own opens

### Tests (tests/test_readreceipt.py)

Added `TestCookieBasedFiltering` class with tests for:
- Tracking is skipped when cookie is present
- Tracking is recorded when cookie is absent
- `/api/cookie/set` endpoint functionality
- `/api/cookie/clear` endpoint functionality
- Settings endpoint includes cookie filtering option

## Files Modified

- `app.py` - Backend tracking and cookie endpoints
- `admin-dashboard/src/pages/Settings.jsx` - UI toggle
- `tests/test_readreceipt.py` - Test coverage

## Usage

1. Admin logs into dashboard
2. Navigates to Settings page
3. Enables "Ignore my own opens" toggle
4. When viewing sent folder in email client, cookie is set
5. Tracking pixels loaded with cookie present are ignored
6. No false positive tracking events recorded

## Security Considerations

- Cookie is httponly (not accessible via JavaScript)
- Cookie is secure (only sent over HTTPS)
- Cookie uses samesite=Lax to prevent CSRF
- Cookie expires after 30 days (auto-renewal via UI)
- No sensitive data stored in cookie value

## Environment Variables

- `COOKIE_FILTERING_ENABLED` - Enable/disable feature globally (default: "true")

## Related Issues

- Issue #149: Browser Extension-based filtering
- Issue #151: IP-based filtering
- Spike #119: Own-open filtering research
