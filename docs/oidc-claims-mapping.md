# OIDC Claims to Admin Roles Mapping

This document describes the implementation of OpenID Connect (OIDC) authentication with claims-based role mapping for the ReadReceipt admin dashboard.

## Overview

The system now supports:
- **OIDC Authentication**: Secure authentication via external identity providers (Authelia, Keycloak, Google, etc.)
- **Claims Mapping**: Automatic mapping of OIDC claims to admin roles
- **Role-Based Access Control (RBAC)**: Granular permissions based on roles
- **Audit Logging**: Complete audit trail of admin actions and role changes
- **Backward Compatibility**: Legacy token authentication still supported

## Configuration

### Environment Variables

Set these environment variables to configure OIDC:

```bash
# OIDC Provider Configuration
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_DISCOVERY_URL=https://auth.example.com/.well-known/openid-configuration

# Access Control
OIDC_ALLOWED_EMAILS=admin@example.com,superuser@example.com
OIDC_ADMIN_ROLES=admin,superuser

# Optional: Force OIDC-only mode (disable token auth)
OIDC_ONLY=true

# Required: Session secret key
SECRET_KEY=your-secret-key-change-in-production
```

### Claims Mapping Logic

The system maps OIDC claims to admin roles in the following order:

1. **Explicit Role Claims**: Checks the `roles` claim for admin roles
2. **Group Claims**: Maps common group names to roles:
   - `admins`, `administrators`, `admin-group` → `admin` role
   - `superusers`, `super-admins` → `superuser` role
3. **Email Whitelist**: Users in `OIDC_ALLOWED_EMAILS` automatically get `admin` role

## Database Schema

### AdminUser Table

Stores admin users with their mapped roles:

```python
class AdminUser:
    id: int              # Primary key
    email: str           # User email (unique)
    oidc_sub: str        # OIDC subject (unique)
    roles: list          # JSON list of roles
    is_active: bool      # Account status
    created_at: datetime # Creation timestamp
    updated_at: datetime # Last update
    last_login: datetime # Last login time
```

### AuditLog Table

Tracks all admin actions and role changes:

```python
class AuditLog:
    id: int              # Primary key
    admin_user_id: int   # Reference to AdminUser
    action: str          # Action type (login, role_added, etc.)
    details: dict        # Additional context
    ip_address: str      # Client IP
    user_agent: str      # Client user agent
    timestamp: datetime  # Event timestamp
```

## API Endpoints

### Authentication

#### POST /api/auth/login
Initiates OIDC authentication flow. Redirects to identity provider.

#### GET /api/auth/callback
Handles OIDC callback. Creates/updates admin user from claims.

#### POST /api/auth/logout
Logs out user and clears session.

#### GET /api/auth/me
Returns current authenticated user information.

**Response:**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "roles": ["admin", "superuser"],
    "is_active": true,
    "created_at": "2026-03-07T20:00:00Z",
    "last_login": "2026-03-07T21:00:00Z"
  }
}
```

### Admin User Management

All endpoints require admin authentication.

#### GET /api/admin/users
List all admin users.

**Response:**
```json
{
  "users": [...],
  "total": 5
}
```

#### GET /api/admin/users/:id
Get a specific admin user.

#### PUT /api/admin/users/:id/roles
Update admin user roles.

**Request:**
```json
{
  "roles": ["admin", "superuser"]
}
```

**Response:**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "roles": ["admin", "superuser"],
  "is_active": true,
  ...
}
```

#### POST /api/admin/users/:id/activate
Activate an admin user.

#### POST /api/admin/users/:id/deactivate
Deactivate an admin user (cannot deactivate last admin).

### Audit Logs

#### GET /api/admin/audit-logs
Get audit logs with optional filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 50)
- `action`: Filter by action type
- `user_id`: Filter by user ID

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "admin_user_id": 1,
      "admin_email": "admin@example.com",
      "action": "login",
      "details": {},
      "ip_address": "192.168.1.1",
      "timestamp": "2026-03-07T20:00:00Z"
    }
  ],
  "total": 100,
  "pages": 2,
  "current_page": 1,
  "per_page": 50
}
```

## Audit Actions

The system logs the following actions:

- `login` - User logged in successfully
- `logout` - User logged out
- `login_denied` - Login attempt failed
- `user_created` - New admin user created from OIDC
- `roles_added` - Roles automatically added from OIDC claims
- `roles_removed` - Roles automatically removed from OIDC claims
- `roles_added_by_admin` - Roles manually added by admin
- `roles_removed_by_admin` - Roles manually removed by admin
- `user_activated` - User account activated
- `user_deactivated` - User account deactivated
- `token_login` - Legacy token authentication used

## Migration

Run the database migration to create the new tables:

```bash
# Using Flask-Migrate
flask db upgrade

# Or manually apply the migration
python -m flask db migrate -m "Add admin user and audit log tables"
python -m flask db upgrade
```

## Security Considerations

1. **Always use HTTPS** in production to protect OIDC tokens
2. **Set a strong SECRET_KEY** - never use the default
3. **Configure OIDC_ALLOWED_EMAILS** to restrict access to known users
4. **Enable OIDC_ONLY mode** in production to disable legacy token auth
5. **Regularly audit** the audit logs for suspicious activity
6. **Rotate OIDC_CLIENT_SECRET** periodically

## Example Identity Provider Configurations

### Authelia

```yaml
# Authelia configuration
identity_providers:
  oidc:
    clients:
      - client_id: readreceipt
        client_name: ReadReceipt Admin
        client_secret: SECRET
        redirect_uris:
          - https://readreceipt.example.com/api/auth/callback
        scopes:
          - openid
          - email
          - profile
        userinfo_signed_response_alg: none
```

### Keycloak

1. Create a new client in Keycloak
2. Set redirect URI to `https://your-domain.com/api/auth/callback`
3. Configure mappers to include roles in token:
   - Add `groups` mapper
   - Add `realm roles` mapper
4. Set client ID and secret in environment variables

### Google

```bash
OIDC_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
OIDC_ALLOWED_EMAILS=admin@yourdomain.com
```

## Testing

Run the test suite to verify OIDC functionality:

```bash
python -m pytest tests/test_oidc_claims.py -v
```

## Troubleshooting

### "Email not in allowed list"

- Check `OIDC_ALLOWED_EMAILS` environment variable
- Ensure email matches exactly (case-sensitive)

### "User does not have admin roles"

- Verify OIDC provider is sending role claims
- Check `OIDC_ADMIN_ROLES` configuration
- Review identity provider group mappings

### Audit logs not being created

- Ensure database migration has been run
- Check database connection
- Verify SQLAlchemy is properly configured

## Backward Compatibility

The system maintains backward compatibility with legacy token authentication:

- Existing `ADMIN_TOKEN` continues to work
- Token auth can be disabled with `OIDC_ONLY=true`
- All admin endpoints now work with both auth methods

## Future Enhancements

- [ ] Support for custom claim mappings via configuration
- [ ] Role hierarchies and inheritance
- [ ] Fine-grained permissions per endpoint
- [ ] Multi-factor authentication (MFA) integration
- [ ] Session management and timeout controls
- [ ] IP-based access restrictions
