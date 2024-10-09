let isFirstInstall = false;

chrome.runtime.onInstalled.addListener((details) => {
    console.log('Extension installed');
    chrome.contextMenus.create({
        id: "syncBookmarks",
        title: chrome.i18n.getMessage('appName'), // 上下文菜单项标题
        contexts: ["action"]
    });
    if (details.reason === "install") {
        chrome.runtime.openOptionsPage();
        isFirstInstall = true;
        }
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "syncBookmarks") {
        syncBookmarks(); // 触发书签同步功能
    }
});

function syncBookmarks() {
    if (isFirstInstall) {
        console.log('Skipping sync on first install');
        return;
    }
    const title = chrome.i18n.getMessage('appName'); // 通知标题
    const message = chrome.i18n.getMessage('syncMessage');
    showNotification(title, message, true);
    chrome.bookmarks.getTree((bookmarkTreeNodes) => {
        console.log(bookmarkTreeNodes);   
        sendBookmarksToServer(bookmarkTreeNodes);
    });
} // 获取书签树并调用发送书签到服务器的函数

function convertBookmarksToArray(bookmarksTree, parentPath = '') {
    if (!bookmarksTree) {
        console.error('bookmarksTree is undefined');
        return [];
    }

    const bookmarksArray = [];
    bookmarksTree.forEach(bookmark => {
        const currentPath = parentPath ? `${parentPath}/${bookmark.title}` : bookmark.title;

        if (bookmark.url) {
            // console.log('Bookmark:', bookmark); // 打印书签属性
            const addDate = bookmark.dateAdded ? new Date(parseInt(bookmark.dateAdded)).toISOString() : null;
            bookmarksArray.push({
                title: bookmark.title,
                url: bookmark.url,
                add_date: addDate,
                path: currentPath
            });
        } else if (bookmark.children) {
            // 递归处理子书签
            bookmarksArray.push(...convertBookmarksToArray(bookmark.children, currentPath));
        }
    });
    return bookmarksArray;
}

function getToken(addr, username, password) {
    return fetch(`${addr}/api/auth/login/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username, password: password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.token) {
            return data.token;
        } else {
            throw new Error('Token not found in response');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        throw error;
    });
}

let bookmarksToSyncCount = 0;
let bookmarksSyncedCount = 0;

function sendBookmarksToServer(bookmarks) {
    bookmarksToSyncCount = bookmarks.length;
    bookmarksSyncedCount = 0;

    chrome.storage.sync.get(['addr', 'username', 'password'], (items) => {
        const addr = items.addr || 'http://localhost:8005';
        const username = items.username || 'guest'; 
        const password = items.password || 'guest'; 
        getToken(addr, username, password)
        .then(token => {
            const bookmarksArray = convertBookmarksToArray(bookmarks);
            const Token = 'Token ' + token;

            console.log('Sending bookmarks to server:', JSON.stringify(bookmarksArray, null, 2)); // 打印发送服务器前的书签
            
            return fetch(`${addr}/api/bookmarks/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': Token 
                },
                body: JSON.stringify(bookmarksArray)
            });
        })
        .then(response => {
            if (!response.ok) {
                console.error('Response Error:', response.status, response.statusText);
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json(); // 只调用一次 response.json()
        })
        .then(data => {
            console.log('Success:', data);
            bookmarksSyncedCount++;
            if (bookmarksSyncedCount === bookmarksToSyncCount) {
                const title = chrome.i18n.getMessage('appName'); // 使用 appName 作为通知标题
                const message = chrome.i18n.getMessage('syncCompleteMessage'); // 使用 syncCompleteMessage 作为通知内容
                showNotification(title, message, false); //手动关闭
            }
        })
        .catch(error => {
            console.error('Error:', error);
            chrome.runtime.sendMessage({ action: "showError", message: error.message });
        });
    });
}

function showNotification(title, message, autoClose = false) {
    if (chrome.notifications) {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'images/icon-48.png',
            title: title,
            message: message,
            buttons: autoClose ? [] : [{ title: chrome.i18n.getMessage('closeButton') }]  // 根据 autoClose 参数决定是否添加关闭按钮
        }, function(notificationId) {
            if (autoClose) {
                setTimeout(() => {
                    chrome.notifications.clear(notificationId);
                }, 5000);  // 自动关闭时间设为5秒
            } else {
                // 监听通知按钮点击事件
                chrome.notifications.onButtonClicked.addListener(function(notifId, btnIdx) {
                    if (notifId === notificationId && btnIdx === 0) {
                        chrome.notifications.clear(notificationId);
                    }
                });

                // 监听通知点击事件
                chrome.notifications.onClicked.addListener(function(notifId) {
                    if (notifId === notificationId) {
                        chrome.notifications.clear(notificationId);
                    }
                });
            }
        });
    } else {
        console.error('Notifications API is not available.');
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "syncBookmarks") {
        syncBookmarks();
        sendResponse({ status: "Sync initiated" });
    }
});

// 监听书签事件 增删改移
chrome.bookmarks.onCreated.addListener(syncBookmarks);
chrome.bookmarks.onRemoved.addListener(syncBookmarks);
chrome.bookmarks.onChanged.addListener(syncBookmarks);
chrome.bookmarks.onMoved.addListener(syncBookmarks);