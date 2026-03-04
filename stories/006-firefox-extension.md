# Story: Firefox Extension

## Description
As a Firefox user, I want a Firefox-compatible version of the Read Receipt extension, so that I can use the same tracking functionality in Firefox.

## Acceptance Criteria
- [ ] Extension works in Firefox
- [ ] Uses same core code as Chrome version
- [ ] Firefox-specific manifest adjustments
- [ ] Tested on latest Firefox version
- [ ] Built using web-ext tool

## Technical Notes
- Use web-ext for building and testing
- Share core code between Chrome and Firefox
- Separate manifest files where needed
- Test Firefox-specific APIs
- Consider Firefox's stricter CSP

## File Structure
```
extensions/
  firefox/
    manifest.json (Firefox-specific)
    background.js (shared or adapted)
    content.js (shared)
    popup.html (shared)
  chrome/
    manifest.json (Chrome-specific)
    ... (same files)
  shared/
    content.js
    popup.js
    providers/
```

## Build Process
- Use npm scripts to build both versions
- Copy shared files to browser-specific directories
- Apply browser-specific manifest
- Package as .xpi (Firefox) and .zip (Chrome)

## Definition of Done
- [ ] Extension loads in Firefox
- [ ] All features working
- [ ] No console errors
- [ ] web-ext lint passes
- [ ] Manual testing completed
- [ ] PR reviewed and approved
