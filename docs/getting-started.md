# Getting Started

This guide will help you get Read Receipt up and running in your environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Installation](#backend-installation)
- [Frontend Installation](#frontend-installation)
- [Extension Installation](#extension-installation)
- [Configuration](#configuration)
- [First-Time Setup](#first-time-setup)
- [Quick Start Guide](#quick-start-guide)
- [Next Steps](#next-steps)

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Python** | 3.11+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | Frontend build | [nodejs.org](https://nodejs.org/) |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/) |
| **Browser** | Chrome/Firefox | Extension host | [chrome.com](https://google.com/chrome) or [firefox.com](https://mozilla.org/firefox) |

### Optional Software

| Software | Purpose | When Needed |
|----------|---------|-------------|
| **PostgreSQL** | Production database | Production deployments |
| **Docker** | Containerisation | Container-based deployments |
| **Helm** | Kubernetes package manager | Kubernetes deployments |

### Verify Prerequisites

```bash
# Check Python version (must be 3.11 or higher)
python --version
# Output: Python 3.11.0

# Check Node.js version (must be 18 or higher)
node --version
# Output: v18.0.0

# Check npm version
npm --version
# Output: 9.0.0

# Check Git
git --version
# Output: git version 2.x.x
```

## Backend Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
```

### Step 2: Create Virtual Environment

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
```
Collecting Flask==3.0.0
Collecting Flask-SQLAlchemy==3.1.1
Collecting Flask-Migrate==4.0.5
...
Successfully installed Flask-3.0.0 Flask-SQLAlchemy-3.1.1 ...
```

### Step 4: Initialise Database

**For SQLite (development):**
```bash
# Database is created automatically on first run
python app.py
```

**For PostgreSQL (production):**
```bash
# Create database
createdb readreceipt

# Or using psql
psql -U postgres -c "CREATE DATABASE readreceipt;"

# Set environment variable
export SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/readreceipt
```

### Step 5: Run Database Migrations

```bash
# Initialise migrations (only once)
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

### Step 6: Start Backend Server

```bash
# Development server
python app.py

# Or with Flask CLI
flask run --host=0.0.0.0 --port=5000
```

**Verify:** Open `http://localhost:5000` in your browser. You should see a blank page (root endpoint returns empty).

## Frontend Installation

### Step 1: Navigate to Admin Dashboard

```bash
cd admin-dashboard
```

### Step 2: Install Dependencies

```bash
npm install
```

**Expected output:**
```
added 450 packages, and audited 451 packages in 30s
...
found 0 vulnerabilities
```

### Step 3: Configure API URL

Edit `admin-dashboard/src/api/api.js` if your backend is not on `localhost:5000`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api'  // Update if needed
```

**Note:** The frontend uses relative paths by default, expecting to be served from the same domain as the backend.

### Step 4: Start Development Server

```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.11  ready in 250 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**Verify:** Open `http://localhost:3000` in your browser. You should see the login page.

### Step 5: Build for Production

```bash
npm run build
```

This creates optimised static files in `admin-dashboard/dist/`.

**Serve with Flask:**
Copy the built files to Flask's static directory or configure Flask to serve them.

## Extension Installation

### Chrome Extension

1. **Open Extensions Page**
   ```
   chrome://extensions/
   ```

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top right

3. **Load Extension**
   - Click "Load unpacked"
   - Navigate to `extensions/chrome` in your cloned repository
   - Click "Select Folder"

4. **Verify Installation**
   - Extension icon should appear in toolbar
   - You may need to pin it (click puzzle piece icon → pin extension)

**Screenshot location:** *Screenshot of Chrome extensions page with Read Receipt loaded*

### Firefox Extension

1. **Open Debugging Page**
   ```
   about:debugging
   ```

2. **Select "This Firefox"**
   - Click in the left sidebar

3. **Load Temporary Add-on**
   - Click "Load Temporary Add-on"
   - Navigate to `extensions/firefox/manifest.json`
   - Click "Open"

4. **Verify Installation**
   - Extension appears under "Temporary Extensions"
   - Icon visible in toolbar

**Note:** Firefox temporary add-ons are removed when the browser closes. For permanent installation, see [Extension Guide](extension-guide.md).

### Configure Extension

1. **Click Extension Icon**
   - Opens popup configuration

2. **Set Tracking Server URL**
   - Enter your backend URL (e.g., `http://localhost:5000`)

3. **Toggle Tracking**
   - Enable/disable tracking as needed

**Screenshot location:** *Screenshot of extension popup showing configuration options*

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example
cp .env.example .env  # If it exists

# Or create manually
touch .env
```

### Basic Configuration

```env
# Database Configuration
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
# For PostgreSQL:
# SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/readreceipt

# Admin Authentication (CHANGE THIS IN PRODUCTION!)
ADMIN_TOKEN=your-super-secure-token-here

# Extension Configuration
EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.live.com

# Logging
LOG_LEVEL=INFO

# Server
PORT=5000
```

### Production Configuration

```env
# Use PostgreSQL
SQLALCHEMY_DATABASE_URI=postgresql://user:strong-password@db-host:5432/readreceipt

# Strong admin token (generate with: openssl rand -hex 32)
ADMIN_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Enable all email providers
EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.live.com,https://mail.yahoo.com

# Production logging
LOG_LEVEL=WARNING

# Standard HTTPS port (requires root or reverse proxy)
PORT=443
```

### Update Extension Configuration

Edit `extensions/chrome/content.js`:

```javascript
// Update this to match your server URL
const TRACKING_SERVER = 'https://readreceipt.yourdomain.com';
```

Edit `extensions/firefox/content.js` similarly.

## First-Time Setup

### 1. Start Backend

```bash
cd /path/to/readreceipt
source venv/bin/activate  # Activate virtual environment
export ADMIN_TOKEN=your-token
python app.py
```

### 2. Start Frontend (Development)

```bash
cd admin-dashboard
npm run dev
```

### 3. Login to Admin Dashboard

1. Navigate to `http://localhost:3000/login`
2. Enter your `ADMIN_TOKEN`
3. Click "Login"

**Screenshot location:** *Screenshot of login page with token entered*

### 4. Create First Recipient

1. Navigate to "Recipients" tab
2. Click "Add Recipient"
3. Enter email and description
4. Click "Save"

**Screenshot location:** *Screenshot of recipient creation form*

### 5. Test Tracking

1. Open Gmail in a new tab
2. Compose a new email
3. Extension should automatically inject tracking pixel
4. Send email to a test address
5. Open the email
6. Check analytics dashboard for the event

**Screenshot location:** *Screenshot of analytics dashboard showing test event*

## Quick Start Guide

### Complete Setup in 5 Minutes

```bash
# 1. Clone and setup backend
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables
export ADMIN_TOKEN=dev-token-123
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3

# 3. Start backend
python app.py &

# 4. Setup frontend
cd admin-dashboard
npm install
npm run dev &

# 5. Load Chrome extension
# - Go to chrome://extensions/
# - Enable Developer Mode
# - Load unpacked → select extensions/chrome
```

### Test the System

```bash
# Generate a test UUID
curl "http://localhost:5000/new-uuid?description=Test&email=test@example.com"

# Test tracking endpoint
curl -I "http://localhost:5000/img/<uuid-from-above>"

# Login to admin (use with your token)
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"token": "dev-token-123"}'
```

### Verify Everything Works

- ✅ Backend running on `http://localhost:5000`
- ✅ Frontend running on `http://localhost:3000`
- ✅ Extension loaded in browser
- ✅ Can login to admin dashboard
- ✅ Can create recipients
- ✅ Tracking events are logged

## Troubleshooting Installation

### Backend Issues

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
export PORT=5001
```

**Database errors:**
```bash
# Remove SQLite database and recreate
rm db.sqlite3
python app.py  # Database recreated automatically
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**npm install fails:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Vite build errors:**
```bash
# Check Node.js version (must be 18+)
node --version

# Update Node.js if needed
```

### Extension Issues

**Extension not loading:**
- Check `manifest.json` for syntax errors
- Ensure all referenced files exist
- Check browser console for errors

**Extension not injecting pixels:**
- Verify you're on Gmail (mail.google.com)
- Check extension is enabled
- Reload extension from extensions page
- Check browser console for errors

## Next Steps

- [Architecture Overview](architecture.md) - Understand system design
- [Admin Guide](admin-guide.md) - Learn to use the dashboard
- [Extension Guide](extension-guide.md) - Detailed extension configuration
- [API Reference](api-reference.md) - API documentation
- [Deployment Guide](deployment.md) - Production deployment

## Getting Help

- **Documentation:** Check other docs in this directory
- **Issues:** [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)

---

**Ready to start tracking?** Proceed to the [Admin Guide](admin-guide.md) to learn how to use the dashboard.
