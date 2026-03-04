# Admin Guide

This guide covers everything you need to know about using the Read Receipt admin dashboard.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Dashboard](#dashboard)
- [Managing Recipients](#managing-recipients)
- [Analytics](#analytics)
- [Settings](#settings)
- [Best Practices](#best-practices)
- [Tips and Tricks](#tips-and-tricks)

## Overview

The admin dashboard is a React-based single-page application that provides:

- **Dashboard** - Overview of tracking statistics and recent activity
- **Recipients** - Manage tracked recipients (create, edit, delete)
- **Analytics** - Detailed analytics and visualisations
- **Settings** - Configure application settings

**Access:** `http://localhost:3000` (or your deployed URL)

**Screenshot location:** *Screenshot of admin dashboard main page showing all sections*

## Getting Started

### Login

1. Navigate to the admin dashboard URL
2. You'll be redirected to the login page
3. Enter your admin token (from `ADMIN_TOKEN` environment variable)
4. Click "Login"

**Screenshot location:** *Screenshot of login page*

**Security Note:**
- Your token is stored in browser localStorage
- Clear browser data to logout
- Use strong tokens in production
- Never share your admin token

### Navigation

The dashboard has a sidebar navigation with the following sections:

- 📊 **Dashboard** - Home page with overview statistics
- 👥 **Recipients** - Recipient management
- 📈 **Analytics** - Detailed analytics and charts
- ⚙️ **Settings** - Configuration options

**Screenshot location:** *Screenshot highlighting sidebar navigation*

## Dashboard

The dashboard provides an at-a-glance view of your email tracking activity.

### Key Metrics

**Total Recipients**
- Number of recipients in your database
- Click to view all recipients

**Total Events**
- Total number of email opens tracked
- Updates in real-time

**Events Today**
- Email opens in the last 24 hours
- Helps track daily engagement

**Unique Opens**
- Number of unique recipients who opened emails
- Different from total events (one recipient can open multiple times)

**Screenshot location:** *Screenshot of dashboard metrics cards*

### Recent Activity

Shows the 5 most recent tracking events:

- **Email** - Recipient identifier
- **Timestamp** - When the email was opened
- **Country** - Geographic location (if available)

**Screenshot location:** *Screenshot of recent activity table*

### Quick Actions

- **Add Recipient** - Quickly create a new recipient
- **View Analytics** - Jump to detailed analytics
- **Export Data** - Download tracking data as CSV

## Managing Recipients

### Viewing Recipients

Navigate to **Recipients** to see all tracked recipients.

**List View Shows:**
- Email address
- Description/Name
- Tracking UUID
- Actions (Edit, Delete)

**Features:**
- Search by email or description
- Sort by any column
- Pagination for large lists

**Screenshot location:** *Screenshot of recipients list view*

### Creating a Recipient

**Method 1: Dashboard Form**

1. Click "Add Recipient" button
2. Fill in the form:
   - **Email** (required) - Recipient's email address
   - **Description** (optional) - Name or description
3. Click "Save"

**Screenshot location:** *Screenshot of create recipient form*

**Method 2: API**

```bash
curl -X POST http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "description": "John Doe"
  }'
```

**Method 3: Automatic (via Extension)**

When you compose an email in Gmail, the extension can automatically create recipients. Configure this in settings.

### Editing a Recipient

1. Find the recipient in the list
2. Click the "Edit" button (pencil icon)
3. Update email or description
4. Click "Save"

**Note:** The UUID cannot be changed. If you need a new UUID, create a new recipient.

**Screenshot location:** *Screenshot of edit recipient form*

### Deleting a Recipient

1. Find the recipient in the list
2. Click the "Delete" button (trash icon)
3. Confirm the deletion

**Warning:** Deleting a recipient does NOT delete associated tracking events. The events remain in the database for historical analytics.

**Bulk Delete:** (Future feature)
- Select multiple recipients
- Click "Delete Selected"
- Confirm bulk deletion

### Importing Recipients

**CSV Import:** (Future feature)

1. Prepare CSV file with columns: `email`, `description`
2. Click "Import" button
3. Upload CSV file
4. Review and confirm import

**CSV Format:**
```csv
email,description
john@example.com,John Doe
jane@example.com,Jane Smith
```

## Analytics

The Analytics section provides detailed insights into email engagement.

### Summary Statistics

**Overview Cards:**
- **Total Events** - All tracking events
- **Unique Recipients** - Recipients who opened at least one email
- **Avg Daily Opens** - Average opens per day (last 7 days)
- **Top Country** - Country with most opens

**Screenshot location:** *Screenshot of analytics summary*

### Time-Series Chart

Visualises email opens over time.

**Features:**
- **Date Range Selector** - Choose 7d, 30d, 90d, or custom range
- **Interactive Chart** - Hover to see exact counts
- **Zoom** - Click and drag to zoom into a period

**Use Cases:**
- Identify best days/times for email engagement
- Track campaign performance over time
- Spot trends and patterns

**Screenshot location:** *Screenshot of time-series chart*

### Geographic Distribution

Shows where your emails are being opened.

**Visualisation:**
- Bar chart or map (future)
- Country-level granularity
- Sorted by number of opens

**Use Cases:**
- Understand your audience geography
- Identify unexpected opens (security)
- Tailor content to regions

**Screenshot location:** *Screenshot of geographic distribution chart*

### Email Client Breakdown

Shows which email clients recipients use.

**Detected Clients:**
- Gmail
- Outlook
- Apple Mail
- Yahoo Mail
- Thunderbird
- Other

**Use Cases:**
- Optimise email design for popular clients
- Troubleshoot rendering issues
- Understand recipient preferences

**Screenshot location:** *Screenshot of email client pie chart*

### Top Recipients

Shows recipients who open emails most frequently.

**Metrics:**
- Recipient email/description
- Number of opens
- Last open date

**Use Cases:**
- Identify engaged recipients
- Find brand advocates
- Detect unusual activity

**Screenshot location:** *Screenshot of top recipients table*

### Export Data

Export all tracking data for external analysis.

**Steps:**
1. Navigate to Analytics
2. Click "Export CSV" button
3. File downloads automatically

**CSV Columns:**
- ID - Tracking event ID
- Recipient ID - Associated recipient
- Timestamp - When opened
- Country - Geographic location
- User Agent - Email client information

**Use Cases:**
- Custom analysis in Excel/Sheets
- Reporting and presentations
- Data backup
- Integration with other tools

**Screenshot location:** *Screenshot of export button*

## Settings

Configure application behaviour and preferences.

### General Settings

**Tracking Enabled**
- Toggle tracking on/off globally
- Useful for maintenance or testing

**Allowed Domains**
- Comma-separated list of domains where extension works
- Default: `https://mail.google.com`
- Add Outlook, Yahoo, etc.

**Screenshot location:** *Screenshot of settings page*

### Security Settings

**Change Admin Token**
- Update your admin token
- Requires restarting the server

**Session Timeout**
- (Future) Configure how long login persists

### Extension Settings

**Default Tracking Server**
- URL where extension sends tracking requests
- Update when deploying to production

**Auto-Create Recipients**
- (Future) Automatically create recipients from sent emails

### Notification Settings

**Email Notifications**
- (Future) Get notified when important emails are opened

**Webhook URLs**
- (Future) Send tracking events to external systems

## Best Practices

### Recipient Management

✅ **DO:**
- Use meaningful descriptions (e.g., "John Doe - Acme Corp")
- Keep email addresses up-to-date
- Regularly clean up inactive recipients
- Export data periodically for backup

❌ **DON'T:**
- Share recipient UUIDs publicly
- Delete recipients if you need historical data
- Import unverified email lists

### Analytics Usage

✅ **DO:**
- Check analytics regularly for insights
- Use date ranges to compare periods
- Export data for detailed analysis
- Monitor for unusual patterns

❌ **DON'T:**
- Read too much into small sample sizes
- Ignore geographic anomalies (could indicate forwarding)
- Share analytics publicly (contains sensitive data)

### Security

✅ **DO:**
- Use strong admin tokens (32+ characters)
- Enable HTTPS in production
- Regularly rotate tokens
- Monitor access logs

❌ **DON'T:**
- Use default "admin" token in production
- Share your admin token
- Leave dashboard open on shared computers
- Store tokens in code repositories

### Performance

✅ **DO:**
- Use PostgreSQL for production
- Index database tables properly
- Export large datasets instead of viewing all
- Archive old data periodically

❌ **DON'T:**
- Keep years of data in active database
- Run analytics on unindexed columns
- Import thousands of recipients at once

## Tips and Tricks

### Keyboard Shortcuts

- `Ctrl/Cmd + K` - Quick search (future)
- `Ctrl/Cmd + Enter` - Save forms
- `Esc` - Close modals

### Filters and Search

**Search Syntax:**
- `john@example.com` - Exact email match
- `John` - Search in description
- `@gmail.com` - Find all Gmail addresses

**Future Filters:**
- Date range
- Country
- Email client
- Open count

### Custom Date Ranges

In analytics, use custom date ranges for:
- Campaign-specific analysis
- Month-over-month comparisons
- Quarterly reports

### Dashboard Customisation

(Future feature)
- Reorder metric cards
- Choose default date range
- Set refresh interval

### Mobile Access

The dashboard is responsive and works on mobile devices:
- Access via phone or tablet
- Touch-optimised controls
- Readable on small screens

**Screenshot location:** *Screenshot of mobile dashboard view*

## Troubleshooting

### Login Issues

**Problem:** Can't login with token

**Solutions:**
1. Verify `ADMIN_TOKEN` environment variable
2. Check for typos in the token
3. Restart the backend server
4. Clear browser cache and localStorage

### Data Not Showing

**Problem:** Dashboard shows zero recipients/events

**Solutions:**
1. Verify backend is running
2. Check browser console for errors
3. Confirm API endpoint is accessible
4. Login again to refresh token

### Export Fails

**Problem:** CSV export doesn't download

**Solutions:**
1. Check browser popup blocker
2. Verify you have tracking events
3. Try a different browser
4. Check server logs for errors

## API Access

The admin dashboard uses the same API available to external clients. See [API Reference](api-reference.md) for details.

**Common API Calls:**

```bash
# Get all recipients
curl http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get dashboard stats
curl http://localhost:5000/api/admin/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analytics summary
curl http://localhost:5000/api/analytics/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Next Steps

- [Extension Guide](extension-guide.md) - Configure browser extensions
- [API Reference](api-reference.md) - Programmatic access
- [Analytics Deep Dive](architecture.md#analytics-endpoints) - Advanced analytics

---

**Need help?** See [Troubleshooting](troubleshooting.md) or open an issue on GitHub.
