# Read Receipt Documentation

Welcome to the Read Receipt documentation. This section contains comprehensive guides for using, configuring, and developing with Read Receipt.

## 📚 Table of Contents

- [Project Overview](#project-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Security](#security)
- [Contributing](#contributing)

---

## Project Overview

**Read Receipt** is a comprehensive email read receipt tracking system that helps you track when recipients open your emails. It consists of:

- **Flask Backend**: RESTful API for tracking, analytics, and administration
- **React Admin Dashboard**: Real-time insights into email engagement
- **Browser Extensions**: Chrome and Firefox extensions for Gmail integration

### Key Features

- 📧 **Email Tracking**: Track email opens via invisible tracking pixels
- 🎯 **Gmail Integration**: Browser extension automatically injects tracking into Gmail compose
- 📊 **Analytics Dashboard**: Real-time insights with charts and metrics
- 🔐 **Admin Dashboard**: Manage recipients and configure settings
- 🔒 **Security First**: Minimal permissions, CSP headers, input validation
- 📈 **Prometheus Metrics**: Monitor application performance
- 🧪 **Well Tested**: >90% test coverage

### Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Browser       │         │   Flask Backend  │
│   Extension     │────────▶│   (app.py)       │
│                 │         └────────┬─────────┘
└─────────────────┘                  │
                                    │
                          ┌─────────▼─────────┐
                          │   PostgreSQL /    │
                          │   SQLite Database │
                          └───────────────────┘
                                    ▲
                          ┌─────────┴─────────┐
                          │   React Admin     │
                          │   Dashboard       │
                          └───────────────────┘
```

---

## Quick Start

Get Read Receipt running in under 5 minutes:

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
export ADMIN_TOKEN=your-secure-token

# Run the application
python app.py
```

The server will start on `http://localhost:5000`.

### 2. Admin Dashboard Setup

```bash
cd admin-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### 3. Install Browser Extension

**Chrome:**
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extensions/chrome` directory

**Firefox:**
1. Open Firefox and navigate to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `extensions/firefox/manifest.json`

### 4. Test It Out

1. Open Gmail in your browser
2. Compose a new email
3. Click the "Add Tracking" button in the compose window
4. Send the email
5. Check the admin dashboard to see when it's opened

---

## Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Database**: PostgreSQL (production) or SQLite (development)
- **Browser**: Chrome or Firefox

### Backend Installation

#### Using pip

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Using mise (recommended)

```bash
# Install mise
curl https://mise.run | sh

# Install Python
mise use python@3.11

# Install dependencies
pip install -r requirements.txt
```

### Frontend Installation

```bash
cd admin-dashboard

# Using npm
npm install

# Using mise
mise use node@20
npm install
```

### Database Setup

#### SQLite (Development)

No additional setup required. The database will be created automatically.

```bash
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

#### PostgreSQL (Production)

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql  # macOS

# Create database
sudo -u postgres createdb readreceipt

# Set environment variables
export SQLALCHEMY_DATABASE_URI=postgresql://postgres:password@localhost/readreceipt
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

#### Required Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `postgresql://user:pass@localhost/db` | `sqlite:///:memory:` |
| `ADMIN_TOKEN` | Admin authentication token | `your-secure-random-token` | `admin` |

#### Optional Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `EXTENSION_ALLOWED_ORIGINS` | Comma-separated allowed domains | `https://mail.google.com,https://outlook.com` | `https://mail.google.com` |
| `LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `PORT` | Server port | `5000` | `5000` |
| `SECRET_KEY` | Flask secret key | `your-secret-key` | Auto-generated |

### Example .env File

```bash
# Database
SQLALCHEMY_DATABASE_URI=postgresql://postgres:securepassword@localhost/readreceipt

# Admin Authentication
ADMIN_TOKEN=your-very-secure-random-token-here

# Extension Settings
EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.com

# Server Settings
PORT=5000
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
```

### Flask Configuration

Additional Flask configuration can be set in `app.py`:

```python
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
```

---

## Usage Guide

For detailed usage instructions and code examples, see the [Usage Guide](usage.md).

### Quick Examples

#### Generate a Tracking UUID

```bash
curl http://localhost:5000/new-uuid
```

Response:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Track Email Opens

Include the tracking pixel in your HTML emails:

```html
<img src="http://your-domain.com/img/550e8400-e29b-41d4-a716-446655440000" width="1" height="1" alt="" />
```

#### View Analytics

```bash
curl http://localhost:5000/api/analytics/summary \
  -H "Authorization: Bearer your-admin-token"
```

---

## Development Setup

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up Node environment
cd admin-dashboard
npm install
cd ..

# Install pre-commit hooks
pre-commit install

# Run database migrations
flask db upgrade
```

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd admin-dashboard
npm test

# All tests with coverage
pytest --cov=app --cov-fail-under=90
```

### Code Quality Tools

```bash
# Lint Python code
ruff check .

# Format Python code
black .

# Type check
mypy .

# Lint JavaScript
cd admin-dashboard
npm run lint
```

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

---

## API Documentation

### Authentication

All admin endpoints require authentication via the `Authorization` header:

```bash
Authorization: Bearer your-admin-token
```

### Public Endpoints

#### Generate UUID

```http
GET /new-uuid
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Tracking Pixel

```http
GET /img/<uuid>
```

This endpoint returns a 1x1 transparent pixel and records the email open event.

### Admin Endpoints

#### Authentication

```http
POST /api/admin/login
Content-Type: application/json

{
  "token": "your-admin-token"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authenticated"
}
```

#### List Recipients

```http
GET /api/admin/recipients
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "recipients": [
    {
      "id": 1,
      "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "description": "Test user"
    }
  ]
}
```

#### Create Recipient

```http
POST /api/admin/recipients
Authorization: Bearer your-admin-token
Content-Type: application/json

{
  "email": "user@example.com",
  "description": "Test user"
}
```

#### Update Recipient

```http
PUT /api/admin/recipients/<id>
Authorization: Bearer your-admin-token
Content-Type: application/json

{
  "email": "newemail@example.com",
  "description": "Updated description"
}
```

#### Delete Recipient

```http
DELETE /api/admin/recipients/<id>
Authorization: Bearer your-admin-token
```

#### Dashboard Statistics

```http
GET /api/admin/stats
Authorization: Bearer your-admin-token
```

### Analytics Endpoints

#### Summary Statistics

```http
GET /api/analytics/summary
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "total_emails": 100,
  "total_opens": 75,
  "unique_recipients": 50,
  "open_rate": 0.75
}
```

#### Time-series Event Data

```http
GET /api/analytics/events?start=2024-01-01&end=2024-12-31
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "events": [
    {
      "date": "2024-01-01",
      "opens": 10
    }
  ]
}
```

#### Top Recipients

```http
GET /api/analytics/recipients?limit=10
Authorization: Bearer your-admin-token
```

#### Geographic Distribution

```http
GET /api/analytics/geo
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "countries": [
    {
      "country": "US",
      "count": 50
    },
    {
      "country": "GB",
      "count": 25
    }
  ]
}
```

#### Email Client Breakdown

```http
GET /api/analytics/clients
Authorization: Bearer your-admin-token
```

#### Export Data

```http
GET /api/analytics/export?format=csv
Authorization: Bearer your-admin-token
```

---

## Deployment

### Docker Deployment

#### Build Image

```bash
docker build -t readreceipt:latest .
```

#### Run Container

```bash
docker run -d \
  --name readreceipt \
  -p 5000:5000 \
  -e SQLALCHEMY_DATABASE_URI=postgresql://postgres:password@db/readreceipt \
  -e ADMIN_TOKEN=your-secure-token \
  readreceipt:latest
```

#### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SQLALCHEMY_DATABASE_URI=postgresql://postgres:password@db/readreceipt
      - ADMIN_TOKEN=your-secure-token
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=readreceipt
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes Deployment (Helm)

#### Install Chart

```bash
# Add repository
helm repo add readreceipt https://charts.readreceipt.io

# Install chart
helm install readreceipt ./helm \
  --set adminToken=your-secure-token \
  --set database.host=postgres.example.com \
  --set database.password=your-db-password
```

#### Configuration

```yaml
# values.yaml
adminToken: your-secure-token
database:
  host: postgres.example.com
  port: 5432
  name: readreceipt
  user: postgres
  password: your-db-password

ingress:
  enabled: true
  hosts:
    - host: readreceipt.example.com
      paths:
        - path: /
          pathType: Prefix
```

### Production Checklist

- [ ] Set strong `ADMIN_TOKEN`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up backups
- [ ] Configure monitoring (Prometheus)
- [ ] Set up logging aggregation
- [ ] Review and harden security settings
- [ ] Run security audit
- [ ] Set up CI/CD pipeline

---

## Security

### Security Features

- **Authentication**: Admin endpoints require token-based authentication
- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Prevention**: Uses SQLAlchemy ORM
- **XSS Prevention**: Content Security Policy headers
- **Minimal Permissions**: Browser extension uses minimal permissions
- **Secure Headers**: Includes security headers (CSP, X-Frame-Options, etc.)

### Best Practices

1. **Use Strong Tokens**: Generate random, long admin tokens
2. **Enable HTTPS**: Always use TLS in production
3. **Rotate Secrets**: Regularly rotate admin tokens and database passwords
4. **Monitor Logs**: Review access logs for suspicious activity
5. **Keep Updated**: Keep dependencies updated
6. **Limit Access**: Use firewall rules to limit access
7. **Backup Regularly**: Implement regular database backups

### Vulnerability Reporting

If you discover a security vulnerability, please:

1. **Do not create a public issue**
2. Email security@example.com with details
3. Include steps to reproduce
4. Allow time for fix before disclosure

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

### Quick Summary

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Ensure >90% coverage
6. Submit a Pull Request

### Code of Conduct

Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md).

---

## Additional Resources

- [GitHub Repository](https://github.com/yasn77/readreceipt)
- [Issue Tracker](https://github.com/yasn77/readreceipt/issues)
- [API Documentation](#api-documentation)
- [Usage Guide](usage.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)
- **Email**: support@example.com

---

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
