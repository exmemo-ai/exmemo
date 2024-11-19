<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }" class="chat-container">
        <div class="header">
            <app-navbar :title="$t('chatManagement')" :info="'ChatTools'" />
            <div class="header-buttons">
                <el-button @click="clearSession">{{ $t('clearSession') }}</el-button>
                <el-button @click="newSession">{{ $t('newSession') }}</el-button>
            </div>
        </div>
        <div class="chat-area">
            <vue-advanced-chat height="100%" :current-user-id="chat.getCurrentUserId()"
                :rooms="JSON.stringify(sessions)" :messages="JSON.stringify(messages)" :rooms-loaded="sessionsLoaded"
                :messages-loaded="messagesLoaded" @send-message="sendMessage($event.detail[0])"
                @fetch-messages="fetchMessages($event.detail[0])" />
        </div>
    </div>
</template>

<script>
import { register } from 'vue-advanced-chat'
import { ChatService } from './chat.js'
import AppNavbar from '@/components/support/AppNavbar.vue'

export default ({
    name: 'ChatManager',
    components: {
        AppNavbar
    },

    setup() {
        register()
        const chat = new ChatService()
        return { chat }
    },

    data() {
        return {
            isMobile: false,
            sessionsLoaded: false,
            messagesLoaded: false,
            messages: [],
            sessions: [],
        }
    },

    methods: {
        async fetchMessages(event) {
            this.messagesLoaded = false;
            try {
                const sessionId = event.room?.roomId;
                const sessionName = event.room?.roomName;
                this.chat.setSession(sessionId, sessionName);
                await this.chat.fetchMessages();
            } catch (error) {
                console.error('Error fetching messages:', error);
            }
            this.messagesLoaded = true;
            this.messages = []; // only change messages's point will refresh the chat
            this.messages = this.chat.getMessages();
        },

        async reloadSession() {
            this.sessions = [];
            this.sessions = await this.chat.getSessions();
            this.sessionsLoaded = true;
        },

        async fetchSessions() {
            try {
                await this.chat.fetchSessions()
            } catch (error) {
                console.error('Error fetching sessions:', error)
            }
            this.reloadSession();
        },

        async sendMessage(message) {
            try {
                this.chat.addMessage(message.content, this.chat.currentUserId);
                this.messages = [];
                this.messages = this.chat.getMessages();
                await this.chat.sendMessage(message.content)
                this.messages = [];
                this.messages = this.chat.getMessages();
            } catch (error) {
                console.error('Error sending message:', error)
            }
        },
        async newSession() {
            await this.fetchSessions();
            try {
                await this.chat.newSession()
            } catch (error) {
                console.error('Error creating new session:', error)
            }
            await this.reloadSession();
        },
        async clearSession() {
            try {
                await this.chat.clearSession()
            } catch (error) {
                console.error('Error clearing session:', error)
            }
            await this.reloadSession();
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
    },
    mounted() {
        this.chat.setObj(this);
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();        
        this.fetchSessions();
    }
})
</script>

<style lang="scss">
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.header {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
}

.chat-area {
    flex: 1;
    min-height: 0; // 防止flex子元素溢出
}

html,
body {
    margin: 0;
    height: 100%;
    font-family: 'Quicksand', sans-serif;
}

#app {
    margin: 0;
    text-align: left;
}
</style>
