# Changelog

All notable changes to Read Receipt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for Outlook.com email composition
- Support for Yahoo Mail email composition
- CSV export functionality for analytics data
- Geographic distribution analytics
- Email client breakdown analytics
- Time-series analytics with date range selection
- Recent activity feed on dashboard
- Health check endpoint for monitoring

### Changed
- Updated to Manifest V3 for Chrome extensions
- Improved tracking pixel injection performance
- Enhanced error handling in API endpoints
- Updated React to v18.2.0
- Upgraded to Vite v5.0.11

### Fixed
- Database connection timeout issues
- Analytics chart rendering bugs
- Extension not detecting compose windows reliably
- Duplicate tracking events from Gmail image proxy

### Security
- Fixed XSS vulnerability in recipient description
- Improved input validation on all endpoints
- Enhanced CORS configuration

## [0.2.0] - 2024-01-15

### Added
- React-based admin dashboard with modern UI
- Analytics dashboard with visualisations using Recharts
- Browser extensions for Chrome and Firefox
- Automatic tracking pixel injection in Gmail
- Token-based authentication for admin endpoints
- Recipient management (CRUD operations)
- Dashboard statistics and metrics
- Settings configuration page
- Docker support with Dockerfile
- Kubernetes deployment with Helm chart
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite with >90% coverage
- Pre-commit hooks for code quality
- Type hints throughout Python codebase
- Database migrations with Flask-Migrate

### Changed
- Migrated from vanilla JavaScript to React for frontend
- Updated Python dependencies to latest versions
- Improved database schema with proper indexing
- Enhanced logging with structured output
- Updated documentation structure

### Fixed
- Fixed tracking pixel caching issues
- Resolved database locking problems with SQLite
- Fixed extension manifest permissions
- Corrected analytics calculation errors

### Removed
- Deprecated Python 3.10 support (now requires 3.11+)
- Removed legacy frontend code
- Removed unused API endpoints

### Security
- Implemented token-based authentication
- Added input validation on all endpoints
- Enabled SQL injection prevention via ORM
- Added XSS prevention through proper escaping
- Implemented Content Security Policy headers

## [0.1.0] - 2023-06-01

### Added
- Initial release of Read Receipt
- Flask backend with REST API
- Basic tracking pixel functionality
- SQLite database support
- Simple admin interface
- Chrome extension (basic version)
- Email tracking with UUID generation
- Basic analytics endpoints
- User agent parsing
- IP-based country detection
- No-cache headers for tracking pixels

## Version History

| Version | Release Date | Key Features |
|---------|-------------|--------------|
| [0.2.0] | 2024-01-15 | React dashboard, extensions, analytics |
| [0.1.0] | 2023-06-01 | Initial release |

## Migration Guide

### Migrating from 0.1.x to 0.2.0

**Breaking Changes:**
- Python 3.11+ required (Python 3.10 no longer supported)
- Frontend completely rewritten in React
- Extension updated to Manifest V3

**Upgrade Steps:**

1. **Update Python:**
   ```bash
   python --version  # Ensure 3.11+
   ```

2. **Update Dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Run Migrations:**
   ```bash
   flask db upgrade
   ```

4. **Rebuild Frontend:**
   ```bash
   cd admin-dashboard
   npm install
   npm run build
   ```

5. **Reload Extension:**
   - Chrome: Go to `chrome://extensions/` and reload
   - Firefox: Go to `about:debugging` and reload

6. **Update Environment Variables:**
   - Ensure `ADMIN_TOKEN` is set
   - Review new optional variables

### Database Schema Changes

**Version 0.2.0:**
- Added indexes for performance
- Added JSON field for tracking details
- Updated country field type

## Release Notes

### 0.2.0 Highlights

This major update brings a completely redesigned admin dashboard built with React, providing:
- Modern, responsive UI
- Interactive analytics charts
- Improved user experience
- Better performance

The browser extensions have been updated to Manifest V3, ensuring compatibility with latest browser versions.

### Known Issues in 0.2.0

- Firefox extensions are temporary (reload required after browser restart)
- Settings are stored in-memory and reset on server restart
- No bulk import/export for recipients (planned for 0.3.0)

## Upcoming Features

### Planned for 0.3.0

- Bulk recipient import/export
- Persistent settings storage
- Email notifications
- Webhook integrations
- Advanced filtering and search
- Custom date range analytics
- Mobile-responsive dashboard improvements
- Rate limiting on API endpoints
- Redis caching layer
- Advanced user permissions

### Under Consideration

- Multi-user support with roles
- API rate limiting dashboard
- Custom tracking domains
- Email template builder
- Integration with email marketing platforms
- Mobile apps (iOS/Android)
- Browser extension for Safari
- Self-hosted extension distribution

## Contributing

To contribute to Read Receipt:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update this changelog
5. Submit a pull request

See [Development Guide](docs/development.md) for detailed instructions.

## Support

For questions or issues:
- Check the [Documentation](docs/)
- Search [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- Ask in [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)

---

**Latest Version:** 0.2.0  
**Release Date:** January 15, 2024  
**Next Release:** TBD

For the most up-to-date information, check the [GitHub Releases](https://github.com/yasn77/readreceipt/releases) page.
