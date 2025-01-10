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
            <vue-advanced-chat height="100%" :current-user-id="chat.getCurrentUserId()" :room-id="activeRoomId"
                :rooms="JSON.stringify(sessions)" :messages="JSON.stringify(messages)" :rooms-loaded="sessionsLoaded"
                :messages-loaded="messagesLoaded" @send-message="sendMessage($event.detail[0])"
                @fetch-messages="fetchMessages($event.detail[0])"
                :show-audio=false />
        </div>
    </div>
</template>

<script>
import { register } from 'vue-advanced-chat'
import { ChatService } from './chat.js'
import AppNavbar from '@/components/support/AppNavbar.vue'
import mitt from 'mitt'
import { ref } from 'vue';

const eventBus = mitt()

export default ({
    name: 'ChatManager',
    components: {
        AppNavbar
    },

    setup() {
        register()
        const chat = new ChatService(eventBus);
        const activeRoomId = ref(null);
        return { chat, activeRoomId }
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
        handleMessageUpdated(messages) {
            this.messages = messages;
        },
        async handleSessionUpdated(sessions) {
            this.sessions = sessions;
            this.activeRoomId = this.chat.currentSessionId;
            this.sessionsLoaded = true;
        },
        async fetchMessages(event) {
            this.messagesLoaded = false;
            try {
                const sessionId = event.room?.roomId;
                this.chat.setSession(sessionId);
                await this.chat.fetchMessages();
            } catch (error) {
                console.error('Error fetching messages:', error);
            }
            this.messagesLoaded = true;
        },

        async fetchSessions() {
            try {
                await this.chat.fetchSessions()
            } catch (error) {
                console.error('Error fetching sessions:', error)
            }
        },

        async sendMessage(message) {
            try {
                console.warn('message', message)
                if (message.content && message.content.length > 0) {
                    this.chat.addMessage(message.content, this.chat.currentUserId);
                    this.messages = [];
                    this.messages = this.chat.getMessages();
                    await this.chat.sendMessage(message.content)
                    this.messages = [];
                    this.messages = this.chat.getMessages();
                } else if (message.files && message.files.length > 0) {
                    for (let i = 0; i < message.files.length; i++) {
                        const file = message.files[i];                        
                        // 添加文件消息到本地显示
                        this.chat.addMessage(`正在发送文件: ${file.name}`, this.chat.currentUserId);
                        this.messages = [];
                        this.messages = this.chat.getMessages();
                        
                        // 发送文件到后端
                        await this.chat.uploadFile(file);
                        
                        this.messages = [];
                        this.messages = this.chat.getMessages();
                    }
                }
            } catch (error) {
                console.error('Error sending message:', error)
            }
        },

        async newSession() {
            try {
                await this.chat.newSession()
            } catch (error) {
                console.error('Error creating new session:', error)
            }
        },
        async clearSession() {
            try {
                await this.chat.clearSession()
            } catch (error) {
                console.error('Error clearing session:', error)
            }
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
    },
    mounted() {
        eventBus.on('session-updated', this.handleSessionUpdated)
        eventBus.on('message-updated', this.handleMessageUpdated)
        this.chat.setObj(this);
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
        this.fetchSessions();
    },

    unmounted() {
        eventBus.off('session-updated', this.handleSessionUpdated)
        eventBus.off('message-updated', this.handleMessageUpdated)
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
