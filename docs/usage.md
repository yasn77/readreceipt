# Usage Guide

This guide provides practical examples and usage patterns for Read Receipt.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Browser Extension](#browser-extension)
- [API Usage](#api-usage)
- [Admin Dashboard](#admin-dashboard)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)

---

## Basic Usage

### Getting Started with Email Tracking

The simplest way to track emails is to use the browser extension with Gmail.

#### Step 1: Install the Browser Extension

See the [Quick Start](README.md#quick-start) guide for installation instructions.

#### Step 2: Compose an Email in Gmail

1. Open Gmail
2. Click "Compose"
3. Write your email as usual

#### Step 3: Add Tracking

Click the "Add Tracking" button in the compose toolbar. A tracking pixel will be automatically inserted into your email.

#### Step 4: Send and Monitor

Send your email. When the recipient opens it, the tracking pixel will load and record the open event. You can view this in the admin dashboard.

---

## Browser Extension

### Gmail Integration

The browser extension integrates seamlessly with Gmail's compose interface.

#### Features

- **One-click tracking**: Add tracking with a single button click
- **Automatic UUID generation**: No manual UUID management needed
- **Visual indicator**: See which emails have tracking enabled
- **Multiple recipients**: Track opens from each recipient separately

#### Using the Extension

1. **Compose Email**: Open Gmail and start composing
2. **Enable Tracking**: Click the "Add Tracking" button
3. **Customize (optional)**: Add a description to identify the recipient
4. **Send**: Send your email normally

#### Extension Settings

The extension uses the following configuration:

```javascript
// Extension configuration
const config = {
  apiUrl: 'http://localhost:5000',  // Backend API URL
  allowedOrigins: ['https://mail.google.com'],
  autoTrack: true  // Automatically track all emails
};
```

### Custom Extension Configuration

To configure the extension for your own backend:

1. Open `extensions/chrome/content.js` (or Firefox equivalent)
2. Modify the `API_BASE_URL` constant:

```javascript
const API_BASE_URL = 'https://your-domain.com';
```

3. Reload the extension

---

## API Usage

### Generating Tracking UUIDs

Before you can track emails, you need a unique tracking UUID.

#### cURL Example

```bash
curl http://localhost:5000/new-uuid
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Python Example

```python
import requests

# Generate UUID
response = requests.get('http://localhost:5000/new-uuid')
uuid = response.json()['uuid']

print(f"Tracking UUID: {uuid}")
```

#### JavaScript Example

```javascript
const response = await fetch('http://localhost:5000/new-uuid');
const data = await response.json();
const uuid = data.uuid;

console.log(`Tracking UUID: ${uuid}`);
```

---

### Creating Recipients

Associate a UUID with a recipient email for better tracking.

#### cURL Example

```bash
curl -X POST http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "description": "John Doe - Sales Lead"
  }'
```

**Response:**
```json
{
  "id": 1,
  "r_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "description": "John Doe - Sales Lead"
}
```

#### Python Example

```python
import requests

# Create recipient
response = requests.post(
    'http://localhost:5000/api/admin/recipients',
    headers={
        'Authorization': 'Bearer your-admin-token',
        'Content-Type': 'application/json'
    },
    json={
        'email': 'user@example.com',
        'description': 'John Doe - Sales Lead'
    }
)

recipient = response.json()
print(f"Created recipient: {recipient['email']}")
```

---

### Tracking Email Opens

#### HTML Email Integration

Include the tracking pixel in your HTML emails:

```html
<!DOCTYPE html>
<html>
<body>
  <h1>Hello!</h1>
  <p>This is your email content.</p>

  <!-- Tracking pixel (1x1 transparent image) -->
  <img src="http://your-domain.com/img/550e8400-e29b-41d4-a716-446655440000"
       width="1"
       height="1"
       alt=""
       style="display:none;" />

</body>
</html>
```

#### Plain Text Email Integration

For plain text emails, include the tracking URL:

```
Hello!

This is your email content.

Track this email at: http://your-domain.com/img/550e8400-e29b-41d4-a716-446655440000
```

#### Python Email Example

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_tracked_email(sender, recipient, subject, body, tracking_uuid):
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    # HTML version with tracking pixel
    html_content = f"""
    <html>
    <body>
        {body}
        <img src="http://your-domain.com/img/{tracking_uuid}"
             width="1" height="1" alt="" style="display:none;" />
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, 'html'))

    # Send email
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('username', 'password')
        server.send_message(msg)

# Usage
send_tracked_email(
    sender='you@example.com',
    recipient='user@example.com',
    subject='Important Update',
    body='<h1>Hello!</h1><p>This is important.</p>',
    tracking_uuid='550e8400-e29b-41d4-a716-446655440000'
)
```

#### Node.js Email Example

```javascript
const nodemailer = require('nodemailer');

async function sendTrackedEmail(options) {
  const transporter = nodemailer.createTransport({
    host: 'smtp.example.com',
    port: 587,
    secure: false,
    auth: {
      user: 'username',
      pass: 'password'
    }
  });

  const html = `
    <html>
    <body>
      ${options.body}
      <img src="http://your-domain.com/img/${options.trackingUuid}"
           width="1" height="1" alt="" style="display:none;" />
    </body>
    </html>
  `;

  await transporter.sendMail({
    from: options.from,
    to: options.to,
    subject: options.subject,
    html: html
  });
}

// Usage
sendTrackedEmail({
  from: 'you@example.com',
  to: 'user@example.com',
  subject: 'Important Update',
  body: '<h1>Hello!</h1><p>This is important.</p>',
  trackingUuid: '550e8400-e29b-41d4-a716-446655440000'
});
```

---

### Viewing Analytics

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

**Response:**
```json
{
  "events": [
    {"date": "2024-01-01", "opens": 10},
    {"date": "2024-01-02", "opens": 15},
    {"date": "2024-01-03", "opens": 8}
  ]
}
```

#### Get Geographic Distribution

```bash
curl http://localhost:5000/api/analytics/geo \
  -H "Authorization: Bearer your-admin-token"
```

**Response:**
```json
{
  "countries": [
    {"country": "US", "count": 50},
    {"country": "GB", "count": 25},
    {"country": "DE", "count": 15}
  ]
}
```

#### Get Email Client Breakdown

```bash
curl http://localhost:5000/api/analytics/clients \
  -H "Authorization: Bearer your-admin-token"
```

**Response:**
```json
{
  "clients": [
    {"client": "Gmail", "count": 40},
    {"client": "Outlook", "count": 25},
    {"client": "Apple Mail", "count": 20}
  ]
}
```

---

## Admin Dashboard

### Accessing the Dashboard

1. Start the admin dashboard:

```bash
cd admin-dashboard
npm run dev
```

2. Open `http://localhost:3000` in your browser

3. Log in with your admin token

### Dashboard Features

#### Recipients Management

- **List Recipients**: View all tracked recipients
- **Add Recipient**: Create new recipient entries
- **Edit Recipient**: Update recipient details
- **Delete Recipient**: Remove recipients

#### Analytics Dashboard

- **Overview**: High-level statistics
- **Opens Over Time**: Time-series chart
- **Geographic Distribution**: Map view
- **Email Clients**: Breakdown by client
- **Top Recipients**: Most engaged recipients

#### Settings

- **Allowed Origins**: Configure extension origins
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

## Advanced Patterns

### Batch Email Tracking

Track multiple emails efficiently:

```python
import requests

API_BASE = 'http://localhost:5000'
ADMIN_TOKEN = 'your-admin-token'

def send_batch_emails(recipients):
    results = []
    for recipient in recipients:
        # Generate UUID for each recipient
        uuid_response = requests.get(f'{API_BASE}/new-uuid')
        uuid = uuid_response.json()['uuid']

        # Create recipient record
        recipient_response = requests.post(
            f'{API_BASE}/api/admin/recipients',
            headers={
                'Authorization': f'Bearer {ADMIN_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={
                'email': recipient['email'],
                'description': recipient['description']
            }
        )

        # Send email with tracking
        tracking_url = f'{API_BASE}/img/{uuid}'
        send_email(recipient['email'], tracking_url)

        results.append({
            'email': recipient['email'],
            'uuid': uuid,
            'tracking_url': tracking_url
        })

    return results

# Usage
recipients = [
    {'email': 'user1@example.com', 'description': 'Customer 1'},
    {'email': 'user2@example.com', 'description': 'Customer 2'},
]

results = send_batch_emails(recipients)
```

### Custom Tracking Parameters

Add custom metadata to tracking events:

```python
import requests

def track_with_metadata(uuid, metadata):
    """
    Track email open with custom metadata.
    Note: This requires backend modification to support custom metadata.
    """
    tracking_url = f'http://your-domain.com/img/{uuid}'
    if metadata:
        # Append metadata as URL parameters
        params = '&'.join([f'{k}={v}' for k, v in metadata.items()])
        tracking_url += f'?{params}'

    return tracking_url

# Usage
metadata = {
    'campaign': 'newsletter',
    'segment': 'premium',
    'source': 'website'
}

tracking_url = track_with_metadata(
    '550e8400-e29b-41d4-a716-446655440000',
    metadata
)
```

### Webhook Integration

Set up webhooks for real-time notifications:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/email-opened', methods=['POST'])
def email_opened_webhook():
    data = request.json

    # Process email open event
    if data['event'] == 'email_opened':
        print(f"Email opened by {data['recipient']}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Location: {data['country']}")

        # Send notification
        send_notification(data)

    return jsonify({'status': 'success'})

def send_notification(data):
    # Implement your notification logic
    # e.g., Slack, Discord, Email, etc.
    pass
```

### A/B Testing

Track different email versions:

```python
import requests

def send_ab_test_emails(recipients, version_a, version_b):
    results = {'A': 0, 'B': 0}

    for i, recipient in enumerate(recipients):
        # Determine version (A/B split)
        version = 'A' if i % 2 == 0 else 'B'
        content = version_a if version == 'A' else version_b

        # Generate UUID
        uuid_response = requests.get('http://localhost:5000/new-uuid')
        uuid = uuid_response.json()['uuid']

        # Create recipient with version info
        requests.post(
            'http://localhost:5000/api/admin/recipients',
            headers={
                'Authorization': 'Bearer your-admin-token',
                'Content-Type': 'application/json'
            },
            json={
                'email': recipient['email'],
                'description': f'AB Test - Version {version}'
            }
        )

        # Send email with tracking
        send_email(recipient['email'], content, uuid)
        results[version] += 1

    return results

# Usage
recipients = get_recipients_list()
results = send_ab_test_emails(
    recipients,
    version_a='<h1>Subject Line A</h1>',
    version_b='<h1>Subject Line B</h1>'
)
```

---

## Troubleshooting

### Common Issues

#### Tracking Not Working

**Symptom**: Email opens are not being tracked.

**Possible Causes**:
1. Tracking pixel URL is incorrect
2. Backend server is not accessible
3. Email client blocks images
4. UUID is invalid

**Solutions**:
1. Verify the tracking URL format: `http://your-domain.com/img/<uuid>`
2. Check backend logs: `tail -f logs/app.log`
3. Test the URL in a browser
4. Ensure the UUID was generated correctly

```bash
# Test tracking URL
curl http://localhost:5000/img/your-uuid-here
```

#### Extension Not Loading

**Symptom**: Browser extension doesn't appear or work.

**Possible Causes**:
1. Extension not loaded in developer mode
2. API URL is incorrect
3. CORS issues
4. Browser compatibility

**Solutions**:
1. Enable developer mode and reload extension
2. Check `API_BASE_URL` in `content.js`
3. Verify CORS settings in backend
4. Try a different browser or update current browser

```javascript
// Check extension console for errors
// Open DevTools (F12) in Gmail and check Console tab
```

#### Authentication Errors

**Symptom**: API returns 401 Unauthorized.

**Possible Causes**:
1. Invalid admin token
2. Missing Authorization header
3. Token expired (if using JWT)

**Solutions**:
1. Verify `ADMIN_TOKEN` in environment variables
2. Include `Authorization: Bearer <token>` header
3. Restart backend after changing token

```bash
# Check environment variables
echo $ADMIN_TOKEN

# Test authentication
curl http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"token": "your-admin-token"}'
```

#### Database Connection Issues

**Symptom**: Application fails to connect to database.

**Possible Causes**:
1. Database server not running
2. Incorrect connection string
3. Network/firewall issues
4. Database not created

**Solutions**:
1. Start database server
2. Verify `SQLALCHEMY_DATABASE_URI`
3. Check firewall rules
4. Create database

```bash
# PostgreSQL
sudo systemctl start postgresql
sudo -u postgres createdb readreceipt

# Check connection
psql -U postgres -d readreceipt -c "SELECT 1;"
```

#### CORS Errors

**Symptom**: Browser blocks API requests due to CORS.

**Possible Causes**:
1. Origin not in allowed list
2. CORS not configured in backend

**Solutions**:
1. Add origin to `EXTENSION_ALLOWED_ORIGINS`
2. Configure CORS in Flask app

```python
# In app.py
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://mail.google.com", "https://outlook.com"]
    }
})
```

### Debugging Tips

#### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
python app.py
```

#### Check Server Logs

```bash
# Follow logs in real-time
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

#### Test API Endpoints

```bash
# Test all endpoints
for endpoint in / /new-uuid /api/admin/stats; do
    echo "Testing $endpoint"
    curl -I http://localhost:5000$endpoint
    echo "---"
done
```

#### Verify Database

```python
# Python script to verify database
from app import app, db

with app.app_context():
    # Check tables exist
    tables = db.engine.table_names()
    print(f"Tables: {tables}")

    # Check recipients
    from app import Recipients
    recipients = Recipients.query.all()
    print(f"Recipients: {len(recipients)}")
```

---

## Best Practices

### Email Content

1. **Place tracking pixel at the end**: Reduces impact on email rendering
2. **Use transparent pixel**: 1x1 GIF or PNG with `style="display:none;"`
3. **Test before sending**: Send test emails to verify tracking works
4. **Comply with regulations**: Inform recipients about tracking where required

### Performance

1. **Use CDN**: Serve tracking images via CDN for faster loading
2. **Cache tracking images**: Browser cache won't affect tracking
3. **Batch API requests**: Reduce API calls when possible
4. **Monitor database**: Regular maintenance and indexing

### Security

1. **Use HTTPS**: Always use secure connections in production
2. **Rotate tokens**: Regularly update admin tokens
3. **Limit permissions**: Use least-privilege principle
4. **Audit logs**: Regularly review access logs

---

## Additional Resources

- [API Documentation](README.md#api-documentation)
- [Configuration Guide](README.md#configuration)
- [Deployment Guide](README.md#deployment)
- [Troubleshooting](#troubleshooting)

---

## Support

If you need help:

1. Check this guide for common solutions
2. Review [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
3. Ask a question on [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)
4. Create a new issue with details about your problem
