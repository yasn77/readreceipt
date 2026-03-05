# Read Receipt

[![CI](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml/badge.svg)](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yasn77/readreceipt/branch/master/graph/badge.svg)](https://codecov.io/gh/yasn77/readreceipt)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive email read receipt tracking system that enables you to track when recipients open your emails. Built with a Flask backend, React admin dashboard, and browser extensions for seamless integration with Gmail and other webmail services.

## Value Proposition

Read Receipt provides:

- **Real-time Email Tracking** - Know exactly when your emails are opened, by whom, and from where
- **Actionable Analytics** - Gain insights into email engagement patterns with detailed analytics and visualisations
- **Seamless Integration** - Browser extensions automatically inject tracking pixels into your outgoing emails
- **Privacy-Conscious Design** - Minimal permissions, transparent tracking, and full control over your data
- **Self-Hosted Solution** - Complete ownership of your data with no third-party dependencies
- **Enterprise-Ready** - Scalable architecture with Kubernetes support and comprehensive monitoring

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [API Reference](#api-reference)
- [Extension Installation](#extension-installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Read Receipt Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser    │         │   Browser    │         │   Browser    │
│  Extension   │         │  Extension   │         │  Extension   │
│   (Chrome)   │         │  (Firefox)   │         │   (Future)   │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ Inject tracking pixel  │                        │
       │ on email compose       │                        │
       ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Flask Backend                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │   Public   │  │    Admin   │  │ Analytics  │  │  Tracking  │     │
│  │  Endpoints │  │    API     │  │   Endpoints│  │  Endpoint  │     │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  PostgreSQL  │         │   React      │
│  (or SQLite) │         │   Dashboard  │
│  Database    │         │   (Vite)     │
└──────────────┘         └──────────────┘
```

### Component Overview

1. **Browser Extensions** - Chrome and Firefox extensions that automatically inject 1x1 tracking pixels into outgoing emails
2. **Flask Backend** - RESTful API handling tracking events, admin operations, and analytics
3. **Database** - PostgreSQL (production) or SQLite (development) for persisting recipients and tracking data
4. **Admin Dashboard** - React-based single-page application for managing recipients and viewing analytics

### Data Flow

1. User composes an email in Gmail (or other supported webmail)
2. Extension automatically injects a unique tracking pixel (`<img src="server/img/{uuid}" />`)
3. Recipient opens the email, triggering a request to the tracking endpoint
4. Backend logs the event with metadata (IP, user agent, timestamp, country)
5. Analytics are updated and available in the admin dashboard

## Features

- 📧 **Email Tracking** - Track when recipients open your emails via invisible 1x1 tracking pixels
- 🎯 **Gmail Integration** - Browser extension automatically injects tracking into Gmail compose windows
- 📊 **Analytics Dashboard** - Real-time insights with geographic distribution, client breakdown, and time-series data
- 🔐 **Admin Dashboard** - Full recipient management, settings configuration, and data export
- 🔒 **Security First** - Token-based authentication, input validation, SQL injection prevention, CSP headers
- 🌍 **Geographic Tracking** - Country-level location data from email opens
- 📱 **Client Detection** - Identify which email clients recipients use (Gmail, Outlook, Apple Mail, etc.)
- 📈 **Prometheus Metrics** - Monitor application performance and health
- 🧪 **Well Tested** - >90% test coverage with automated CI/CD pipelines
- 🐳 **Docker Ready** - Containerised deployment with Helm charts for Kubernetes

## Quick Start

Get up and running in minutes using mise and uv:

### Prerequisites

- [mise](https://mise.jdx.dev/) - Tool version manager
- Node.js 18 or higher
- PostgreSQL (optional, SQLite for development)
- Chrome or Firefox browser (for extension)

### Quick Setup with mise

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Install mise if you haven't already
curl https://mise.run | sh

# mise will automatically install Python, uv, and all tools
mise install

# Set environment variables
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
export ADMIN_TOKEN=your-secure-token-here

# Install dependencies with uv
mise run install

# Run the application
mise run dev
```

The server will start on `http://localhost:5000` with automatic virtual environment activation.

### Alternative: Manual Setup (without mise)

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install uv package manager
pip install uv

# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
export ADMIN_TOKEN=your-secure-token-here

# Run the application
python app.py
```

### Admin Dashboard Setup

```bash
cd admin-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Browser Extension

See the [Extension Installation Guide](docs/extension-guide.md) for detailed instructions.

## Installation

For comprehensive installation instructions, see the [Getting Started Guide](docs/getting-started.md).

### Backend Installation

```bash
# Clone repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if using Flask-Migrate)
# flask db init  # Only once
# flask db migrate
# flask db upgrade

# Start server
python app.py
```

### Frontend Installation

```bash
cd admin-dashboard

# Install dependencies
npm install

# Build for production
npm run build

# Or run development server
npm run dev
```

### Docker Deployment

```bash
# Build Docker image
docker build -t readreceipt .

# Run container
docker run -d \
  -p 5000:5000 \
  -e ADMIN_TOKEN=your-secure-token \
  -e SQLALCHEMY_DATABASE_URI=postgresql://user:pass@host:5432/readreceipt \
  -v $(pwd)/data:/app/data \
  --name readreceipt \
  readreceipt
```

### Kubernetes Deployment

```bash
# Install using Helm
helm install readreceipt ./helm/readreceipt \
  --set adminToken=your-secure-token \
  --set image.tag=v0.1.3 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=readreceipt.yourdomain.com
```

See [Deployment Guide](docs/deployment.md) for production deployment instructions.

## Development Tasks

This project uses mise for task management. Available tasks:

```bash
# Install all dependencies
mise run install

# Run the application
mise run dev

# Run tests
mise run test

# Run tests with coverage
mise run test-cov

# Lint code
mise run lint

# Format code
mise run format

# Type check
mise run typecheck

# Run pre-commit hooks
mise run precommit

# Clean build artifacts
mise run clean

# Show project info
mise run info

# Serve documentation
mise run docs
```

See `.mise.toml` for the complete list of available tasks.

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///:memory:` | No |
| `ADMIN_TOKEN` | Admin authentication token | `admin` | Yes (change in production) |
| `EXTENSION_ALLOWED_ORIGINS` | Comma-separated allowed domains for extension | `https://mail.google.com` | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `PORT` | Server port | `5000` | No |

Create a `.env` file for local development:

```bash
cp .env.example .env
```

Example `.env` file:

```env
# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/readreceipt

# Security
ADMIN_TOKEN=your-super-secure-token-here

# Extension Configuration
EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.live.com

# Logging
LOG_LEVEL=INFO

# Server
PORT=5000
```

### Database Configuration

**SQLite (Development)**
```env
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

**PostgreSQL (Production)**
```env
SQLALCHEMY_DATABASE_URI=postgresql://username:password@hostname:5432/readreceipt
```

### Extension Configuration

Update `TRACKING_SERVER` in `extensions/chrome/content.js` to point to your server:

```javascript
const TRACKING_SERVER = 'https://readreceipt.yourdomain.com';
```

See [Deployment Guide](docs/deployment.md) for production configuration.

## API Reference

Complete API documentation is available at [docs/api-reference.md](docs/api-reference.md).

### Authentication

Admin endpoints require authentication via the `Authorization` header:

```http
Authorization: Bearer <ADMIN_TOKEN>
```

### Public Endpoints

#### Generate Tracking UUID

```http
GET /new-uuid?description={description}&email={email}
```

Generates a new tracking UUID and optionally creates a recipient record.

**Response:**
```html
<p>550e8400-e29b-41d4-a716-446655440000</p>
description email
```

#### Tracking Pixel Endpoint

```http
GET /img/<uuid>
```

Returns a 1x1 transparent PNG and logs the tracking event.

**Response:** `image/png` (1x1 transparent pixel)

**Headers:**
- `Cache-Control: no-store, no-cache`
- `Pragma: no-cache`
- `Expires: -1`

### Admin Endpoints

#### Login

```http
POST /api/admin/login
Content-Type: application/json

{
  "token": "your-admin-token"
}
```

**Response (200 OK):**
```json
{
  "status": "authenticated"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid token"
}
```

#### List Recipients

```http
GET /api/admin/recipients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "description": "John Doe",
    "email": "john@example.com"
  }
]
```

#### Create Recipient

```http
POST /api/admin/recipients
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "john@example.com",
  "description": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "description": "John Doe",
  "email": "john@example.com"
}
```

#### Update Recipient

```http
PUT /api/admin/recipients/<id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Updated description",
  "email": "newemail@example.com"
}
```

#### Delete Recipient

```http
DELETE /api/admin/recipients/<id>
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "deleted"
}
```

#### Get Dashboard Stats

```http
GET /api/admin/stats
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "total_recipients": 150,
  "total_events": 1250,
  "events_today": 45,
  "unique_opens": 98,
  "recent_events": [
    {
      "email": 1,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Analytics Endpoints

#### Summary Statistics

```http
GET /api/analytics/summary
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "total_events": 1250,
  "unique_recipients": 98,
  "avg_daily_opens": 17.86,
  "top_country": "United States"
}
```

#### Time-Series Events

```http
GET /api/analytics/events?range=7d
Authorization: Bearer <token>
```

**Query Parameters:**
- `range` - Time range (e.g., `7d`, `30d`, `90d`)

**Response (200 OK):**
```json
[
  {"date": "2024-01-10", "count": 15},
  {"date": "2024-01-11", "count": 23},
  {"date": "2024-01-12", "count": 18}
]
```

#### Top Recipients

```http
GET /api/analytics/recipients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {"recipient_id": 1, "count": 45},
  {"recipient_id": 5, "count": 32}
]
```

#### Geographic Distribution

```http
GET /api/analytics/geo
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {"country": "United States", "count": 450},
  {"country": "United Kingdom", "count": 230},
  {"country": "Germany", "count": 180}
]
```

#### Email Client Breakdown

```http
GET /api/analytics/clients
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {"name": "Gmail", "value": 650},
  {"name": "Outlook", "value": 320},
  {"name": "Apple Mail", "value": 180}
]
```

#### Export Analytics

```http
GET /api/analytics/export
Authorization: Bearer <token>
```

**Response:** CSV file download

### Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

## Extension Installation

Detailed installation instructions are available in the [Extension Guide](docs/extension-guide.md).

### Chrome Extension

1. **Open Extensions Page**
   - Navigate to `chrome://extensions/` in Chrome
   - Or click Menu → More tools → Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" in the top right corner

3. **Load Extension**
   - Click "Load unpacked"
   - Select the `extensions/chrome` directory from your cloned repository
   - The extension icon should appear in your toolbar

4. **Configure Extension**
   - Click the extension icon
   - Enter your tracking server URL
   - Toggle tracking on/off as needed

**Screenshot:** *Extension should appear in Chrome toolbar with a receipt icon*

### Firefox Extension

1. **Open Debugging Page**
   - Navigate to `about:debugging` in Firefox
   - Click "This Firefox" in the left sidebar

2. **Load Temporary Add-on**
   - Click "Load Temporary Add-on"
   - Navigate to `extensions/firefox/manifest.json`
   - Select the file to load

3. **Verify Installation**
   - The extension should appear in "Temporary Extensions"
   - Icon should be visible in the toolbar

**Note:** Firefox temporary add-ons persist only until browser restart. For permanent installation, package the extension as an XPI file.

### Supported Email Services

- ✅ Gmail (mail.google.com)
- ✅ Outlook.com (outlook.live.com)
- ✅ Yahoo Mail (mail.yahoo.com)
- ⚠️ Other webmail services (may require custom configuration)

### Troubleshooting Extensions

**Extension not injecting pixels:**
- Ensure you're on a supported domain (e.g., mail.google.com)
- Check browser console for errors (F12 → Console)
- Verify the extension is enabled in `chrome://extensions/`

**Tracking not working:**
- Confirm your server URL is correctly configured
- Check that the server is accessible from your browser
- Verify firewall rules allow outbound requests

See [Extension Guide](docs/extension-guide.md) for comprehensive troubleshooting.

## Troubleshooting

For comprehensive troubleshooting, see [docs/troubleshooting.md](docs/troubleshooting.md).

### Common Issues

**Backend won't start:**
```bash
# Check Python version (requires 3.11+)
python --version

# Verify dependencies are installed
pip install -r requirements.txt

# Check if port is in use
lsof -i :5000
```

**Database errors:**
```bash
# For SQLite, ensure write permissions
chmod 644 db.sqlite3

# For PostgreSQL, verify connection string
# Test connection: psql -h hostname -U username -d readreceipt
```

**Extension not working:**
- Ensure you're on a supported domain (Gmail, Outlook, Yahoo)
- Check browser console for errors (F12)
- Verify extension is enabled and has necessary permissions
- Reload the extension from the extensions page

**Analytics not showing data:**
- Check that tracking events are being logged (server logs)
- Verify the tracking server URL is accessible
- Ensure CORS is properly configured if using different domains

**Admin dashboard login fails:**
- Verify `ADMIN_TOKEN` environment variable is set correctly
- Check browser console for network errors
- Ensure backend server is running and accessible

### Debugging Tips

**Enable debug logging:**
```bash
export LOG_LEVEL=DEBUG
python app.py
```

**Check database contents:**
```bash
# SQLite
sqlite3 db.sqlite3 "SELECT * FROM recipients;"

# PostgreSQL
psql -h hostname -U username -d readreceipt -c "SELECT * FROM recipients;"
```

**Test tracking endpoint:**
```bash
curl -I https://your-server.com/img/test-uuid
```

### Known Issues

- Gmail may cache images, delaying tracking events
- Some email clients block external images by default
- Firefox temporary extensions require reloading after each restart

See [Known Issues](docs/troubleshooting.md#known-issues) for a complete list.

## FAQ

### General Questions

**Q: Is email tracking legal?**
A: Email tracking laws vary by jurisdiction. In many regions, you should inform recipients that emails are tracked. Check local regulations such as GDPR (Europe), CCPA (California), or other privacy laws applicable to your use case.

**Q: How does the tracking work?**
A: The extension injects a 1x1 transparent pixel (tracking image) into outgoing emails. When the recipient opens the email and images load, their email client requests the image from our server, logging the event with metadata (timestamp, IP, user agent, country).

**Q: Can recipients block tracking?**
A: Yes. Recipients can:
- Disable automatic image loading in their email client
- Use privacy extensions that block tracking pixels
- View emails in plain text mode
- Use email clients that proxy images (like Gmail's image proxy)

**Q: Does this work with all email clients?**
A: The tracking works with most email clients that load external images. However:
- Gmail proxies images through their servers (we detect and handle this)
- Some clients block external images by default
- Plain text emails won't display tracking pixels

### Technical Questions

**Q: Can I self-host this?**
A: Yes! This is designed as a self-hosted solution. See the [Deployment Guide](docs/deployment.md) for instructions.

**Q: What database should I use?**
A: SQLite is fine for development and small deployments. For production, we recommend PostgreSQL for better performance and reliability.

**Q: How do I scale this for high volume?**
A: For high-volume deployments:
- Use PostgreSQL with connection pooling
- Deploy behind a load balancer
- Use Redis for caching (future feature)
- Consider horizontal scaling with Kubernetes

**Q: Can I track multiple email accounts?**
A: Yes. The extension works across all tabs and windows. Each tracking pixel is unique, so you can track emails from multiple accounts.

**Q: Is there an API rate limit?**
A: No built-in rate limiting in the current version. For production deployments, consider adding rate limiting via a reverse proxy (nginx, Cloudflare) or application-level middleware.

### Privacy & Security

**Q: What data is collected?**
A: When an email is opened, we collect:
- Timestamp of the open
- IP address (anonymised in some configurations)
- Country (derived from IP)
- User agent (email client information)
- Referrer information

**Q: How long is data retained?**
A: Indefinitely by default. You can implement data retention policies as needed for compliance.

**Q: Is the data encrypted?**
A: Data in transit is encrypted via HTTPS (recommended for production). Data at rest encryption depends on your database configuration.

**Q: Can I export my data?**
A: Yes. Use the `/api/analytics/export` endpoint to download all tracking data as CSV.

### Support

**Q: How do I report a bug?**
A: Please open an issue on the [GitHub repository](https://github.com/yasn77/readreceipt/issues) with detailed reproduction steps.

**Q: Can I contribute?**
A: Absolutely! See the [Contributing Guide](docs/development.md) for instructions.

**Q: Where can I get help?**
A: Check the [Documentation](docs/), open a GitHub issue, or contact the maintainers.

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first-time setup |
| [Architecture](docs/architecture.md) | System design and data flow |
| [Admin Guide](docs/admin-guide.md) | Using the admin dashboard |
| [Extension Guide](docs/extension-guide.md) | Browser extension installation and configuration |
| [API Reference](docs/api-reference.md) | Complete API documentation |
| [Deployment](docs/deployment.md) | Production deployment guide |
| [Development](docs/development.md) | Development environment and contributing |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |

Documentation is also available as a searchable site. Build it with:

```bash
# Install MkDocs and material theme
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

Visit `http://localhost:8000` to view the documentation site.

## Contributing

We welcome contributions! Please see our [Development Guide](docs/development.md) for:

- Setting up a development environment
- Code style guidelines
- Running tests
- Submitting pull requests
- Branch strategy

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run pre-commit hooks (`pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest

# Lint code
ruff check .

# Format code
black .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [React](https://react.dev/) and [Vite](https://vitejs.dev/) - Frontend framework and build tool
- [Recharts](https://recharts.org/) - Analytics visualisation
- [ua-parser](https://github.com/ua-parser) - User agent parsing
- All contributors and supporters

## Security

For security concerns, please contact the maintainers directly rather than opening a public issue.

**Security Features:**
- Token-based authentication for admin endpoints
- Input validation on all endpoints
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention through proper escaping
- Content Security Policy headers
- Minimal extension permissions
- No-cache headers on tracking endpoints

---

**Made with ❤️ by the Read Receipt Team**
