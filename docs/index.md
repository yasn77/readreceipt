# Read Receipt Documentation

Welcome to the Read Receipt documentation! This comprehensive guide will help you set up, configure, and use the Read Receipt email tracking system.

## What is Read Receipt?

Read Receipt is a self-hosted email tracking system that enables you to monitor when recipients open your emails. It consists of:

- **Browser Extensions** for Chrome and Firefox that automatically inject tracking pixels
- **Flask Backend** API that handles tracking events and analytics
- **React Admin Dashboard** for managing recipients and viewing insights

## Quick Links

### Getting Started

- **[Getting Started Guide](getting-started.md)** - Installation and first-time setup
- **[Quick Start](#quick-start)** - Get up and running in 5 minutes
- **[Architecture Overview](architecture.md)** - System design and components

### User Guides

- **[Admin Dashboard Guide](admin-guide.md)** - Using the web interface
- **[Extension Guide](extension-guide.md)** - Browser extension installation
- **[API Reference](api-reference.md)** - Complete API documentation

### Deployment

- **[Deployment Guide](deployment.md)** - Production deployment options
- **[Docker Deployment](deployment.md#docker-deployment)** - Container setup
- **[Kubernetes Deployment](deployment.md#kubernetes-deployment)** - K8s/Helm setup

### Development

- **[Development Guide](development.md)** - Setting up dev environment
- **[Logging Configuration](logging.md)** - Structured logging setup
- **[Contributing](development.md#contributing-process)** - How to contribute
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Quick Start

Get Read Receipt running in 5 minutes:

### 1. Clone Repository

```bash
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
```

### 2. Setup Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ADMIN_TOKEN=dev-token-123
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3

# Start server
python app.py
```

### 3. Setup Frontend

```bash
cd admin-dashboard
npm install
npm run dev
```

### 4. Install Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extensions/chrome` folder

### 5. Start Using

1. Navigate to `http://localhost:3000`
2. Login with token: `dev-token-123`
3. Compose an email in Gmail
4. Track opens in the dashboard

## Features

### 📧 Email Tracking

Track when recipients open your emails with invisible 1x1 tracking pixels. Get real-time notifications and detailed analytics.

### 🎯 Gmail Integration

Browser extensions automatically inject tracking pixels into your Gmail compose windows. No manual intervention required.

### 📊 Analytics Dashboard

Comprehensive analytics including:
- Open rates over time
- Geographic distribution
- Email client breakdown
- Top engaged recipients

### 🔐 Self-Hosted

Complete control over your data. Host on your own infrastructure with no third-party dependencies.

### 🔒 Privacy-Focused

Minimal data collection, transparent tracking, and full compliance with privacy regulations.

### 🌍 Geographic Tracking

Know where your emails are being opened with country-level location data.

### 📱 Client Detection

Identify which email clients your recipients use (Gmail, Outlook, Apple Mail, etc.).

## System Requirements

### Backend

- Python 3.11 or higher
- PostgreSQL 12+ (or SQLite for development)
- 2GB RAM minimum
- 10GB storage

### Frontend

- Node.js 18 or higher
- Modern web browser (Chrome, Firefox, Edge)

### Browser Extension

- Chrome 88+ or Firefox 85+
- Access to Gmail, Outlook.com, or Yahoo Mail

## Documentation Structure

```
docs/
├── architecture.md          # System architecture and design
├── getting-started.md       # Installation and setup
├── admin-guide.md           # Admin dashboard usage
├── extension-guide.md       # Browser extension guide
├── api-reference.md         # Complete API documentation
├── deployment.md            # Production deployment
├── development.md           # Development guide
└── troubleshooting.md       # Common issues
```

## Support

### Getting Help

- **Documentation:** Browse the docs in this site
- **GitHub Issues:** [Report bugs or request features](https://github.com/yasn77/readreceipt/issues)
- **GitHub Discussions:** [Ask questions and discuss](https://github.com/yasn77/readreceipt/discussions)

### Community

- Join our community discussions
- Contribute to the project
- Share your use cases

### Professional Support

For enterprise deployments and professional support, contact the maintainers.

## Contributing

We welcome contributions! See our [Development Guide](development.md) for:

- Setting up a development environment
- Code style guidelines
- Running tests
- Submitting pull requests

### Quick Contribution

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

Read Receipt is licensed under the [MIT License](https://github.com/yasn77/readreceipt/blob/master/LICENSE).

## Changelog

See our [Changelog](changelog.md) for version history and release notes.

## Stay Updated

- ⭐ Star the repository on GitHub
- 🔔 Watch for releases
- 📢 Follow project announcements

---

**Ready to get started?** Check out the [Getting Started Guide](getting-started.md) or jump into the [Quick Start](#quick-start) above.

**Need help?** See our [Troubleshooting Guide](troubleshooting.md) or open an issue on GitHub.
