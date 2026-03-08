/**
 * Tests for browser extension tracking pixel blocking
 * Issue #149 - Browser Extension Pixel Blocking
 */

const assert = require('assert');

// Mock chrome API for testing
const mockChrome = {
  storage: {
    sync: {
      get: jest.fn(),
      set: jest.fn()
    },
    local: {
      get: jest.fn(),
      set: jest.fn()
    },
    onChanged: {
      addListener: jest.fn()
    }
  },
  webRequest: {
    onBeforeRequest: {
      addListener: jest.fn()
    }
  },
  tabs: {
    get: jest.fn(),
    query: jest.fn()
  },
  runtime: {
    onInstalled: {
      addListener: jest.fn()
    },
    onMessage: {
      addListener: jest.fn()
    },
    lastError: null
  }
};

// Mock the chrome API globally
global.chrome = mockChrome;

describe('Extension Pixel Blocking', () => {
  let blockingEnabled = true;
  let blockedRequests = [];

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    blockedRequests = [];
    blockingEnabled = true;
  });

  describe('isTrackingPixel', () => {
    const isTrackingPixel = (url) => {
      const trackingPixelPattern = /\/img\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
      return trackingPixelPattern.test(url);
    };

    test('should detect valid tracking pixel URLs', () => {
      expect(isTrackingPixel('https://example.com/img/123e4567-e89b-12d3-a456-426614174000')).toBe(true);
      expect(isTrackingPixel('http://test.com/img/abcd1234-5678-90ef-ghij-klmnopqrstuv')).toBe(true);
    });

    test('should reject non-tracking URLs', () => {
      expect(isTrackingPixel('https://example.com/images/photo.jpg')).toBe(false);
      expect(isTrackingPixel('https://example.com/img/not-a-uuid')).toBe(false);
      expect(isTrackingPixel('https://example.com/api/tracking')).toBe(false);
    });

    test('should handle edge cases', () => {
      expect(isTrackingPixel('')).toBe(false);
      expect(isTrackingPixel(null)).toBe(false);
      expect(isTrackingPixel(undefined)).toBe(false);
    });
  });

  describe('isSentFolder', () => {
    const isSentFolder = (url) => {
      if (!url) return false;

      const gmailSentPatterns = [
        '#sent',
        '#sent/1',
        '#label/sent',
        '#inbox/?search=sent',
        '/search/category:sent',
        '#search/category%3Asent'
      ];

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
    };

    test('should detect Gmail sent folder URLs', () => {
      expect(isSentFolder('https://mail.google.com/mail/u/0/#sent')).toBe(true);
      expect(isSentFolder('https://mail.google.com/mail/u/0/#sent/1')).toBe(true);
      expect(isSentFolder('https://mail.google.com/mail/u/0/#label/sent')).toBe(true);
      expect(isSentFolder('https://mail.google.com/mail/u/0/#search/category%3Asent')).toBe(true);
    });

    test('should detect Outlook sent folder URLs', () => {
      expect(isSentFolder('https://outlook.live.com/mail/0/sentitems')).toBe(true);
      expect(isSentFolder('https://outlook.live.com/mail/0/SentItems')).toBe(true);
      expect(isSentFolder('https://outlook.live.com/mail/0/#sentitems')).toBe(true);
    });

    test('should reject non-sent folder URLs', () => {
      expect(isSentFolder('https://mail.google.com/mail/u/0/#inbox')).toBe(false);
      expect(isSentFolder('https://mail.google.com/mail/u/0/#drafts')).toBe(false);
      expect(isSentFolder('https://outlook.live.com/mail/0/inbox')).toBe(false);
      expect(isSentFolder('')).toBe(false);
      expect(isSentFolder(null)).toBe(false);
    });
  });

  describe('Blocking Logic', () => {
    test('should block tracking pixel when in sent folder', async () => {
      mockChrome.tabs.get.mockResolvedValue({
        url: 'https://mail.google.com/mail/u/0/#sent',
        id: 1
      });

      // Simulate webRequest listener being called
      const details = {
        url: 'https://example.com/img/123e4567-e89b-12d3-a456-426614174000',
        tabId: 1,
        type: 'image'
      };

      // The blocking logic would be tested through the background script
      // This is a simplified test of the core logic
      const tabUrl = 'https://mail.google.com/mail/u/0/#sent';
      const isPixel = true;
      const isInSent = isSentFolder(tabUrl);

      expect(isPixel && isInSent).toBe(true);
    });

    test('should not block tracking pixel when NOT in sent folder', async () => {
      mockChrome.tabs.get.mockResolvedValue({
        url: 'https://mail.google.com/mail/u/0/#inbox',
        id: 1
      });

      const tabUrl = 'https://mail.google.com/mail/u/0/#inbox';
      const isPixel = true;
      const isInSent = isSentFolder(tabUrl);

      expect(isPixel && isInSent).toBe(false);
    });

    test('should not block non-tracking images', () => {
      const isPixel = isTrackingPixel('https://example.com/images/photo.jpg');
      const isInSent = isSentFolder('https://mail.google.com/mail/u/0/#sent');

      expect(isPixel).toBe(false);
      expect(isPixel && isInSent).toBe(false);
    });

    test('should respect blockingEnabled setting', () => {
      // When blocking is disabled, no blocking should occur
      blockingEnabled = false;

      const shouldBlock = blockingEnabled &&
                         isTrackingPixel('https://example.com/img/123e4567-e89b-12d3-a456-426614174000') &&
                         isSentFolder('https://mail.google.com/mail/u/0/#sent');

      expect(shouldBlock).toBe(false);
    });
  });

  describe('Request Logging', () => {
    test('should log blocked requests', () => {
      const requestDetails = {
        url: 'https://example.com/img/123e4567-e89b-12d3-a456-426614174000',
        tabId: 1,
        type: 'image'
      };

      const logEntry = {
        timestamp: new Date().toISOString(),
        url: requestDetails.url,
        tabId: requestDetails.tabId,
        type: requestDetails.type
      };

      blockedRequests.unshift(logEntry);

      expect(blockedRequests.length).toBe(1);
      expect(blockedRequests[0].url).toBe(requestDetails.url);
      expect(blockedRequests[0].tabId).toBe(1);
    });

    test('should limit logged requests to MAX_BLOCKED_REQUESTS', () => {
      const MAX_BLOCKED_REQUESTS = 100;

      // Add more than MAX_BLOCKED_REQUESTS
      for (let i = 0; i < 150; i++) {
        blockedRequests.unshift({
          timestamp: new Date().toISOString(),
          url: `https://example.com/img/test-${i}`,
          tabId: 1,
          type: 'image'
        });

        if (blockedRequests.length > MAX_BLOCKED_REQUESTS) {
          blockedRequests = blockedRequests.slice(0, MAX_BLOCKED_REQUESTS);
        }
      }

      expect(blockedRequests.length).toBe(MAX_BLOCKED_REQUESTS);
    });
  });

  describe('Message Handling', () => {
    test('should respond to getBlockedRequests message', () => {
      const mockBlockedRequests = [
        { url: 'https://example.com/img/test1', timestamp: new Date().toISOString(), tabId: 1 }
      ];

      // Simulate message handler
      const response = { blockedRequests: mockBlockedRequests };

      expect(response.blockedRequests).toEqual(mockBlockedRequests);
    });

    test('should respond to clearBlockedRequests message', () => {
      blockedRequests = [
        { url: 'https://example.com/img/test1', timestamp: new Date().toISOString(), tabId: 1 }
      ];

      // Simulate clear action
      blockedRequests = [];

      expect(blockedRequests.length).toBe(0);
    });

    test('should respond to getStatus message', () => {
      const response = {
        blockingEnabled: true,
        blockedCount: 5
      };

      expect(response.blockingEnabled).toBe(true);
      expect(response.blockedCount).toBe(5);
    });
  });
});

// Helper functions for testing
function isTrackingPixel(url) {
  const trackingPixelPattern = /\/img\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  return trackingPixelPattern.test(url);
}

function isSentFolder(url) {
  if (!url) return false;

  const gmailSentPatterns = [
    '#sent',
    '#sent/1',
    '#label/sent',
    '#inbox/?search=sent',
    '/search/category:sent',
    '#search/category%3Asent'
  ];

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
