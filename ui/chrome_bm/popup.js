document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('appName').innerText = chrome.i18n.getMessage('appName');
    document.getElementById('syncButton').innerText = chrome.i18n.getMessage('syncButton');

    document.getElementById('syncButton').addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: "syncBookmarks" });
    });

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "showError") {
            const errorMessage = request.message;
            alert(errorMessage);
        }
    });
});