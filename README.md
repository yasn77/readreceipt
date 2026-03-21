# Read Receipt

[![CI](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml/badge.svg)](https://github.com/yasn77/readreceipt/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yasn77/readreceipt/branch/master/graph/badge.svg)](https://codecov.io/gh/yasn77/readreceipt)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive email read receipt tracking system with a Flask backend, React admin dashboard, and browser extensions for Gmail and other webmail services.

**📚 [Documentation](docs/)** | **📘 [Usage Guide](docs/usage.md)** | **🐳 [Docker Guide](DOCKER.md)** | **🤝 [Contributing](CONTRIBUTING.md)** | **📋 [Code of Conduct](CODE_OF_CONDUCT.md)**

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
├── src/                          # Source code
│   └── readreceipt/
│       ├── app.py               # Flask application
│       ├── auth/                # Authentication modules
│       ├── security/            # Security utilities
│       └── utils/               # Utility functions
├── admin-dashboard/              # React admin UI
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/
│   └── package.json
├── migrations/                   # Database migrations
├── tests/                        # Test suite
├── extensions/                   # Browser extensions
│   ├── chrome/                  # Chrome extension
│   └── firefox/                 # Firefox extension
├── helm/                         # Kubernetes deployment
├── .github/workflows/            # CI/CD pipelines
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Docker Compose configuration
├── docker-entrypoint.sh          # Container entrypoint script
├── .dockerignore                 # Docker build exclusions
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Python tool configuration
└── README.md                     # This file
```

## Deployment

### Docker

ReadReceipt provides a comprehensive Docker setup with multi-stage builds for optimized production images.

#### Quick Start with Docker

```bash
# Build the Docker image
docker build -t readreceipt:latest .

# Run with Docker (minimal setup)
docker run -d \
  --name readreceipt \
  -p 8000:8000 \
  -e ADMIN_TOKEN=your-secure-token \
  -e SQLALCHEMY_DATABASE_URI=sqlite:////app/data/readreceipt.db \
  -v readreceipt-data:/app/data \
  readreceipt:latest
```

#### Docker Compose (Recommended)

The easiest way to run ReadReceipt is with Docker Compose:

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings (especially ADMIN_TOKEN)
nano .env

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_TOKEN` | Admin authentication token (required) | `change-me-in-production` |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:////app/data/readreceipt.db` |
| `EXTENSION_ALLOWED_ORIGINS` | Comma-separated allowed domains | `https://mail.google.com,https://outlook.live.com` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `PORT` | Server port | `8000` |
| `FLASK_ENV` | Flask environment | `production` |

#### Docker Build Stages

The Dockerfile uses multi-stage builds for optimization:

1. **frontend-builder**: Builds the React admin dashboard
2. **python-deps**: Installs Python dependencies
3. **production**: Final image combining backend and frontend

To build a specific stage:

```bash
# Build only the frontend
docker build --target frontend-builder -t readreceipt-frontend .

# Build only Python dependencies
docker build --target python-deps -t readreceipt-deps .
```

#### Production Deployment

For production deployments:

```bash
# Use PostgreSQL instead of SQLite (uncomment in docker-compose.yml)
# Set secure credentials
docker-compose up -d

# Scale the application (if using an external database)
docker-compose up -d --scale readreceipt=3
```

#### Health Checks

The Docker image includes a health check endpoint:

```bash
# Check application health
curl http://localhost:8000/health
```

#### Volume Persistence

Data is persisted using Docker volumes:

- `readreceipt-data`: SQLite database and application data
- Mount point: `/app/data`

To backup data:

```bash
# Create backup
docker run --rm -v readreceipt-data:/data -v $(pwd):/backup alpine tar czf /backup/readreceipt-backup.tar.gz -C /data .

# Restore backup
docker run --rm -v readreceipt-data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/readreceipt-backup.tar.gz"
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
