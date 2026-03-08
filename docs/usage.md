# Usage Guide

This guide provides practical examples and usage patterns for Read Receipt.

## Table of Contents

- [Quick Start (5-Minute Setup)](#quick-start-5-minute-setup)
- [Configuration](#configuration)
- [Tracking Email Opens](#tracking-email-opens)
- [Viewing Analytics](#viewing-analytics)
- [Admin Dashboard](#admin-dashboard)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Quick Start (5-Minute Setup)

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+**: For running the Flask backend
- **Node.js 18+**: For the admin dashboard (optional, but recommended)
- **A web browser**: Chrome or Firefox for the extension
- **git**: For cloning the repository

### Basic Run Command

```bash
# Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Install dependencies
pip install -r requirements.txt

# Set environment variables (required)
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
export ADMIN_TOKEN=your-secure-token

# Run the application
python app.py
```

The server will start on `http://localhost:5000`.

### How to Read Outputs

When you run `python app.py`, you'll see output similar to:

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
```

**What this means:**
- `Running on http://0.0.0.0:5000`: The server is accessible at `http://localhost:5000`
- `Press CTRL+C to quit`: Stop the server by pressing Ctrl+C
- `Debug mode: on`: Changes to code will auto-reload the server

### Where to Find Logs

Logs are printed to the console by default. To save logs to a file:

```bash
# Run with logs saved to file
python app.py > logs/app.log 2>&1
```

To view logs in real-time:

```bash
# Follow logs as they're written
tail -f logs/app.log
```

**Log levels:**
- `INFO`: General informational messages (default)
- `DEBUG`: Detailed debugging information
- `WARNING`: Warning messages
- `ERROR`: Error messages

To change log level:

```bash
export LOG_LEVEL=DEBUG
python app.py
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

**Required Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///db.sqlite3` |
| `ADMIN_TOKEN` | Admin authentication token | `your-secure-random-token` |

**Optional Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `EXTENSION_ALLOWED_ORIGINS` | Allowed domains for extension | `https://mail.google.com` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Server port | `5000` |

### Example .env File

```bash
# Database
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3

# Admin Authentication
ADMIN_TOKEN=your-very-secure-random-token-here

# Extension Settings
EXTENSION_ALLOWED_ORIGINS=https://mail.google.com

# Server Settings
PORT=5000
LOG_LEVEL=INFO
```

---

## Tracking Email Opens

### Using the Browser Extension (Recommended)

The easiest way to track emails is with the browser extension.

#### Installation

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

#### Usage

1. Open Gmail in your browser
2. Compose a new email
3. Click the "Add Tracking" button in the compose toolbar
4. Send your email normally

### Using the API

If you prefer to use the API directly:

#### 1. Generate a Tracking UUID

```bash
curl http://localhost:5000/new-uuid
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. Create a Tracked Email

Include the tracking pixel in your HTML email:

```html
<!DOCTYPE html>
<html>
<body>
  <h1>Hello!</h1>
  <p>This is your email content.</p>

  <!-- Tracking pixel -->
  <img src="http://localhost:5000/img/550e8400-e29b-41d4-a716-446655440000"
       width="1"
       height="1"
       alt=""
       style="display:none;" />

</body>
</html>
```

#### 3. Send the Email

Use your email service (Gmail, Outlook, SendGrid, etc.) to send the HTML email above.

---

## Viewing Analytics

### Using the Admin Dashboard (Recommended)

The admin dashboard provides a visual interface for viewing analytics.

#### Start the Dashboard

```bash
cd admin-dashboard
npm install
npm run dev
```

Open `http://localhost:3000` in your browser and log in with your admin token.

#### What You'll See

- **Overview**: Total emails, opens, and open rate
- **Opens Over Time**: Chart showing opens by date
- **Geographic Distribution**: Map showing opens by country
- **Email Clients**: Breakdown of email clients used
- **Top Recipients**: Most engaged recipients

### Using the API

If you prefer to use the API directly:

#### Get Summary Statistics

```bash
curl http://localhost:5000/api/analytics/summary \
  -H "Authorization: Bearer your-admin-token"
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

#### Get Time-series Data

```bash
curl "http://localhost:5000/api/analytics/events?start=2024-01-01&end=2024-12-31" \
  -H "Authorization: Bearer your-admin-token"
```

#### Get Geographic Distribution

```bash
curl http://localhost:5000/api/analytics/geo \
  -H "Authorization: Bearer your-admin-token"
```

#### Get Email Client Breakdown

```bash
curl http://localhost:5000/api/analytics/clients \
  -H "Authorization: Bearer your-admin-token"
```

---

## Admin Dashboard

### Installation and Setup

```bash
cd admin-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Logging In

1. Open `http://localhost:3000` in your browser
2. Enter your admin token (set via `ADMIN_TOKEN` environment variable)
3. Click "Login"

### Dashboard Features

#### Recipients Management

- **List Recipients**: View all tracked recipients
- **Add Recipient**: Click "Add Recipient" to create a new entry
- **Edit Recipient**: Click the edit icon on a recipient row
- **Delete Recipient**: Click the delete icon on a recipient row

#### Analytics Dashboard

- **Overview Cards**: High-level statistics at a glance
- **Time Series Chart**: Opens over time
- **Geographic Map**: Opens by country
- **Email Clients**: Pie chart showing client breakdown
- **Top Recipients**: Table of most engaged recipients

#### Settings

- **Allowed Origins**: Configure which domains can use the extension
- **Admin Token**: Update authentication token
- **Log Level**: Adjust logging verbosity

### Exporting Data

Export analytics data to CSV:

```bash
curl http://localhost:5000/api/analytics/export?format=csv \
  -H "Authorization: Bearer your-admin-token" \
  -o analytics.csv
```

---

## API Reference

### Authentication

All admin endpoints require authentication via the `Authorization` header:

```bash
Authorization: Bearer your-admin-token
```

### Public Endpoints

#### Generate UUID

Create a new tracking UUID.

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

Record an email open event (returns a 1x1 transparent image).

```http
GET /img/<uuid>
```

### Admin Endpoints

#### Authentication

Verify admin token.

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

Get all recipients.

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

Create a new recipient.

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

Update an existing recipient.

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

Delete a recipient.

```http
DELETE /api/admin/recipients/<id>
Authorization: Bearer your-admin-token
```

#### Dashboard Statistics

Get dashboard statistics.

```http
GET /api/admin/stats
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "total_emails": 100,
  "total_opens": 75,
  "unique_recipients": 50
}
```

### Analytics Endpoints

#### Summary Statistics

Get summary statistics.

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

Get opens over time.

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
    },
    {
      "date": "2024-01-02",
      "opens": 15
    }
  ]
}
```

#### Top Recipients

Get most engaged recipients.

```http
GET /api/analytics/recipients?limit=10
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "recipients": [
    {
      "email": "user@example.com",
      "description": "Test user",
      "opens": 25
    }
  ]
}
```

#### Geographic Distribution

Get opens by country.

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

Get opens by email client.

```http
GET /api/analytics/clients
Authorization: Bearer your-admin-token
```

**Response:**
```json
{
  "clients": [
    {
      "client": "Gmail",
      "count": 40
    },
    {
      "client": "Outlook",
      "count": 25
    },
    {
      "client": "Apple Mail",
      "count": 20
    }
  ]
}
```

#### Export Data

Export analytics data.

```http
GET /api/analytics/export?format=csv
Authorization: Bearer your-admin-token
```

---

## Troubleshooting

### Tracking Not Working

**Symptom**: Email opens are not being tracked.

**Possible Causes:**
1. Tracking pixel URL is incorrect
2. Backend server is not accessible
3. Email client blocks images
4. UUID is invalid

**Solutions:**

1. Verify the tracking URL format: `http://your-domain.com/img/<uuid>`
2. Check if the backend is running:
   ```bash
   curl http://localhost:5000/new-uuid
   ```
3. Test the tracking URL in a browser
4. Ensure the UUID was generated correctly

### Extension Not Loading

**Symptom**: Browser extension doesn't appear or work.

**Possible Causes:**
1. Extension not loaded in developer mode
2. API URL is incorrect
3. CORS issues
4. Browser compatibility

**Solutions:**

1. Enable developer mode and reload extension:
   - Chrome: `chrome://extensions/`
   - Firefox: `about:debugging`
2. Check the API URL in `extensions/chrome/content.js`:
   ```javascript
   const API_BASE_URL = 'http://localhost:5000';
   ```
3. Check the browser console for errors (F12)
4. Verify the backend is running

### Authentication Errors

**Symptom**: API returns 401 Unauthorized.

**Possible Causes:**
1. Invalid admin token
2. Missing Authorization header
3. Token mismatch

**Solutions:**

1. Verify `ADMIN_TOKEN` in environment variables:
   ```bash
   echo $ADMIN_TOKEN
   ```
2. Include the `Authorization` header:
   ```bash
   curl http://localhost:5000/api/admin/stats \
     -H "Authorization: Bearer your-admin-token"
   ```
3. Restart the backend after changing the token

### Database Connection Issues

**Symptom**: Application fails to connect to database.

**Possible Causes:**
1. Database server not running
2. Incorrect connection string
3. Network/firewall issues

**Solutions:**

1. Check if the database is running (PostgreSQL):
   ```bash
   sudo systemctl status postgresql
   ```
2. Verify `SQLALCHEMY_DATABASE_URI` in environment variables
3. Test the connection:
   ```bash
   python -c "from app import app, db; app.app_context().push(); print(db.engine)"
   ```

### CORS Errors

**Symptom**: Browser blocks API requests due to CORS.

**Possible Causes:**
1. Origin not in allowed list
2. CORS not configured

**Solutions:**

1. Add origin to `EXTENSION_ALLOWED_ORIGINS`:
   ```bash
   export EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.com
   ```
2. Restart the backend

### Debug Mode

To see detailed error messages, enable debug mode:

```bash
export LOG_LEVEL=DEBUG
python app.py
```

---

## Best Practices

### Email Content

1. **Place tracking pixel at the end**: Reduces impact on email rendering
2. **Use transparent pixel**: 1x1 GIF or PNG with `style="display:none;"`
3. **Test before sending**: Send test emails to verify tracking works
4. **Comply with regulations**: Inform recipients about tracking where required by law

### Performance

1. **Use CDN**: Serve tracking images via CDN for faster loading in production
2. **Monitor database**: Regular maintenance and indexing
3. **Optimize queries**: Use database indexes for frequent queries

### Security

1. **Use strong tokens**: Generate random, long admin tokens (at least 32 characters)
2. **Use HTTPS**: Always use secure connections in production
3. **Rotate tokens**: Regularly update admin tokens
4. **Limit permissions**: Use least-privilege principle
5. **Audit logs**: Regularly review access logs

### Testing

Before sending important emails:

1. Send a test email to yourself
2. Verify the tracking pixel loads
3. Check the admin dashboard for the open event
4. Confirm analytics are being recorded

---

## Additional Resources

- [Documentation README](docs/README.md) - Comprehensive project documentation
- [Project README](README.md) - Project overview and quick start
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [GitHub Issues](https://github.com/yasn77
