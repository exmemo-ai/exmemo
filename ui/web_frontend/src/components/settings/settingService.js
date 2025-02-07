import axios from 'axios';
import { getURL, setDefaultAuthHeader } from '@/components/support/conn';

class SettingService {
    constructor() {
        this._settingCache = null;
        this._pendingSettings = null;
        this._isLocked = false;
        this._waitQueue = [];
    }

    static _instance = null;

    static getInstance() {
        if (!SettingService._instance) {
            SettingService._instance = new SettingService();
        }
        return SettingService._instance;
    }

    async _acquireLock() {
        if (this._isLocked) {
            await new Promise(resolve => this._waitQueue.push(resolve));
        }
        this._isLocked = true;
    }

    _releaseLock() {
        this._isLocked = false;
        const next = this._waitQueue.shift();
        if (next) next();
    }

    async loadSetting(force = false) {
        try {
            if (!force && this._settingCache) {
                return this._settingCache;
            }    
            await this._acquireLock();
            setDefaultAuthHeader();
            const formData = new FormData();
            formData.append('rtype', 'get_setting');
            const response = await axios.post(getURL() + 'api/setting/', formData);
            this._settingCache = response.data;
            this._pendingSettings = JSON.parse(JSON.stringify(response.data));
        } finally {
            this._releaseLock();
        }
        return this._settingCache;
    }

    getSettingCache() {
        return this._settingCache;
    }

    getPendingSettings() {
        return this._pendingSettings;
    }

    async saveSetting() {
        setDefaultAuthHeader();
        const formData = new FormData();
        formData.append('rtype', 'save');
        for (const [key, value] of Object.entries(this._pendingSettings.setting)) {
            formData.append(key, value);
        }
        const response = await axios.post(getURL() + 'api/setting/', formData);
        await this.loadSetting(true);
        return response.data;
    }

    async resetSetting() {
        setDefaultAuthHeader();
        const formData = new FormData();
        formData.append('rtype', 'reset');
        const response = await axios.post(getURL() + 'api/setting/', formData);
        await this.loadSetting(true);
        return response.data;
    }

    getSetting(key) {
        if (!this._settingCache) {
            return null;
        }
        if (key in this._settingCache.setting) {
            return this._settingCache.setting[key];
        }
        return null;
    }

    getPendingSetting(key) {
        if (!this._pendingSettings) {
            return null;
        }
        if (key in this._pendingSettings.setting) {
            return this._pendingSettings.setting[key];
        }
        return null;
    }

    setSetting(key, value) {
        console.log('setSetting', key, value);
        if (!this._pendingSettings) {
            return;
        }
        this._pendingSettings.setting[key] = value;
    }

    resetPendingSetting() {
        this._pendingSettings = JSON.parse(JSON.stringify(this._settingCache));
    }
}

export default SettingService;
