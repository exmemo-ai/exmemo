<template>
    <el-container class="navbar-container nav-container">
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
        <div class="bottom-row">
            <el-tabs v-model="activeTab" @tab-click="handleTabClick">
                <el-tab-pane name="DataManager" :label="$t('dataManager')"></el-tab-pane>
                <el-tab-pane name="ChatTools" :label="$t('chatTools')"></el-tab-pane>
                <el-tab-pane name="SupportTools" :label="$t('assistantTools')"></el-tab-pane>
                <el-tab-pane name="ReadingTools" :label="$t('readingTools')"></el-tab-pane>
                <el-tab-pane name="BMManager" :label="$t('bookmarkManager')"></el-tab-pane> 
            </el-tabs>
        </div>
    </el-container>
</template>

<script>
import logo from '@/assets/images/logo.png'
import axios from 'axios';
import { setDefaultAuthHeader,getURL } from './conn';
import { Setting, ArrowDown, SwitchButton } from '@element-plus/icons-vue'

export default {
    name: 'AppNavbar',
    components: {
        Setting,
        ArrowDown,
        SwitchButton
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
            userAvatar: '', // 可以在这里设置默认头像URL
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
            this.$router.push('/');
        },
        gotoBMManager() {
            this.$router.push('/bm_manager'); 
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
.navbar-container {
    flex-direction: column;
    padding: 10px;
}

.top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.title {
    margin: 0;
}

.user-controls {
    display: flex;
    align-items: center;
}

.bottom-row {
    display: flex;
    align-items: center;
}

.el-tabs {
    margin-right: 20px;
}

:deep(.el-tabs__header) {
    margin-bottom: 0;
}

.title-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.nav-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
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

/* 添加移动设备适配样式 */
@media screen and (max-width: 768px) {
    .title {
        font-size: 16px;
        margin: 0;
    }

    .nav-avatar {
        width: 28px;
        height: 28px;
    }

    .username {
        display: none; /* 在移动端隐藏用户名 */
    }

    .user-dropdown-trigger {
        padding: 2px;
    }

    :deep(.el-tabs__item) {
        padding: 0 10px !important;
        font-size: 14px;
    }
}
</style>
