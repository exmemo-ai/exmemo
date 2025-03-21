<template>
    <el-container class="nav-container">
        <div class="top-row">
            <div class="title-container">
                <img :src="logo" class="nav-avatar" />
                <h3 class="title">{{ appName }}</h3>
            </div>
            <div class="user-controls">
                <el-dropdown v-if="isLogin" trigger="click">
                    <div class="user-dropdown-trigger">
                        <el-avatar :size="32" :src="userAvatar">
                            {{ login_user.charAt(0).toUpperCase() }}
                        </el-avatar>
                        <span class="username">{{ login_user }}</span>
                        <el-icon>
                            <ArrowDown />
                        </el-icon>
                    </div>
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item v-if="info !== 'Setting'" @click="gotoUserSetting">
                                <el-icon>
                                    <Setting />
                                </el-icon>
                                <span>{{ $t('userSetting') }}</span>
                            </el-dropdown-item>
                            <el-dropdown-item @click="openGitHub">
                                <el-icon>
                                    <Link />
                                </el-icon>
                                <span>{{ $t('mainPage') }}</span>
                            </el-dropdown-item>
                            <el-dropdown-item divided @click="logoutFunc">
                                <el-icon>
                                    <SwitchButton />
                                </el-icon>
                                <span>{{ $t('logout') }}</span>
                            </el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
                <el-button v-else type="primary" plain @click="loginFunc">
                    {{ $t('login') }}
                </el-button>
            </div>
        </div>
        <div class="bottom-row" style="width:100%; display: flex;">
            <el-tabs v-model="activeTab" @tab-click="handleTabClick" >
                <el-tab-pane name="ChatTools" :label="$t('chatTools')"></el-tab-pane>
                <el-tab-pane name="DataManager" :label="$t('dataManager')"></el-tab-pane>
                <el-tab-pane name="ReadingTools" :label="$t('learnTools')"></el-tab-pane>
                <el-tab-pane name="BMManager" :label="$t('bookmarkManager')"></el-tab-pane>
                <!--<el-tab-pane name="SupportTools" :label="$t('assistantTools')"></el-tab-pane>-->
            </el-tabs>
            <el-icon class="clipboard-icon" @click="openClipboard" size="small" :title="$t('paste.openClipboard')">
                <ClipboardIcon />
            </el-icon>
        </div>
        <el-dialog
            v-model="dialogVisible"
            :title="$t('paste.pasteDlgTitle')"
            width="80%"
            :close-on-click-modal="false"
        >
            <el-input
                v-model="pastedContent"
                type="textarea"
                :rows="3"
                :placeholder="$t('paste.pastePlaceholder')"
            />
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">{{ $t('cancel') }}</el-button>
                    <el-button type="primary" @click="handlePastedContent">
                        {{ $t('confirm') }}
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </el-container>
</template>

<script>
import logo from '@/assets/images/logo.png'
import axios from 'axios';
import { setDefaultAuthHeader,getURL } from './conn';
import { Setting, ArrowDown, SwitchButton, Link } from '@element-plus/icons-vue'
import ClipboardIcon from '@/components/icons/ClipboardIcon.vue'

export default {
    name: 'AppNavbar',
    components: {
        Setting,
        ArrowDown,
        SwitchButton,
        ClipboardIcon,
        Link
    },
    props: {
        title: {
            type: String,
            required: true
        },
        info: {
            type: String,
            default: 'DataManager'
        }
    },
    data() {
        return {
            appName: 'ExMemo',
            logo: logo,
            isLogin: false,
            login_user: '',
            activeTab: 'DataManager',
            userAvatar: '',
            dialogVisible: false,
            pastedContent: '',
        };
    },
    methods: {
        gotoUserSetting() {
            this.$router.push('/user_setting');
        },
        gotoChat() {
            this.$router.push('/chat');
        },
        gotoReader() {
            this.$router.push('/translate');
        },
        gotoAssistant() {
            this.$router.push('/support_tools');
        },
        gotoDataManager() {
            this.$router.push('/data');
        },
        gotoBMManager() {
            this.$router.push('/bm_manager'); 
        },
        async openClipboard() {
            try {
                if (!navigator?.clipboard) {
                    this.showPasteDialog();
                    return;
                }

                if (navigator.permissions) {
                    const result = await navigator.permissions.query({ name: 'clipboard-read' });
                    if (result.state === 'denied') {
                        this.showPasteDialog();
                        return;
                    }
                }
                const text = await navigator.clipboard.readText();
                this.processContent(text);
            } catch (err) {
                console.error('Clipboard error:', err);
                this.showPasteDialog();
            }
        },
        
        showPasteDialog() {
            this.pastedContent = '';
            this.dialogVisible = true;
        },

        handlePastedContent() {
            if (!this.pastedContent) {
                this.$message({
                    type: 'warning',
                    message: this.$t('paste.contentEmpty')
                });
                return;
            }
            this.processContent(this.pastedContent, true);
            this.dialogVisible = false;
        },

        processContent(content, onlyURL = false) {
            if (content.startsWith('http')) {
                window.open(`/view_markdown?url=${content}`, '_blank');
            } else if (content.length > 0 && !onlyURL) {
                window.open(`/edit_markdown`, '_blank');
            } else {
                this.$message({
                    type: 'warning',
                    message: this.$t('paste.contentNotSupport')
                });
            }
        },
        loginFunc() {
            this.$router.push('/login');
        },
        logoutFunc() {
            console.log("Logout button clicked!");
            if (localStorage.getItem('username') === null) {
                this.$message({
                    type: 'error',
                    message: this.$t('notLoggedIn')
                })
                return;
            }
            try {
                axios.post(getURL() + "api/auth/logout/");
                this.$message({
                    type: 'success',
                    message: this.$t('logoutSuccess'),
                })
            } catch (error) {
                this.$message({
                    type: 'warning',
                    message: this.$t('logoutFailed', { error: error.response.data }),
                })
            }
            localStorage.removeItem('username');
            delete axios.defaults.headers.common['Authorization'];
            this.isLogin = false;
            this.$router.push('/login');
        },
        checkLogin() {
            setDefaultAuthHeader();
            console.log('Checking login status');
            if (localStorage.getItem('username') !== null) {
                console.log('Logged in');
                this.login_user = localStorage.getItem('username');
                this.isLogin = true;
                return true;
            } else {
                console.log('Not logged in');
                this.isLogin = false;
                return false;
            }
        },
        handleTabClick(tab) {
            switch (tab.props.name) {
                case 'ChatTools':
                    this.gotoChat();
                    break;
                case 'DataManager':
                    this.gotoDataManager();
                    break;
                case 'ReadingTools':
                    this.gotoReader();
                    break;
                case 'SupportTools':
                    this.gotoAssistant();
                    break;
                case 'BMManager':
                    this.gotoBMManager();
                    break;
            }
        },
        openGitHub() {
            window.open('https://github.com/exmemo-ai/exmemo', '_blank');
        },
    },
    watch: {
        info: {
            immediate: true,
            handler(newInfo) {
                this.activeTab = newInfo;
            }
        }
    },
    mounted() {
        this.isLogin = this.checkLogin(this);
        if (this.isLogin) {
            this.login_user = localStorage.getItem('username');
        }
        this.activeTab = this.info; // 初始化选中状态
    },
    beforeDestroy() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        window.removeEventListener('resize', this.resetSelectionWidth);
    }
}
</script>

<style scoped>


.user-controls {
    display: flex;
    align-items: center;
}

.bottom-row {
    display: flex;
    align-items: center;
}

.el-tabs {
    margin-right: 5px;
}

:deep(.el-tabs__header) {
    margin-bottom: 0;
}

.user-controls .el-button.is-circle {
    margin-right: 10px;
}

.user-dropdown-trigger {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 2px 8px;
    border-radius: 20px;
    transition: background-color 0.3s;
}

.user-dropdown-trigger:hover {
    background-color: var(--el-fill-color-light);
}

.username {
    margin: 0 8px;
    font-size: 14px;
    color: var(--el-text-color-primary);
}

:deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 8px;
}

:deep(.el-dropdown-menu__item .el-icon) {
    margin-right: 4px;
}

.el-avatar {
    background: var(--el-color-primary);
    color: white;
    font-weight: bold;
}

@media screen and (max-width: 768px) {
    .username {
        display: none;
    }

    .user-dropdown-trigger {
        padding: 2px;
    }

    :deep(.el-tabs__item) {
        padding: 0 5px !important;
        font-size: 14px;
    }

    .clipboard-icon {
        margin: 0 5px !important;
    }
}

.clipboard-icon {
    margin-right: 30px;
    margin-left: 30px;
    cursor: pointer;
    font-size: 20px;
    color: var(--el-text-color-primary);
}

.clipboard-icon:hover {
    color: var(--el-color-primary);
}
</style>
