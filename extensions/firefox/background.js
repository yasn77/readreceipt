// Service worker for the extension
console.log("Background service worker started.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("Extension installed.");
});

// Firefox uses browser.browserAction for MV2 extensions
browser.browserAction.onClicked.addListener((tab) => {
  console.log("Action clicked!");
  // Example: Send a message to the content script
  browser.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (tabs[0].id) {
      browser.tabs.sendMessage(tabs[0].id, {greeting: "hello from background"});
    }
  });
});
