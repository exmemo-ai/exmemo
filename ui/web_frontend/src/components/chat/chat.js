import axios from 'axios';
import FormData from 'form-data';
import { getURL, setDefaultAuthHeader } from '@/components/support/conn';
import defaultAvatar from '@/assets/images/chat.png'
import { useI18n } from 'vue-i18n'

export class ChatService {
    constructor() {
        this.obj = null;
        this.messages = [];
        this.sessions = [];
        const { t } = useI18n();
        this.t = t;
        this.currentUserId = 'user';
        this.currentSessionId = sessionStorage.getItem('sid');
        this.currentSessionName = sessionStorage.getItem('sname');
        //this.currentSessionId = null; // for test
        if (!this.currentSessionId) {
            this.createSession();
        }
        this.botId = 'assistant';
    }

    setObj(obj) {
        this.obj = obj;
    }

    createSession() {
        this.currentSessionId = `${new Date().toISOString().replace('T', ' ').replace(/\.\d+Z/, '')}`;
        this.currentSessionId = this.currentSessionId.slice(0, 19);
        this.currentSessionName = this.currentSessionId;
        sessionStorage.setItem('sid', this.currentSessionId);
        sessionStorage.setItem('sname', this.currentSessionName);
        this.pushSession(this.currentSessionId, this.currentSessionName);
        this.messages = [];
        this.addDefaultMessage();
    }

    pushSession(sessionId, sessionName) {
        const newSession =
        {
            roomId: sessionId,
            roomName: sessionName,
            avatar: defaultAvatar,
            users: [
                { _id: this.currentUserId, username: 'user' },
                { _id: this.botId, username: 'assistant' }
            ]
        }
        this.sessions.unshift(newSession);
    }

    async sendMessage(content) {        
        let info = '';
        try {
            const formData = new FormData();
            formData.append('rtype', 'text');
            formData.append('content', content.trim());
            formData.append('sid', this.currentSessionId);
            formData.append('sname', this.currentSessionName);
            formData.append('source', 'web');
            formData.append('is_group', 'false');

            const func = 'api/message/';
            setDefaultAuthHeader();
            const response = await axios.post(getURL() + func, formData);
            if (response.status === 401) {
                parseBackendError(this.obj, error);
                throw new Error('Token expired');
            }
            info = await this.parseInfo(response);
        } catch (error) {
            info = String(error);
        }
        this.addMessage(info, this.botId);
    }

    addMessage(message, userId, dt = null) {
        if (dt === null) {
            const now = new Date();
            dt = now.toISOString().replace('T', ' ').replace(/\.\d+Z/, '');
        }
        let date = dt.split(' ')[0];
        let timestamp = dt.split(' ')[1].slice(0, 5);
        //timestamp = new Date().toString().substring(16, 21),
        //date = new Date().toDateString()
        const newMessage = {
            _id: this.messages.length,
            content: message,
            senderId: userId,
            date: date,
            timestamp: timestamp
        };
        this.messages.push(newMessage);
    }

    async parseInfo(response) {
        if (response.status === 200) {
            const result = response.data;
            if (result.status === 'success') {
                if (result.info === null) {
                    return '';
                } else if (typeof result.info === 'string') {
                    return result.info;
                }
            }
        }
        return 'Message sending failed';
    }

    async parseMessages(response) {
        if (response.status === 200) {
            const result = response.data;
            if (result.status === 'success') {
                if (result.info === null) {
                    return;
                } else if (typeof result.info === 'string') {
                    console.log('parseMessages return info', result.info);
                } else if (Array.isArray(result.info)) {
                    this.messages = [];
                    for (const item of result.info) {
                        //console.log('item', item);
                        this.addMessage(item.content, item.sender, item.created_time);
                    }
                }
            }
        }
    }

    async parseSessions(response) {
        if (response.status === 200) {
            const result = response.data;
            if (result.status === 'success') {
                this.sessions = [];
                if (Array.isArray(result.info)) {
                    for (const item of result.info) {
                        this.pushSession(item.sid, item.sname);
                    }
                }
            }
        }
    }

    async fetchSessions() {
        try {
            const formData = new FormData();
            formData.append('rtype', 'get_sessions');

            const func = 'api/message/';
            setDefaultAuthHeader();
            const response = await axios.post(getURL() + func, formData);
            if (response.status === 401) {
                parseBackendError(this.obj, error);
                throw new Error('Token expired');
            }
            await this.parseSessions(response);
        } catch (error) {
            const error_str = String(error);
            this.addMessage(error_str, this.botId);
        }
    }

    async fetchMessages() {
        try {
            const formData = new FormData();
            formData.append('rtype', 'get_messages');
            formData.append('sid', this.currentSessionId);

            const func = 'api/message/';
            setDefaultAuthHeader();
            const response = await axios.post(getURL() + func, formData);
            if (response.status === 401) {
                parseBackendError(this.obj, error);
                throw new Error('Token expired');
            }
            await this.parseMessages(response);
        } catch (error) {
            const error_str = String(error);
            this.addMessage(error_str, this.botId);
        }
        this.addDefaultMessage();
    }

    addDefaultMessage() {
        if (this.messages.length === 0) {
            this.addMessage(this.t('letsChat'), this.botId);
        }
    }

    setSession(sessionId, sessionName) {
        this.currentSessionId = sessionId;
        this.currentSessionName = sessionName;
    }

    getCurrentUserId() {
        return this.currentUserId;
    }

    getSessions() {
        return this.sessions;
    }

    getMessages() {
        return this.messages;
    }

    async clearSession() {
        try {
            const formData = new FormData();
            formData.append('rtype', 'clear_session');
            formData.append('sid', this.currentSessionId);

            const func = 'api/message/';
            setDefaultAuthHeader();
            const response = await axios.post(getURL() + func, formData);
            if (response.status === 401) {
                parseBackendError(this.obj, error);
                throw new Error('Token expired');
            }
            info = await this.parseInfo(response);
        } catch (error) {
            const error_str = String(error);
            this.addMessage(error_str, this.botId);
        }
        await this.fetchSessions();
        this.createSession();
    }

    async newSession() {
        try {
            const formData = new FormData();
            formData.append('rtype', 'save_session');
            formData.append('sid', this.currentSessionId);
            const func = 'api/message/';
            setDefaultAuthHeader();
            const response = await axios.post(getURL() + func, formData);
            if (response.status === 401) {
                parseBackendError(this.obj, error);
                throw new Error('Token expired');
            }
            await this.parseSessions(response);
        } catch (error) {
            const error_str = String(error);
            this.addMessage(error_str, this.botId);
        }
        await this.fetchSessions();
        this.createSession();
    }
}