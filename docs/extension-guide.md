# Extension Guide

This guide covers installation, configuration, and troubleshooting for the Read Receipt browser extensions.

## Table of Contents

- [Overview](#overview)
- [Chrome Extension](#chrome-extension)
- [Firefox Extension](#firefox-extension)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Supported Email Services](#supported-email-services)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Overview

The Read Receipt browser extensions automatically inject tracking pixels into your outgoing emails, enabling you to track when recipients open them.

**Key Features:**
- ✅ Automatic tracking pixel injection
- ✅ UUID generation for unique tracking
- ✅ Support for multiple email services
- ✅ Toggle tracking on/off
- ✅ Configurable tracking server
- ✅ Minimal permissions required

**Extension Architecture:**
```
┌─────────────────────────────────────────┐
│          Browser Extension               │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Content    │  │  Background  │    │
│  │    Script    │  │     Worker   │    │
│  │              │  │              │    │
│  │ - Detect     │  │ - Manage     │    │
│  │   compose    │  │   state      │    │
│  │ - Inject     │  │ - Handle     │    │
│  │   pixel      │  │   events     │    │
│  └──────────────┘  └──────────────┘    │
│                                         │
│  ┌──────────────┐                      │
│  │    Popup     │                      │
│  │      UI      │                      │
│  │              │                      │
│  │ - Configure  │                      │
│  │ - Toggle     │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────┘
```

## Chrome Extension

### Installation

#### Step 1: Open Extensions Page

1. Open Google Chrome
2. Navigate to `chrome://extensions/`
3. Or click: Menu (⋮) → More tools → Extensions

**Screenshot location:** *Screenshot of Chrome menu showing Extensions option*

#### Step 2: Enable Developer Mode

1. Find the "Developer mode" toggle in the top right
2. Click to enable it
3. Additional buttons will appear

**Screenshot location:** *Screenshot highlighting Developer mode toggle*

#### Step 3: Load Extension

1. Click "Load unpacked" button
2. Navigate to your Read Receipt repository
3. Select the `extensions/chrome` folder
4. Click "Select" or "Open"

**Screenshot location:** *Screenshot of file picker showing extensions/chrome folder*

#### Step 4: Verify Installation

1. Extension should appear in the extensions list
2. Look for "Read Receipt" with version number
3. Extension icon should appear in toolbar (may be hidden in extensions menu)

**Screenshot location:** *Screenshot of installed extension in Chrome*

#### Step 5: Pin Extension (Optional)

1. Click the extensions puzzle piece icon
2. Find "Read Receipt" in the list
3. Click the pin icon next to it
4. Extension icon now visible in toolbar

**Screenshot location:** *Screenshot of pinning extension to toolbar*

### Updating

**Manual Update:**
1. Go to `chrome://extensions/`
2. Click the refresh icon on the Read Receipt card
3. Extension reloads with latest changes

**Automatic Update:**
- Chrome automatically updates unpacked extensions on browser restart
- For development, use manual reload

### Uninstallation

1. Go to `chrome://extensions/`
2. Find Read Receipt extension
3. Click "Remove"
4. Confirm removal

## Firefox Extension

### Installation

#### Step 1: Open Debugging Page

1. Open Firefox
2. Navigate to `about:debugging`
3. Or click: Menu (☰) → More tools → Debugging

**Screenshot location:** *Screenshot of Firefox about:debugging page*

#### Step 2: Select This Firefox

1. Click "This Firefox" in the left sidebar
2. Temporary Extensions section appears

**Screenshot location:** *Screenshot highlighting "This Firefox" option*

#### Step 3: Load Temporary Add-on

1. Click "Load Temporary Add-on..." button
2. Navigate to your Read Receipt repository
3. Go to `extensions/firefox/` folder
4. Select `manifest.json` file
5. Click "Open"

**Screenshot location:** *Screenshot of file picker selecting manifest.json*

#### Step 4: Verify Installation

1. Extension appears under "Temporary Extensions"
2. Status shows as active
3. Extension icon visible in toolbar

**Screenshot location:** *Screenshot of installed Firefox extension*

### Important Notes

**Temporary Nature:**
- Firefox temporary add-ons are **removed when browser closes**
- You must reload the extension each session
- This is a Firefox security feature for unpacked extensions

**Permanent Installation Options:**

1. **Package as XPI:**
   ```bash
   cd extensions/firefox
   zip -r ../readreceipt.xpi *
   ```
   - Drag XPI file into Firefox
   - Installs permanently (until removed)

2. **Use Firefox Developer Edition:**
   - More permissive for development extensions
   - Better debugging tools

3. **Submit to AMO:**
   - Firefox Add-ons website
   - Requires review process
   - Available to all Firefox users

### Updating

**Reload Extension:**
1. Go to `about:debugging`
2. Find Read Receipt in Temporary Extensions
3. Click "Reload" button
4. Extension updates immediately

### Uninstallation

1. Go to `about:debugging`
2. Find Read Receipt
3. Click "Remove" button
4. Extension uninstalled

## Configuration

### Setting Tracking Server URL

The extension needs to know where to send tracking requests.

#### Chrome

1. Click the Read Receipt extension icon
2. In the popup, find "Tracking Server URL"
3. Enter your server URL (e.g., `http://localhost:5000` or `https://readreceipt.yourdomain.com`)
4. Click "Save"

**Screenshot location:** *Screenshot of Chrome extension popup with server URL*

#### Firefox

1. Click the Read Receipt extension icon
2. Enter tracking server URL in popup
3. Click "Save"

### Toggling Tracking

You can enable/disable tracking without uninstalling:

1. Click extension icon
2. Toggle the "Enable Tracking" switch
3. Status updates immediately

**Use Cases:**
- Disable during testing
- Pause tracking temporarily
- Troubleshoot issues

### Advanced Configuration

#### Edit Content Script

For advanced users, edit `content.js` directly:

```javascript
// extensions/chrome/content.js
const TRACKING_SERVER = 'https://your-server.com';
let trackingEnabled = true;

// Custom configuration
const CUSTOM_SETTINGS = {
  autoInject: true,
  logDebug: false,
  // ...
};
```

**Reload extension after changes.**

#### Modify Permissions

Edit `manifest.json` to add/remove permissions:

```json
{
  "permissions": [
    "tabs",
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "https://mail.google.com/*",
    "https://outlook.live.com/*"
  ]
}
```

**Reload extension after manifest changes.**

## How It Works

### Tracking Pixel Injection Flow

```
1. User opens Gmail compose window
         │
         ▼
2. Content script detects compose window
   (via URL pattern and DOM observation)
         │
         ▼
3. Generate unique UUID
   (e.g., 550e8400-e29b-41d4-a716-446655440000)
         │
         ▼
4. Create 1x1 transparent image element
   <img src="{TRACKING_SERVER}/img/{uuid}"
        width="1" height="1"
        style="display:none" />
         │
         ▼
5. Append image to email body
         │
         ▼
6. User sends email
         │
         ▼
7. Recipient opens email
         │
         ▼
8. Email client loads tracking pixel
         │
         ▼
9. Server logs tracking event
         │
         ▼
10. Analytics updated
```

### Code Example

**Detection:**
```javascript
function isGmailCompose() {
  return window.location.href.includes('mail.google.com') &&
         (window.location.href.includes('#compose') ||
          document.querySelector('[role="dialog"][aria-label*="Compose"]'));
}
```

**Pixel Injection:**
```javascript
function injectTrackingPixel(emailBody) {
  const uuid = generateUUID();
  const img = document.createElement('img');
  img.src = `${TRACKING_SERVER}/img/${uuid}`;
  img.width = 1;
  img.height = 1;
  img.style.display = 'none';
  emailBody.appendChild(img);
}
```

### Observer Pattern

The extension uses MutationObserver to detect when compose windows open:

```javascript
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.addedNodes.length > 0) {
      if (isGmailCompose()) {
        const body = findComposeBody();
        if (body) {
          injectTrackingPixel(body);
        }
      }
    }
  });
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});
```

## Supported Email Services

### Fully Supported ✅

| Service | Domain | Status | Notes |
|---------|--------|--------|-------|
| **Gmail** | mail.google.com | ✅ Full | Primary target, well-tested |
| **Outlook.com** | outlook.live.com | ✅ Full | Works with web version |
| **Yahoo Mail** | mail.yahoo.com | ✅ Full | Works with web version |

### Partially Supported ⚠️

| Service | Domain | Status | Notes |
|---------|--------|--------|-------|
| **ProtonMail** | mail.protonmail.com | ⚠️ Limited | May require manual configuration |
| **iCloud Mail** | icloud.com/mail | ⚠️ Limited | Test thoroughly |
| **Zoho Mail** | mail.zoho.com | ⚠️ Limited | DOM structure varies |

### Not Supported ❌

- Desktop email clients (Outlook desktop, Thunderbird, Apple Mail)
- Mobile email apps (Gmail app, Outlook app, Apple Mail)
- Self-hosted webmail (Roundcube, Horde) - may work with custom configuration

### Adding Support for New Services

To add support for a new email service:

1. **Identify Compose Window:**
   - Find unique URL pattern
   - Identify DOM structure
   - Locate email body element

2. **Update manifest.json:**
   ```json
   "content_scripts": [
     {
       "matches": ["https://newservice.com/*"],
       "js": ["content.js"]
     }
   ]
   ```

3. **Add Detection Logic:**
   ```javascript
   function isNewServiceCompose() {
     return window.location.href.includes('newservice.com') &&
            document.querySelector('.compose-selector');
   }
   ```

4. **Test Thoroughly:**
   - Compose new email
   - Reply to email
   - Forward email
   - Send with attachments
   - Verify pixel injection

## Troubleshooting

### Extension Not Loading

**Chrome:**

**Problem:** Extension doesn't appear in extensions list

**Solutions:**
1. Check `manifest.json` for syntax errors (use JSON validator)
2. Verify all referenced files exist
3. Check Chrome console for errors: `chrome://extensions/` → "Errors" button
4. Try reloading Chrome

**Firefox:**

**Problem:** Can't load temporary add-on

**Solutions:**
1. Ensure you're selecting `manifest.json` (not folder)
2. Check Firefox Browser Console (Ctrl+Shift+J)
3. Verify manifest.json is valid JSON
4. Try restarting Firefox

### Extension Not Injecting Pixels

**Problem:** Tracking pixels not appearing in emails

**Solutions:**

1. **Check Domain:**
   - Ensure you're on a supported domain (mail.google.com, etc.)
   - Extension only works on specified domains

2. **Verify Extension is Enabled:**
   - Check extensions page
   - Ensure toggle is enabled
   - Look for extension icon

3. **Check Console:**
   - Open browser console (F12)
   - Look for Read Receipt log messages
   - Check for errors

4. **Reload Extension:**
   - Chrome: `chrome://extensions/` → Reload
   - Firefox: `about:debugging` → Reload

5. **Test on Simple Compose:**
   - Open new compose window
   - Don't add recipients initially
   - Check if pixel appears in source

### Tracking Not Working

**Problem:** Emails sent but no tracking events logged

**Solutions:**

1. **Verify Server URL:**
   - Check extension popup settings
   - Ensure URL is correct and accessible
   - Test URL in browser: `{URL}/new-uuid`

2. **Check Server Logs:**
   - Look for incoming requests
   - Verify no CORS errors
   - Check firewall rules

3. **Test Tracking Endpoint:**
   ```bash
   curl -I https://your-server.com/img/test-uuid
   ```
   Should return 200 OK with image/png

4. **Verify Pixel in Sent Email:**
   - View email source
   - Search for `<img` tags
   - Should see tracking pixel

5. **Check Recipient Email Client:**
   - Some clients block external images
   - Ask recipient to enable images
   - Test with different email providers

### CORS Errors

**Problem:** Console shows CORS policy errors

**Solutions:**

1. **Server-Side:**
   Add CORS headers to Flask app:
   ```python
   from flask_cors import CORS
   CORS(app, origins=['https://mail.google.com'])
   ```

2. **Extension Manifest:**
   Ensure host_permissions include your server:
   ```json
   "host_permissions": [
     "https://your-server.com/*"
   ]
   ```

3. **Development:**
   Use HTTP for local development to avoid mixed content issues

### Performance Issues

**Problem:** Extension slows down Gmail

**Solutions:**

1. **Disable Debug Logging:**
   ```javascript
   // Set to false in content.js
   const DEBUG = false;
   ```

2. **Reduce Observer Frequency:**
   Increase debounce time in observer

3. **Check Memory Usage:**
   - Chrome: Task Manager (Shift+Esc)
   - Firefox: about:performance
   - Reload extension if memory high

4. **Update Extension:**
   Ensure you're using latest version with performance fixes

### Security Warnings

**Problem:** Browser shows security warnings

**Solutions:**

1. **Use HTTPS:**
   - Always use HTTPS in production
   - Browsers block mixed content (HTTP from HTTPS pages)

2. **Valid Certificate:**
   - Ensure SSL certificate is valid
   - No self-signed certs in production

3. **CSP Compliance:**
   - Extension follows Content Security Policy
   - No inline scripts (except where required)

## Development

### Local Development Setup

1. **Clone Repository:**
   ```bash
   git clone https://github.com/yasn77/readreceipt.git
   cd readreceipt/extensions/chrome
   ```

2. **Load Unpacked:**
   - Follow installation steps above
   - Use development server URL

3. **Enable Debug Mode:**
   ```javascript
   const DEBUG = true;
   ```

4. **Monitor Console:**
   - Keep browser console open
   - Watch for log messages

### Testing

**Manual Testing:**

1. Compose email in Gmail
2. Check page source for tracking pixel
3. Send to test email
4. Open email and verify tracking event

**Automated Testing:** (Future)
```javascript
// Test suite for extension
describe('Read Receipt Extension', () => {
  it('should inject tracking pixel', () => {
    // Test implementation
  });
});
```

### Debugging

**Chrome:**

1. Go to `chrome://extensions/`
2. Find Read Receipt
3. Click "Inspect views: background page"
4. Use DevTools to debug

**Firefox:**

1. Go to `about:debugging`
2. Find Read Receipt
3. Click "Inspect"
4. Use DevTools to debug

### Building for Production

**Chrome:**

1. Ensure all files are in `extensions/chrome/`
2. No build step required (vanilla JS)
3. Package as ZIP for distribution

**Firefox:**

1. Create XPI package:
   ```bash
   cd extensions/firefox
   zip -r ../readreceipt-firefox.xpi *
   ```

2. Submit to AMO or distribute directly

### Publishing

**Chrome Web Store:**

1. Create developer account ($5 fee)
2. Package extension as ZIP
3. Submit to Chrome Web Store
4. Wait for review (typically 1-3 days)

**Firefox Add-ons (AMO):**

1. Create developer account (free)
2. Package as XPI
3. Submit to AMO
4. Wait for review (typically 1-5 days)

## Best Practices

### Security

- ✅ Use HTTPS for tracking server
- ✅ Validate server URL input
- ✅ Don't store sensitive data in extension
- ✅ Request minimal permissions
- ✅ Keep extension updated

### Performance

- ✅ Minimise DOM manipulation
- ✅ Debounce observer callbacks
- ✅ Clean up event listeners
- ✅ Avoid memory leaks

### User Experience

- ✅ Provide clear status indicators
- ✅ Show helpful error messages
- ✅ Make settings easy to find
- ✅ Respect user preferences

## Next Steps

- [Admin Guide](admin-guide.md) - Manage recipients and view analytics
- [API Reference](api-reference.md) - Programmatic access
- [Troubleshooting](troubleshooting.md) - General troubleshooting

---

**Need help?** Check [Troubleshooting](troubleshooting.md) or open an issue on GitHub.
