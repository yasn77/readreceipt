/**
 * Background service worker for Read Receipt extension
 * Handles tracking pixel blocking when viewing sent folder
 */

console.log('[ReadReceipt] Background service worker started.');

// Store blocked requests in memory (cleared on service worker restart)
let blockedRequests = [];
let blockingEnabled = true;

// Maximum number of blocked requests to store
const MAX_BLOCKED_REQUESTS = 100;

/**
 * Check if current tab is viewing a sent folder
 * @param {string} url - Current tab URL
 * @returns {boolean}
 */
function isSentFolder(url) {
  if (!url) return false;

  // Gmail sent folder patterns
  const gmailSentPatterns = [
    '#sent',
    '#sent/1',
    '#label/sent',
    '#inbox/?search=sent',
    '/search/category:sent',
    '#search/category%3Asent'
  ];

  // Outlook sent folder patterns
  const outlookSentPatterns = [
    '/sentitems',
    '/SentItems',
    '#sentitems',
    '/drafts-sentitems',
    'view=Sent'
  ];

  for (const pattern of gmailSentPatterns) {
    if (url.includes(pattern)) return true;
  }

  for (const pattern of outlookSentPatterns) {
    if (url.includes(pattern)) return true;
  }

  return false;
}

/**
 * Check if URL is a tracking pixel from our server
 * @param {string} url - URL to check
 * @returns {boolean}
 */
function isTrackingPixel(url) {
  // Pattern: /img/<uuid> where uuid is a UUID format
  const trackingPixelPattern = /\/img\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  return trackingPixelPattern.test(url);
}

/**
 * Log a blocked request
 * @param {Object} requestDetails - Details of the blocked request
 */
function logBlockedRequest(requestDetails) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    url: requestDetails.url,
    tabId: requestDetails.tabId,
    type: requestDetails.type
  };

  blockedRequests.unshift(logEntry);

  // Keep only the most recent entries
  if (blockedRequests.length > MAX_BLOCKED_REQUESTS) {
    blockedRequests = blockedRequests.slice(0, MAX_BLOCKED_REQUESTS);
  }

  // Update storage for popup to access
  chrome.storage.local.set({ blockedRequests });

  console.log('[ReadReceipt] Blocked tracking pixel:', requestDetails.url);
}

/**
 * Initialize request blocking
 */
function initBlocking() {
  // Load settings
  chrome.storage.sync.get(['blockingEnabled'], (result) => {
    blockingEnabled = result.blockingEnabled !== false;
    console.log('[ReadReceipt] Blocking enabled:', blockingEnabled);
  });

  // Listen for settings changes
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'sync' && changes.blockingEnabled) {
      blockingEnabled = changes.blockingEnabled.newValue !== false;
      console.log('[ReadReceipt] Blocking toggled:', blockingEnabled);
    }
  });

  // Install webRequest blocking listener
  chrome.webRequest.onBeforeRequest.addListener(
    async (details) => {
      if (!blockingEnabled) {
        return {};
      }

      // Check if this is a tracking pixel
      if (!isTrackingPixel(details.url)) {
        return {};
      }

      // Get the tab to check if it's viewing sent folder
      if (!details.tabId || details.tabId === -1) {
        return {}; // Can't determine tab context
      }

      try {
        const tab = await chrome.tabs.get(details.tabId);
        if (tab.url && isSentFolder(tab.url)) {
          logBlockedRequest(details);
          console.log('[ReadReceipt] Blocking pixel - user is in sent folder');
          return { cancel: true };
        }
      } catch (error) {
        console.error('[ReadReceipt] Error getting tab:', error);
        return {};
      }

      return {};
    },
    {
      urls: [
        'https://*/*',
        'http://*/*'
      ],
      types: ['image']
    },
    ['blocking']
  );

  console.log('[ReadReceipt] webRequest blocking initialized');
}

// Listen for extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('[ReadReceipt] Extension installed');
  blockedRequests = [];
  chrome.storage.local.set({ blockedRequests });
});

// Listen for popup messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getBlockedRequests') {
    sendResponse({ blockedRequests });
  }

  if (message.action === 'clearBlockedRequests') {
    blockedRequests = [];
    chrome.storage.local.set({ blockedRequests });
    sendResponse({ status: 'success' });
  }

  if (message.action === 'getStatus') {
    sendResponse({
      blockingEnabled,
      blockedCount: blockedRequests.length
    });
  }

  return true;
});

// Initialize on startup
initBlocking();
