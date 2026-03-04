/**
 * Content script for Read Receipt extension
 * Injects tracking pixel into Gmail compose window
 */

(function() {
  'use strict';

  const TRACKING_SERVER = 'https://your-server.com';
  let trackingEnabled = true;

  /**
   * Generate a unique UUID for tracking
   * @returns {string} Unique identifier
   */
  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Create tracking pixel element
   * @param {string} uuid - Unique tracking identifier
   * @returns {HTMLImageElement} Tracking pixel
   */
  function createTrackingPixel(uuid) {
    const img = document.createElement('img');
    img.src = `${TRACKING_SERVER}/img/${uuid}`;
    img.width = 1;
    img.height = 1;
    img.style.display = 'none';
    return img;
  }

  /**
   * Inject tracking pixel into email body
   * @param {HTMLElement} emailBody - Email body element
   */
  function injectTrackingPixel(emailBody) {
    if (!trackingEnabled || !emailBody) return;

    const uuid = generateUUID();
    const pixel = createTrackingPixel(uuid);

    emailBody.appendChild(pixel);

    console.log('[ReadReceipt] Tracking pixel injected:', uuid);

    chrome.storage.local.set({ lastTrackedUUID: uuid });
  }

  /**
   * Check if current page is Gmail compose
   * @returns {boolean}
   */
  function isGmailCompose() {
    return window.location.href.includes('mail.google.com') &&
           (window.location.href.includes('#compose') ||
            document.querySelector('[role="dialog"][aria-label*="Compose"]'));
  }

  /**
   * Find Gmail compose email body
   * @returns {HTMLElement|null}
   */
  function findComposeBody() {
    const composeDialog = document.querySelector('[role="dialog"][aria-label*="Compose"]');
    if (!composeDialog) return null;

    return composeDialog.querySelector('[contenteditable="true"][aria-label*="Body"]');
  }

  /**
   * Initialize Gmail observer for compose windows
   */
  function initGmailObserver() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
          if (isGmailCompose()) {
            setTimeout(() => {
              const body = findComposeBody();
              if (body) {
                injectTrackingPixel(body);
              }
            }, 500);
          }
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  /**
   * Load settings from storage
   */
  function loadSettings() {
    chrome.storage.sync.get(['trackingEnabled'], (result) => {
      trackingEnabled = result.trackingEnabled !== false;
      console.log('[ReadReceipt] Tracking enabled:', trackingEnabled);
    });
  }

  /**
   * Listen for messages from background script
   */
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'toggleTracking') {
      trackingEnabled = message.enabled;
      console.log('[ReadReceipt] Tracking toggled:', trackingEnabled);
      sendResponse({ status: 'success' });
    }

    if (message.action === 'getStatus') {
      sendResponse({ enabled: trackingEnabled });
    }

    return true;
  });

  /**
   * Initialize content script
   */
  function init() {
    loadSettings();

    if (window.location.href.includes('mail.google.com')) {
      console.log('[ReadReceipt] Gmail detected, initializing...');
      initGmailObserver();

      if (isGmailCompose()) {
        setTimeout(() => {
          const body = findComposeBody();
          if (body) {
            injectTrackingPixel(body);
          }
        }, 1000);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
