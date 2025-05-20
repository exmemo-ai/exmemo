<template>
    <div class="full-container">
        <el-container ref="navbar" style="flex: 0; width: 100%;">
            <app-navbar :title="$t('chatManagement')" :info="'ChatTools'" />
        </el-container>
        <div class="chat-container">
            <vue-advanced-chat
            height="100%" 
            width="100%"
            :current-user-id="chat.getCurrentUserId()" 
            :room-id="activeRoomId"
            :emoji-data-source="chat.getEmojiDataSource()"
            :rooms="JSON.stringify(sessions)" 
            :messages="JSON.stringify(messages)" 
            :rooms-loaded="sessionsLoaded"
            :room-actions="JSON.stringify(roomActions)" 
            @room-action-handler="roomActionHandler($event.detail[0])"
            :messages-loaded="messagesLoaded" 
            @send-message="sendMessage($event.detail[0])"
            @fetch-messages="fetchMessages($event.detail[0])"
            @add-room="newSession"
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
import { useI18n } from 'vue-i18n'


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
        const { t, te } = useI18n();
        const roomActions = ref([
            { name: 'deleteSession', title: t('session.deleteSession') },
            { name: 'renameSession', title: t('session.renameSession') }
        ]);

        return { chat, activeRoomId, t, te, roomActions }
    },

    data() {
        return {
            isMobile: false,
            sessionsLoaded: false,
            messagesLoaded: false,
            messages: [],
            sessions: []
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
                        this.chat.addMessage(this.t('session.sendFile') + `: ${file.name}`, this.chat.currentUserId);
                        this.messages = [];
                        this.messages = this.chat.getMessages();
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
        async clearSession(sessionId = null) {
            try {
                await this.chat.clearSession(sessionId)
            } catch (error) {
                console.error('Error clearing session:', error)
            }
        },
        async renameSession(sessionId) {
            const newSessionName = prompt(this.t('session.newSessionName'));
            if (newSessionName) {
                try {
                    await this.chat.renameSession(sessionId, newSessionName)
                } catch (error) {
                    console.error('Error renaming session:', error)
                }
            }
        },
		roomActionHandler({ action, roomId }) {
            console.log('xxxx', action, 'roomid', roomId)
			switch (action.name) {
				case 'renameSession':                    
                    this.renameSession(roomId);
                    break;
				case 'deleteSession':
                    this.clearSession(roomId);
                    break;
			}
		},        
        handleResize() {
            this.isMobile = window.innerWidth < 768;
            const visualHeight = window.innerHeight;
            const navbarHeight = this.$refs.navbar.$el.offsetHeight;
            document.documentElement.style.setProperty('--mainHeight', `${visualHeight - navbarHeight}px`);
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
        window.addEventListener('unhandledrejection', event => {
            console.log('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', event)
            if (event.reason?.toString().includes('Failed to fetch') && 
                event.reason?.stack?.includes('vue-advanced-chat')) {
                event.preventDefault();
                console.debug('Suppressed vue-advanced-chat error:', event.reason);
            }
        });
    },

    unmounted() {
        eventBus.off('session-updated', this.handleSessionUpdated)
        eventBus.off('message-updated', this.handleMessageUpdated)
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('unhandledrejection', this.handleError);
    }
})
</script>

<style scoped>
.header {
    flex: none;
}

/*这里 height 必须是具体值，否则输入框位置不对，理论上可以与main-container合一*/
.chat-container {
    overflow: hidden;
    height: calc(var(--mainHeight, 100%)) !important;
    width: 100%; 
}

.header-buttons {
    padding: 5px;
}
</style>
