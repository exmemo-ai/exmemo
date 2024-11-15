<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }" class="setting-page">
        <div>
            <app-navbar :title="$t('userSetting')" :info="'Setting'" />
        </div>
        <div class="settings-container">
            <div class="settings-nav">
                <div class="nav-item" 
                     v-for="item in navItems" 
                     :key="item.key"
                     :class="{ active: currentSection === item.key }"
                     @click="currentSection = item.key">
                    {{ $t(item.label) }}
                </div>
            </div>

            <div class="settings-content">
                <div v-show="currentSection === 'voice'" class="section-content">
                    <setting-t-t-s ref="ttsSettings" />
                </div>

                <div v-show="currentSection === 'dialog'" class="section-content">
                    <setting-l-l-m ref="llmSettings" />
                </div>

                <div v-show="currentSection === 'privilege'" class="section-content">
                    <pre class="file-content">{{ info_privilege }}</pre>
                </div>
            </div>
        </div>

        <el-footer class="settings-footer">
            <el-button @click='saveFunc' type="primary">{{ $t('save') }}</el-button>
            <el-button @click='resetFunc' type="primary">{{ $t('reset') }}</el-button>
            <el-button @click='resetPassword' type="primary">{{ $t('set_password') }}</el-button>
        </el-footer>
    </div>
</template>

<script>
import { getURL, parseBackendError } from '../conn'
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import AppNavbar from '@/components/AppNavbar.vue'
import SettingTTS from './SettingTTS.vue'
import SettingLLM from './SettingLLM.vue'

export default {
    components: {
        AppNavbar,
        SettingTTS,
        SettingLLM
    },
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        return {
            isMobile: false,
            isLogin: true,
            login_user: '',
            info_privilege: '',
            currentSection: 'voice',
            navItems: [
                { key: 'voice', label: 'voiceSynthesis' },
                { key: 'dialog', label: 'dialogModel' },
                { key: 'privilege', label: 'privileges' }
            ]
        };
    },
    methods: {
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
        resetPassword() {
            this.$router.push("/set_password?user_id=" + localStorage.getItem('username'));
        },
        loadSetting() {
            const formData = new FormData();
            formData.append('rtype', 'get_setting');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log(res);
                console.log(res.data);
                if (res.data.status == "success") {
                    this.info_privilege = res.data.info.privilege;
                    this.$refs.ttsSettings.updateSettings({
                        ...res.data.info.setting,
                        engine_list: res.data.info.engine_list
                    });
                    this.$refs.llmSettings.updateSettings(res.data.info);
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
        resetFunc() {
            this.$confirm(this.$t('confirmResetSettings'), this.$t('hint'), {
                confirmButtonText: this.$t('confirm'),
                cancelButtonText: this.$t('cancel'),
                type: 'warning'
            }).then(() => {
                this.realReset();
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: this.$t('operationCancelled')
                });
            });
        },
        realReset() {
            const formData = new FormData();
            formData.append('rtype', 'reset');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log(res);
                console.log(res.data);
                if (res.data.status == "success") {
                    this.$message({
                        message: res.data.info,
                        type: 'success'
                    });
                    this.loadSetting();
                } else {
                    this.$message({
                        message: res.data.info,
                        type: 'warning'
                    });
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
        saveFunc() {
            console.log(this.engine_value, this.language_value, this.speed_value);
            const ttsSettings = this.$refs.ttsSettings.getSettings();
            const llmSettings = this.$refs.llmSettings.getSettings();
            const formData = new FormData();
            formData.append('rtype', 'save');
            formData.append('tts_engine', ttsSettings.tts_engine);
            formData.append('tts_voice', ttsSettings.tts_voice);
            formData.append('tts_language', ttsSettings.tts_language);
            formData.append('tts_speed', ttsSettings.tts_speed);
            formData.append('llm_chat_model', llmSettings.llm_chat_model);
            formData.append('llm_chat_prompt', llmSettings.llm_chat_prompt);
            formData.append('llm_chat_show_count', llmSettings.llm_chat_show_count);
            formData.append('llm_chat_memory_count', llmSettings.llm_chat_memory_count);
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log(res);
                console.log(res.data);
                if (res.data.status == "success") {
                    this.$message({
                        message: res.data.info,
                        type: 'success'
                    });
                } else {
                    this.$message({
                        message: res.data.info,
                        type: 'warning'
                    });
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
    },
    mounted() {
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
        this.loadSetting();
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    },
}
</script>

<style scoped>
.setting-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.nav-container {
    flex-shrink: 0;
}

.nav-item {
    padding: 8px 16px;
    margin: 4px 0;
    cursor: pointer;
    border-radius: 6px;
    transition: background-color 0.3s;
}

.nav-item:hover {
    background-color: #f6f8fa;
}

.nav-item.active {
    background-color: #f1f8ff;
    color: #0366d6;
}

.section-content {
    max-width: 800px;
}

@media (max-width: 768px) {
    .settings-container {
        flex-direction: column;
    }

    .settings-nav {
        width: 100%;
        border-right: none;
        border-bottom: 1px solid #e1e4e8;
        padding-bottom: 16px;
        margin-bottom: 16px;
        flex-shrink: 0;
    }
}
</style>