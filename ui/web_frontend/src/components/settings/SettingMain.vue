<template>
    <div class="full-container">
        <el-container ref="navbar" style="flex: 0; width: 100%;">
            <app-navbar :title="$t('userSetting')" :info="'Setting'" />
        </el-container>
        <el-container class="main_container">
          <el-container style="flex: 1; width: 100%; flex-direction: row;">
            <el-aside class="aside-menu" :class="{ 'collapse-aside': isCollapse, 'mobile-aside': isMobile }">
                <div class="toggle-button-collapse" @click="toggleCollapse">
                    <el-icon>
                        <Fold v-if="!isCollapse"/>
                        <Expand v-else/>
                    </el-icon>
                </div>
                <el-menu :default-active="currentSection" @select="handleSelect" :collapse="isCollapse">
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
                    <el-menu-item index="prompt">
                        <span>{{ $t('prompt') }}</span>
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
                    
                    <div v-show="currentSection === 'prompt'">
                        <setting-prompt ref="promptSettings" />
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
        </el-container>
        
        <el-footer ref="footer" class="settings-footer">
            <el-button @click='saveFunc' type="primary">{{ $t('save') }}</el-button>
            <el-button @click='resetFunc'>{{ $t('reset') }}</el-button>
            <el-button @click='resetPassword'>{{ $t('set_password') }}</el-button>
        </el-footer>
    </div>
</template>

<script>
import { parseBackendError } from '@/components/support/conn'
import SettingService from '@/components/settings/settingService';
import { useI18n } from 'vue-i18n';
import AppNavbar from '@/components/support/AppNavbar.vue'
import SettingTTS from './SettingTTS.vue'
import SettingLLM from './SettingLLM.vue'
import SettingBookmark from './SettingBookmark.vue'
import SettingExtract from './SettingExtract.vue'
import SettingPrompt from './SettingPrompt.vue'
import { Fold, Expand } from '@element-plus/icons-vue'

export default {
    components: {
        AppNavbar,
        SettingTTS,
        SettingLLM,
        SettingBookmark,
        SettingExtract,
        SettingPrompt,
        Fold,
        Expand
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
            currentSection: 'voice',
            isCollapse: false,
            validSections: ['voice', 'dialog', 'extract', 'bookmark', 'prompt', 'privilege'] // 添加有效的设置项列表
        };
    },
    methods: {
        toggleCollapse() {
            this.isCollapse = !this.isCollapse;
        },        
        handleResize() {
            this.isMobile = window.innerWidth < 768;
            const visualHeight = window.innerHeight;
            const navbarHeight = this.$refs.navbar.$el.offsetHeight;
            const footerHeight = this.$refs.footer.$el.offsetHeight;
            document.documentElement.style.setProperty('--mainHeight', `${visualHeight - navbarHeight - footerHeight}px`);
        },
        resetPassword() {
            this.$router.push("/set_password?user_id=" + localStorage.getItem('username'));
        },
        async loadSetting() {
            try {
                const settingService = SettingService.getInstance();
                const data = await settingService.loadSetting();
                if (data.status === "success") {
                    this.info_privilege = data.privilege;
                    this.info_usage = data.usage;
                }
            } catch (err) {
                parseBackendError(err);
            }
        },

        async realReset() {
            try {
                const settingService = SettingService.getInstance();
                const data = await settingService.resetSetting();
                if (data.status === "success") {
                    this.$message({
                        message: data.info,
                        type: 'success'
                    });
                    this.loadSetting();
                } else {
                    this.$message({
                        message: data.info,
                        type: 'warning'
                    });
                }
            } catch (err) {
                parseBackendError(err);
            }
        },

        async saveFunc() {
            try {                
                const settingService = SettingService.getInstance();
                const data = await settingService.saveSetting();
                if (data.status === "success") {
                    this.$message({
                        message: data.info,
                        type: 'success'
                    });
                } else {
                    this.$message({
                        message: data.info,
                        type: 'warning'
                    });
                }
            } catch (err) {
                parseBackendError(err);
            }
        },
        initializeSection() {
            const section = this.$route.query.section;
            if (section && this.validSections.includes(section)) {
                this.currentSection = section;
            }
        },

        handleSelect(key) {
            this.currentSection = key;
            this.$router.push({
                query: { ...this.$route.query, section: key }
            });
        }
    },
    mounted() {
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
        this.loadSetting();
        this.initializeSection();
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
        SettingService.getInstance().resetPendingSetting();
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

@media (max-width: 768px) {
    .el-input, .el-select {
        width: 100%;
        min-width: 260px;
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