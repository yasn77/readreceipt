/**
 * Popup script for Read Receipt extension (Firefox)
 * Displays blocked requests and settings
 */

document.addEventListener('DOMContentLoaded', () => {
  const blockingToggle = document.getElementById('blockingToggle');
  const trackingToggle = document.getElementById('trackingToggle');
  const blockedList = document.getElementById('blockedList');
  const blockedCount = document.getElementById('blockedCount');
  const blockedCountSmall = document.getElementById('blockedCountSmall');
  const clearBtn = document.getElementById('clearBtn');
  const statusBadge = document.getElementById('statusBadge');

  /**
   * Format timestamp to readable time
   * @param {string} timestamp - ISO timestamp
   * @returns {string}
   */
  function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute ago
    if (diff < 60000) {
      return 'Just now';
    }
    // Less than 1 hour ago
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    }
    // Less than 24 hours ago
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    }
    // Older
    return date.toLocaleDateString();
  }

  /**
   * Render blocked requests list
   * @param {Array} requests - Array of blocked request objects
   */
  function renderBlockedList(requests) {
    if (requests.length === 0) {
      blockedList.innerHTML = `
        <div class="empty-state">
          No tracking pixels blocked yet.
          <br>
          Pixels will be blocked when you view your sent emails.
        </div>
      `;
      clearBtn.style.display = 'none';
      return;
    }

    blockedList.innerHTML = requests.map(req => {
      // Extract just the UUID from the URL for display
      const urlParts = req.url.split('/img/');
      const uuid = urlParts[1] ? urlParts[1].substring(0, 8) + '...' : 'unknown';
      
      return `
        <div class="blocked-item">
          <span class="blocked-url" title="${req.url}">/img/${uuid}</span>
          <span class="blocked-time">${formatTime(req.timestamp)}</span>
        </div>
      `;
    }).join('');

    clearBtn.style.display = 'block';
  }

  /**
   * Update UI with current status
   */
  function updateStatus() {
    chrome.runtime.sendMessage({ action: 'getStatus' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error getting status:', chrome.runtime.lastError);
        return;
      }

      blockingToggle.checked = response.blockingEnabled;
      blockedCount.textContent = response.blockedCount;
      blockedCountSmall.textContent = `(${response.blockedCount})`;

      if (response.blockingEnabled) {
        statusBadge.textContent = 'Active';
        statusBadge.className = 'status-badge status-active';
      } else {
        statusBadge.textContent = 'Inactive';
        statusBadge.className = 'status-badge status-inactive';
      }
    });

    chrome.runtime.sendMessage({ action: 'getBlockedRequests' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error getting blocked requests:', chrome.runtime.lastError);
        return;
      }

      renderBlockedList(response.blockedRequests || []);
    });
  }

  /**
   * Toggle blocking setting
   */
  blockingToggle.addEventListener('change', () => {
    chrome.storage.sync.set({ blockingEnabled: blockingToggle.checked }, () => {
      console.log('[ReadReceipt] Blocking enabled set to:', blockingToggle.checked);
      updateStatus();
    });
  });

  /**
   * Toggle tracking injection setting
   */
  trackingToggle.addEventListener('change', () => {
    chrome.storage.sync.set({ trackingEnabled: trackingToggle.checked }, () => {
      console.log('[ReadReceipt] Tracking enabled set to:', trackingToggle.checked);
      
      // Notify content script
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0] && tabs[0].id) {
          chrome.tabs.sendMessage(tabs[0].id, {
            action: 'toggleTracking',
            enabled: trackingToggle.checked
          });
        }
      });
    });
  });

  /**
   * Clear blocked requests log
   */
  clearBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'clearBlockedRequests' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error clearing blocked requests:', chrome.runtime.lastError);
        return;
      }

      updateStatus();
    });
  });

  // Initial status update
  updateStatus();
});
