# Read Receipt

[![CI](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml/badge.svg)](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yasn77/readreceipt/branch/master/graph/badge.svg)](https://codecov.io/gh/yasn77/readreceipt)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive email read receipt tracking system with a Flask backend, React admin dashboard, and browser extensions for Gmail and other webmail services.

**📚 [Documentation](docs/)** | **📘 [Usage Guide](docs/usage.md)** | **🤝 [Contributing](CONTRIBUTING.md)** | **📋 [Code of Conduct](CODE_OF_CONDUCT.md)**

## Features

- 📧 **Email Tracking** - Track when recipients open your emails via invisible tracking pixels
- 🎯 **Gmail Integration** - Browser extension automatically injects tracking into Gmail compose
- 📊 **Analytics Dashboard** - Real-time insights into email engagement
- 🔐 **Admin Dashboard** - Manage recipients and configure settings
- 🔒 **Security First** - Minimal permissions, CSP headers, input validation
- 📈 **Prometheus Metrics** - Monitor application performance
- 🧪 **Well Tested** - >90% test coverage

## Quick Start

### Prerequisites

- [mise](https://mise.jdx.dev/) - Development environment manager
- Chrome or Firefox browser

### Installation

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Install mise (if not already installed)
curl https://mise.run | sh

# Install tools and dependencies with mise
mise install
```

This will:
- Install Python 3.11 and Node.js 20
- Set up a virtual environment using `uv`
- Install all Python dependencies
- Install all frontend dependencies

### Development

```bash
# Start the backend development server
mise run dev

# In another terminal, start the admin dashboard
mise run dev-frontend
```

The backend will be available at `http://localhost:5000` and the dashboard at `http://localhost:3000`.

### Available mise Tasks

- `mise run install` - Install all dependencies (backend + frontend)
- `mise run dev` - Run backend development server
- `mise run dev-frontend` - Run frontend development server
- `mise run test` - Run tests with pytest
- `mise run lint` - Run linters (ruff, black, mypy)
- `mise run format` - Format code with black
- `mise run build` - Build frontend (admin-dashboard)
- `mise run clean` - Clean build artifacts and cache
- `mise run hooks` - Run pre-commit hooks
- `mise run security` - Run security scans (bandit, safety)
- `mise run ci` - Run full CI pipeline (lint + test + build)

### Browser Extension

#### Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extensions/chrome` directory
5. The extension icon should appear in your toolbar

#### Firefox

1. Open Firefox and navigate to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `extensions/firefox/manifest.json`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///:memory:` |
| `ADMIN_TOKEN` | Admin authentication token | `admin` |
| `EXTENSION_ALLOWED_ORIGINS` | Comma-separated allowed domains | `https://mail.google.com` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Server port | `5000` |

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

## API Endpoints

### Public Endpoints

- `GET /` - Root endpoint (returns empty)
- `GET /new-uuid` - Generate new tracking UUID
- `GET /img/<uuid>` - Tracking pixel endpoint

### Admin Endpoints

- `POST /api/admin/login` - Admin authentication
- `GET /api/admin/recipients` - List recipients
- `POST /api/admin/recipients` - Create recipient
- `PUT /api/admin/recipients/<id>` - Update recipient
- `DELETE /api/admin/recipients/<id>` - Delete recipient
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/settings` - Get settings
- `PUT /api/admin/settings` - Update settings

### Analytics Endpoints

- `GET /api/analytics/summary` - Summary statistics
- `GET /api/analytics/events` - Time-series event data
- `GET /api/analytics/recipients` - Top recipients
- `GET /api/analytics/geo` - Geographic distribution
- `GET /api/analytics/clients` - Email client breakdown
- `GET /api/analytics/export` - Export CSV

## Testing

### Backend Tests

```bash
# Run all tests with coverage (using mise)
mise run test

# Or directly with pytest
pytest

# Run specific test file
pytest tests/test_readreceipt.py -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd admin-dashboard

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

### Quick Commands

```bash
# Run all linters
mise run lint

# Format code
mise run format

# Run pre-commit hooks
mise run hooks

# Run security scans
mise run security
```

## Project Structure

```
readreceipt/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Python tool configuration
├── manifest.json         # Chrome extension manifest
├── content.js            # Extension content script
├── background.js         # Extension background worker
├── admin-dashboard/      # React admin UI
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/
│   └── package.json
├── tests/                # Test suite
│   └── test_readreceipt.py
├── stories/              # Agile user stories
├── .github/workflows/    # CI/CD pipelines
└── helm/                 # Kubernetes deployment
```

## Deployment

### Docker

```bash
# Build image
docker build -t readreceipt .

# Run container
docker run -p 5000:5000 -e ADMIN_TOKEN=your-token readreceipt
```

### Kubernetes (Helm)

```bash
# Install chart
helm install readreceipt ./helm --set adminToken=your-token
```

## Security

- All admin endpoints require authentication
- Input validation on all endpoints
- SQL injection prevention via ORM
- XSS prevention
- Content Security Policy headers
- Minimal extension permissions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes with sign-off (`git commit -s -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines and [docs/](docs/) for comprehensive documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask framework
- React and Vite
- Recharts for analytics
- All contributors
