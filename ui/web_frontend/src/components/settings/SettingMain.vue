<template>
    <div class="full-container">
        <el-container style="flex: 0; width: 100%;">
            <app-navbar :title="$t('userSetting')" :info="'Setting'" />
        </el-container>
        <el-container style="flex: 1; width: 100%; overflow: hidden;">
            <el-aside class="aside-menu" :class="{ 'mobile-aside': isMobile }">
                <el-menu :default-active="currentSection" @select="handleSelect">
                    <el-menu-item index="voice">
                        <span>{{ $t('voiceSynthesis') }}</span>
                    </el-menu-item>
                    <el-menu-item index="dialog">
                        <span>{{ $t('dialogModel') }}</span>
                    </el-menu-item>
                    <el-menu-item index="extract">
                        <span>{{ $t('settings.extract') }}</span>
                    </el-menu-item>
                    <el-menu-item index="bookmark">
                        <span>{{ $t('settings.bookmark') }}</span>
                    </el-menu-item>
                    <el-menu-item index="privilege">
                        <span>{{ $t('privileges') }}</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-container style="flex: 1; width: 100%; flex-direction: column;">
                <div class="settings-content">
                    <div v-show="currentSection === 'voice'">
                        <setting-t-t-s ref="ttsSettings" />
                    </div>

                    <div v-show="currentSection === 'dialog'">
                        <setting-l-l-m ref="llmSettings" />
                    </div>

                    <div v-show="currentSection === 'bookmark'">
                        <setting-bookmark ref="bookmarkSettings" />
                    </div>

                    <div v-show="currentSection === 'extract'">
                        <setting-extract ref="extractSettings" />
                    </div>

                    <div v-show="currentSection === 'privilege'">
                        <el-form>
                            <div class="settings-section">
                                <div class="settings-section-header">
                                    {{ $t('privileges') }}
                                </div>
                                <div class="settings-section-content">
                                    <el-form-item class="info-description">
                                        {{ info_privilege }}
                                    </el-form-item>
                                </div>
                            </div>
                        </el-form>
                        <el-form>
                            <div class="settings-section">
                                <div class="settings-section-header">
                                    {{ $t('usage') }}
                                </div>
                                <div class="settings-section-content">
                                    <el-form-item class="info-description">
                                        {{ info_usage }}
                                    </el-form-item>
                                </div>
                            </div>
                        </el-form>
                    </div>
                </div>
            </el-container>
        </el-container>

        <el-footer class="settings-footer">
            <el-button @click='saveFunc' type="primary">{{ $t('save') }}</el-button>
            <el-button @click='resetFunc'>{{ $t('reset') }}</el-button>
            <el-button @click='resetPassword'>{{ $t('set_password') }}</el-button>
        </el-footer>
    </div>
</template>

<script>
import { getURL, parseBackendError } from '@/components/support/conn'
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import AppNavbar from '@/components/support/AppNavbar.vue'
import SettingTTS from './SettingTTS.vue'
import SettingLLM from './SettingLLM.vue'
import SettingBookmark from './SettingBookmark.vue'
import SettingExtract from './SettingExtract.vue'

export default {
    components: {
        AppNavbar,
        SettingTTS,
        SettingLLM,
        SettingBookmark,
        SettingExtract
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
            info_usage: '',
            currentSection: 'voice'
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
                    this.info_privilege = res.data.privilege;
                    this.info_usage = res.data.usage;
                    this.$refs.ttsSettings.updateSettings({
                        ...res.data.setting,
                        engine_list: res.data.engine_list
                    });
                    this.$refs.llmSettings.updateSettings(res.data);
                    this.$refs.bookmarkSettings.updateSettings(res.data);
                    this.$refs.extractSettings.updateSettings(res.data.setting);
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
            const bookmarkSettings = this.$refs.bookmarkSettings.getSettings();
            const extractSettings = this.$refs.extractSettings.getSettings();
            const formData = new FormData();
            formData.append('rtype', 'save');
            formData.append('tts_engine', ttsSettings.tts_engine);
            formData.append('tts_voice', ttsSettings.tts_voice);
            formData.append('tts_language', ttsSettings.tts_language);
            formData.append('tts_speed', ttsSettings.tts_speed);
            formData.append('llm_chat_model', llmSettings.llm_chat_model);
            formData.append('llm_tool_model', llmSettings.llm_tool_model);
            formData.append('llm_chat_prompt', llmSettings.llm_chat_prompt);
            formData.append('llm_chat_show_count', llmSettings.llm_chat_show_count);
            formData.append('llm_chat_max_context_count', llmSettings.llm_chat_max_context_count);
            formData.append('llm_chat_memory_count', llmSettings.llm_chat_memory_count);
            formData.append('bookmark_download_web', bookmarkSettings.bookmark_download_web);
            Object.entries(extractSettings).forEach(([key, value]) => {
                formData.append(key, value);
            });
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
        handleSelect(key) {
            this.currentSection = key;
        }
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
.settings-content {
    flex: 1;
    padding: 0px;
    overflow: auto;
}

.settings-footer {
    flex-shrink: 0;
    border-top: 1px solid #e1e4e8;
    padding: 16px;
    text-align: right;
    background: white;
}

.aside-menu {
    width: 200px !important;
}

.aside-menu :deep(.el-menu) {
    border-right: none;
}

.aside-menu :deep(.el-menu-item) {
    padding: 0 15px !important;
}

@media (max-width: 768px) {
    .el-input, .el-select {
        width: 100%;
        min-width: 260px;
    }

    .aside-menu {
        width: 100% !important;
    }
}

.info-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 10px;
    color: #2c3e50;
}

.info-description {
    margin-bottom: 5px;
    white-space: pre-wrap;
}

</style>