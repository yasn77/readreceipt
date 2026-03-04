# Story: Chrome Extension - Manifest V3

## Description
As a user, I want a Chrome extension that automatically injects read receipt tracking into Gmail, so that I can track when recipients open my emails without manual intervention.

## Acceptance Criteria
- [ ] Extension uses Manifest V3 format
- [ ] Content script injects tracking pixel into Gmail compose
- [ ] Background service worker handles messages
- [ ] Popup UI for enabling/disabling tracking
- [ ] Support for multiple email providers (modular architecture)
- [ ] Proper error handling and logging
- [ ] Minimal permissions requested

## Technical Notes
- Use Manifest V3 (service workers, not background pages)
- Modular provider architecture for easy extension
- Use Chrome Storage API for settings
- Implement retry logic for failed tracking
- Use TypeScript for better type safety (optional)

## Components
1. **manifest.json**
   - Manifest V3 format
   - Required permissions only
   - Content script for Gmail
   - Action popup

2. **background.js**
   - Service worker
   - Message handling
   - Settings management

3. **content.js**
   - Gmail compose detection
   - Tracking pixel injection
   - DOM observation

4. **popup.html/popup.js**
   - Toggle tracking on/off
   - Show status
   - Quick settings

5. **providers/gmail.js**
   - Gmail-specific DOM selectors
   - Compose window detection
   - Pixel injection logic

## Provider Architecture
```
src/
  providers/
    gmail.js (implemented)
    outlook.js (stub)
    yahoo.js (stub)
    base.js (interface)
```

## Definition of Done
- [ ] Extension loads in Chrome
- [ ] Tracking pixel injected in Gmail compose
- [ ] Popup UI working
- [ ] Settings persist across sessions
- [ ] No console errors
- [ ] Manual testing completed
- [ ] PR reviewed and approved
