// Service worker for the extension
console.log("Background service worker started.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("Extension installed.");
});

chrome.action.onClicked.addListener((tab) => {
  console.log("Action clicked!");
  // Example: Send a message to the content script
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (tabs[0].id) {
      chrome.tabs.sendMessage(tabs[0].id, {greeting: "hello from background"});
    }
  });
});
