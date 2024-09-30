document.addEventListener('DOMContentLoaded', () => {
    const ipInput = document.getElementById('addr');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const saveButton = document.getElementById('save');

    // 加载用户之前保存的设置
    chrome.storage.sync.get(['addr', 'username', 'password'], (items) => {
        console.log('Loaded settings:', items);
        ipInput.value = items.addr || 'http://localhost:8005';
        usernameInput.value = items.username || 'guest';
        passwordInput.value = items.password || 'guest';
    });

    // 保存设置
    saveButton.addEventListener('click', () => {
        const addr = ipInput.value;
        const username = usernameInput.value;
        const password = passwordInput.value;
        console.log('Saving settings:', { addr, username, password });
        chrome.storage.sync.set({ addr, username, password }, () => {
            console.log('Settings saved:', { addr, username, password });
            alert(chrome.i18n.getMessage('settingsSaved'));
        });
    });

    // 设置国际化文本
    document.getElementById('appName').innerText = chrome.i18n.getMessage('appName');
    document.getElementById('ipAddress').innerText = chrome.i18n.getMessage('ipAddress');
    document.getElementById('username').innerText = chrome.i18n.getMessage('username');
    document.getElementById('password').innerText = chrome.i18n.getMessage('password');
    document.getElementById('save').innerText = chrome.i18n.getMessage('saveSettings');
});