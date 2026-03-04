# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Read Receipt.

## Table of Contents

- [Common Issues](#common-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Extension Issues](#extension-issues)
- [Database Issues](#database-issues)
- [Deployment Issues](#deployment-issues)
- [Debugging Tips](#debugging-tips)
- [Known Issues](#known-issues)
- [Getting Help](#getting-help)

## Common Issues

### Quick Fixes

**Server won't start:**
```bash
# Check if port is in use
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port
export PORT=5001
```

**Can't login to dashboard:**
- Verify `ADMIN_TOKEN` environment variable
- Check for typos in token
- Clear browser cache and localStorage
- Restart backend server

**Extension not working:**
- Ensure you're on supported domain (mail.google.com)
- Check extension is enabled
- Reload extension from extensions page
- Check browser console for errors

**No tracking events:**
- Verify server URL in extension settings
- Check server is accessible
- Test tracking endpoint manually
- Check server logs for incoming requests

## Backend Issues

### Server Won't Start

**Problem:** `python app.py` fails with error

**Common Causes:**

1. **Missing Dependencies:**
   ```bash
   # Solution: Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

2. **Port Already in Use:**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   
   # Kill the process
   kill -9 <PID>
   
   # Or use different port
   export PORT=5001
   python app.py
   ```

3. **Database Connection Error:**
   ```bash
   # Check database URI
   echo $SQLALCHEMY_DATABASE_URI
   
   # Test PostgreSQL connection
   psql -h hostname -U username -d readreceipt
   
   # For SQLite, check permissions
   ls -la db.sqlite3
   chmod 644 db.sqlite3
   ```

4. **Import Errors:**
   ```bash
   # Check Python version (must be 3.11+)
   python --version
   
   # Reinstall problematic package
   pip uninstall flask
   pip install flask
   ```

### High Memory Usage

**Problem:** Server consuming excessive memory

**Solutions:**

1. **Check for Memory Leaks:**
   ```bash
   # Monitor memory usage
   watch -n 1 'ps aux | grep python'
   ```

2. **Optimize Database Queries:**
   - Add indexes to frequently queried columns
   - Use pagination for large result sets
   - Avoid N+1 queries

3. **Limit Concurrent Connections:**
   ```bash
   # Use gunicorn with worker limits
   gunicorn -w 4 --threads 2 app:app
   ```

4. **Enable Garbage Collection:**
   ```python
   import gc
   gc.collect()
   ```

### Slow Response Times

**Problem:** API endpoints responding slowly

**Solutions:**

1. **Enable Query Logging:**
   ```python
   import logging
   logging.basicConfig()
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

2. **Add Database Indexes:**
   ```sql
   CREATE INDEX idx_tracking_timestamp ON tracking(timestamp);
   CREATE INDEX idx_recipients_r_uuid ON recipients(r_uuid);
   ```

3. **Use Connection Pooling:**
   ```env
   SQLALCHEMY_ENGINE_OPTIONS={"pool_size": 10, "max_overflow": 20}
   ```

4. **Cache Frequently Accessed Data:**
   - Use Redis for caching
   - Implement application-level caching

### 500 Internal Server Error

**Problem:** API returns 500 error

**Debugging Steps:**

1. **Check Server Logs:**
   ```bash
   # View Flask logs
   journalctl -u readreceipt -f
   
   # Or check application logs
   tail -f /path/to/logs/app.log
   ```

2. **Enable Debug Mode:**
   ```bash
   export FLASK_ENV=development
   export LOG_LEVEL=DEBUG
   ```

3. **Check Exception Details:**
   ```python
   @app.errorhandler(500)
   def handle_500(error):
       app.logger.error(f'Internal error: {error}')
       return jsonify({"error": str(error)}), 500
   ```

4. **Common Causes:**
   - Database connection lost
   - Missing environment variables
   - Unhandled exceptions in code
   - Resource limits exceeded

## Frontend Issues

### Dashboard Won't Load

**Problem:** Blank page or loading spinner

**Solutions:**

1. **Check Browser Console:**
   ```
   F12 → Console tab
   Look for errors
   ```

2. **Verify Backend is Running:**
   ```bash
   curl http://localhost:5000/
   # Should return 200 OK
   ```

3. **Check API Endpoint:**
   ```javascript
   // In admin-dashboard/src/api/api.js
   const API_BASE_URL = '/api'  // Ensure correct
   ```

4. **Clear Browser Cache:**
   ```
   Ctrl+Shift+Delete (Windows/Linux)
   Cmd+Shift+Delete (Mac)
   Select "Cached images and files"
   ```

5. **Rebuild Frontend:**
   ```bash
   cd admin-dashboard
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### Login Fails

**Problem:** Can't login with admin token

**Solutions:**

1. **Verify Token:**
   ```bash
   echo $ADMIN_TOKEN
   # Ensure it matches what you're entering
   ```

2. **Test Login Endpoint:**
   ```bash
   curl -X POST http://localhost:5000/api/admin/login \
     -H "Content-Type: application/json" \
     -d '{"token": "your-token"}'
   ```

3. **Check CORS:**
   - Ensure backend allows frontend origin
   - Check browser console for CORS errors

4. **Clear localStorage:**
   ```javascript
   // In browser console
   localStorage.clear()
   ```

### Charts Not Rendering

**Problem:** Analytics charts empty or broken

**Solutions:**

1. **Check Data:**
   ```bash
   curl http://localhost:5000/api/analytics/summary \
     -H "Authorization: Bearer your-token"
   ```

2. **Verify Recharts Installation:**
   ```bash
   cd admin-dashboard
   npm install recharts
   ```

3. **Check Console Errors:**
   - Look for Recharts-specific errors
   - Check for data format issues

4. **Browser Compatibility:**
   - Ensure browser supports SVG
   - Try different browser

### API Requests Failing

**Problem:** Network errors in browser console

**Solutions:**

1. **Check Network Tab:**
   ```
   F12 → Network tab
   Look for failed requests
   Check status codes
   ```

2. **Verify Authentication:**
   ```javascript
   // Check token in localStorage
   localStorage.getItem('adminToken')
   ```

3. **Check CORS Configuration:**
   ```python
   from flask_cors import CORS
   CORS(app, origins=['http://localhost:3000'])
   ```

4. **Test with cURL:**
   ```bash
   curl http://localhost:5000/api/admin/recipients \
     -H "Authorization: Bearer your-token"
   ```

## Extension Issues

### Extension Not Loading

**Chrome:**

**Problem:** Extension doesn't appear in extensions list

**Solutions:**
1. Check `manifest.json` for syntax errors
2. Verify all referenced files exist
3. Check for errors: `chrome://extensions/` → "Errors" button
4. Reload Chrome

**Firefox:**

**Problem:** Can't load temporary add-on

**Solutions:**
1. Ensure selecting `manifest.json` file (not folder)
2. Check Browser Console (Ctrl+Shift+J)
3. Restart Firefox
4. Try Firefox Developer Edition

### Extension Not Injecting Pixels

**Problem:** Tracking pixels not appearing in emails

**Solutions:**

1. **Verify Domain:**
   - Ensure on supported domain (mail.google.com)
   - Check URL matches manifest.json host_permissions

2. **Check Extension Status:**
   ```
   chrome://extensions/
   Ensure extension is enabled
   ```

3. **Inspect Console:**
   ```
   F12 → Console
   Look for "[ReadReceipt]" log messages
   ```

4. **Check Compose Detection:**
   - Open new compose window
   - Wait a few seconds
   - Check page source for `<img>` tag

5. **Reload Extension:**
   ```
   chrome://extensions/ → Reload button
   about:debugging → Reload button
   ```

### Tracking Not Working

**Problem:** Emails sent but no tracking events

**Solutions:**

1. **Verify Server URL:**
   - Check extension popup settings
   - Test URL in browser: `{URL}/new-uuid`

2. **Check Server Logs:**
   ```bash
   # Look for incoming requests
   tail -f /path/to/logs/app.log
   ```

3. **Test Tracking Endpoint:**
   ```bash
   curl -I "http://localhost:5000/img/test-uuid"
   # Should return 200 OK with image/png
   ```

4. **Verify Pixel in Sent Email:**
   - View email source
   - Search for `<img` tags
   - Should see tracking pixel with UUID

5. **Check Recipient Email Client:**
   - Some clients block external images
   - Ask recipient to enable images
   - Test with different providers

### CORS Errors

**Problem:** Console shows CORS policy errors

**Solutions:**

1. **Server-Side Fix:**
   ```python
   from flask_cors import CORS
   
   CORS(app, 
        origins=[
            'https://mail.google.com',
            'https://outlook.live.com'
        ],
        allow_headers=['Content-Type', 'Authorization'])
   ```

2. **Extension Manifest:**
   ```json
   {
     "host_permissions": [
       "https://your-server.com/*"
     ]
   }
   ```

3. **Development Mode:**
   - Use HTTP for local development
   - Avoid mixed content (HTTP from HTTPS)

## Database Issues

### Connection Errors

**Problem:** Can't connect to database

**PostgreSQL:**

**Solutions:**
1. **Check PostgreSQL is Running:**
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Verify Connection String:**
   ```bash
   echo $SQLALCHEMY_DATABASE_URI
   # Should be: postgresql://user:pass@host:5432/dbname
   ```

3. **Test Connection:**
   ```bash
   psql -h localhost -U readreceipt -d readreceipt
   ```

4. **Check pg_hba.conf:**
   ```bash
   # Allow local connections
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   # Add: local   all   all   md5
   ```

5. **Verify Database Exists:**
   ```bash
   sudo -u postgres psql -c "\l"
   ```

### Migration Errors

**Problem:** Flask-Migrate fails

**Solutions:**

1. **Check Migration History:**
   ```bash
   flask db history
   ```

2. **Stamp Current Revision:**
   ```bash
   flask db stamp head
   ```

3. **Re-run Migrations:**
   ```bash
   flask db upgrade
   ```

4. **Reset Database (Development Only):**
   ```bash
   rm db.sqlite3
   flask db init
   flask db migrate
   flask db upgrade
   ```

### Slow Queries

**Problem:** Database queries slow

**Solutions:**

1. **Enable Query Logging:**
   ```python
   app.config['SQLALCHEMY_ECHO'] = True
   ```

2. **Add Indexes:**
   ```sql
   CREATE INDEX idx_tracking_timestamp ON tracking(timestamp);
   CREATE INDEX idx_tracking_recipients_id ON tracking(recipients_id);
   CREATE INDEX idx_recipients_r_uuid ON recipients(r_uuid);
   ```

3. **Analyze Query Plans:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM tracking WHERE timestamp > NOW() - INTERVAL '7 days';
   ```

4. **Vacuum and Analyze:**
   ```sql
   VACUUM ANALYZE tracking;
   VACUUM ANALYZE recipients;
   ```

### Database Locked (SQLite)

**Problem:** `database is locked` error

**Solutions:**

1. **Check for Locking Processes:**
   ```bash
   lsof db.sqlite3
   ```

2. **Increase Timeout:**
   ```python
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'connect_args': {'timeout': 30}
   }
   ```

3. **Use WAL Mode:**
   ```sql
   PRAGMA journal_mode=WAL;
   ```

4. **Consider PostgreSQL:**
   - SQLite not suitable for production
   - Migrate to PostgreSQL for concurrent access

## Deployment Issues

### Docker Issues

**Problem:** Container won't start

**Solutions:**

1. **Check Logs:**
   ```bash
   docker logs readreceipt
   ```

2. **Verify Environment Variables:**
   ```bash
   docker inspect readreceipt | grep -A 20 Env
   ```

3. **Test Locally:**
   ```bash
   docker run -it readreceipt /bin/bash
   python app.py
   ```

4. **Check Resource Limits:**
   ```bash
   docker stats readreceipt
   ```

### Kubernetes Issues

**Problem:** Pods not starting

**Solutions:**

1. **Check Pod Status:**
   ```bash
   kubectl get pods -n readreceipt
   kubectl describe pod <pod-name> -n readreceipt
   ```

2. **View Logs:**
   ```bash
   kubectl logs <pod-name> -n readreceipt
   ```

3. **Check Events:**
   ```bash
   kubectl get events -n readreceipt --sort-by='.lastTimestamp'
   ```

4. **Verify Secrets:**
   ```bash
   kubectl get secrets -n readreceipt
   kubectl describe secret readreceipt-secrets -n readreceipt
   ```

### SSL/TLS Issues

**Problem:** HTTPS not working

**Solutions:**

1. **Check Certificate:**
   ```bash
   sudo certbot certificates
   ```

2. **Renew Certificate:**
   ```bash
   sudo certbot renew
   ```

3. **Verify nginx Configuration:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Check Firewall:**
   ```bash
   sudo ufw allow 443/tcp
   sudo ufw status
   ```

## Debugging Tips

### Enable Debug Logging

**Backend:**
```bash
export LOG_LEVEL=DEBUG
export FLASK_ENV=development
python app.py
```

**Frontend:**
```javascript
// In browser console
localStorage.setItem('debug', 'true')
```

### Use Browser DevTools

**Network Tab:**
- Monitor API requests
- Check response codes
- View request/response headers
- Inspect payloads

**Console Tab:**
- View JavaScript errors
- Check log messages
- Execute commands

**Application Tab:**
- Inspect localStorage
- Check cookies
- View service workers

### Test Endpoints Manually

```bash
# Test root endpoint
curl -I http://localhost:5000/

# Test tracking endpoint
curl -I http://localhost:5000/img/test-uuid

# Test admin endpoint
curl http://localhost:5000/api/admin/recipients \
  -H "Authorization: Bearer your-token"

# Test analytics
curl http://localhost:5000/api/analytics/summary \
  -H "Authorization: Bearer your-token"
```

### Check Database Directly

**SQLite:**
```bash
sqlite3 db.sqlite3

# List tables
.tables

# View recipients
SELECT * FROM recipients LIMIT 10;

# View tracking events
SELECT * FROM tracking ORDER BY timestamp DESC LIMIT 10;
```

**PostgreSQL:**
```bash
psql -h localhost -U readreceipt -d readreceipt

# List tables
\dt

# View data
SELECT * FROM recipients LIMIT 10;
SELECT COUNT(*) FROM tracking;
```

### Monitor System Resources

```bash
# CPU and memory
top
htop

# Disk usage
df -h
du -sh /path/to/readreceipt

# Network connections
netstat -tulpn
ss -tulpn

# Process monitoring
ps aux | grep python
```

## Known Issues

### Current Limitations

1. **Gmail Image Caching:**
   - Gmail proxies images through their servers
   - May delay tracking events
   - We detect and handle GmailImageProxy user agents

2. **Firefox Temporary Extensions:**
   - Extensions removed on browser close
   - Must reload each session
   - Workaround: Package as XPI file

3. **No Rate Limiting:**
   - Current version has no built-in rate limiting
   - Implement via reverse proxy (nginx, Cloudflare)
   - Planned for future release

4. **Settings Not Persistent:**
   - Settings stored in-memory
   - Reset on server restart
   - Planned: Database-backed settings

5. **No Bulk Operations:**
   - Can't import/export recipients in bulk
   - Must create individually
   - Planned feature

### Browser Compatibility

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | 88+ | ✅ Full | Recommended |
| Firefox | 85+ | ✅ Full | Temporary extensions |
| Safari | 14+ | ⚠️ Limited | Extension not available |
| Edge | 88+ | ✅ Full | Chrome-based |

### Email Client Compatibility

| Client | Tracking | Notes |
|--------|----------|-------|
| Gmail Web | ✅ Full | Primary target |
| Outlook Web | ✅ Full | Well-supported |
| Yahoo Mail | ✅ Full | Supported |
| Apple Mail | ⚠️ Partial | Blocks external images by default |
| Outlook Desktop | ⚠️ Partial | May block images |
| Thunderbird | ⚠️ Partial | Requires image enablement |
| Mobile Apps | ❌ No | Extensions don't work on mobile |

## Getting Help

### Resources

- **Documentation:** Check other docs in this directory
- **GitHub Issues:** [Search existing issues](https://github.com/yasn77/readreceipt/issues)
- **GitHub Discussions:** [Ask questions](https://github.com/yasn77/readreceipt/discussions)

### Before Asking for Help

1. **Check Documentation:**
   - Read relevant guides
   - Search for your issue

2. **Gather Information:**
   - Error messages
   - Steps to reproduce
   - Environment details (OS, versions)
   - Logs and screenshots

3. **Try Basic Troubleshooting:**
   - Restart services
   - Clear cache
   - Check logs
   - Test with minimal configuration

### How to Report Issues

**Good Issue Report:**

```markdown
**Description:**
Clear description of the problem

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- Browser: Chrome 120
- Deployment: Docker

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Logs:**
```
Relevant log output
```

**Screenshots:**
If applicable
```

### Contact

- **Security Issues:** Contact maintainers directly (not public issues)
- **General Questions:** GitHub Discussions
- **Bug Reports:** GitHub Issues
- **Feature Requests:** GitHub Issues with "enhancement" label

---

**Still stuck?** Open an issue on GitHub with detailed information about your problem.
