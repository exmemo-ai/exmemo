<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">

        <el-container>
            <h3 style="text-align: left;">{{ $t('userSetting') }}</h3>
            <div style="display: flex; align-items: center; justify-content: flex-end; margin-left: auto; max-width: 100%;">
                <el-label type="text" v-if="isLogin" style="margin-right: 5px;">{{ login_user }}</el-label>
                <el-button type="text" @click="logoutFunc" v-if="isLogin">{{ $t('logout') }}</el-button>
                <el-button type="text" @click="loginFunc" v-else>{{ $t('login') }}</el-button>
            </div>
        </el-container>

        <el-container>
            <h4 style="text-align: left;">{{ $t('voiceSynthesis') }}</h4>
        </el-container>
        <el-main class="custom-padding">
            <div style="display: flex; flex-direction: column;">
                <el-form-item :label="$t('engine')">
                    <el-select v-model="engine_value" :placeholder="$t('pleaseSelect')" @change="engineChangeFunc">
                        <el-option v-for="item in engine_options" :key="item.value" :label="item.label" :value="item.value">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('voice')">
                    <el-select v-model="voice_value" :placeholder="$t('pleaseSelect')">
                        <el-option v-for="item in voice_options" :key="item.value" :label="item.label" :value="item.value">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('language')">
                    <el-select v-model="language_value" :placeholder="$t('pleaseSelect')">
                        <el-option v-for="item in language_options" :key="item.value" :label="item.label"
                            :value="item.value">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('speed')">
                    <el-select v-model="speed_value" :placeholder="$t('pleaseSelect')">
                        <el-option v-for="item in speed_options" :key="item.value" :label="item.label" :value="item.value">
                        </el-option>
                    </el-select>
                </el-form-item>
            </div>
        </el-main>

        <el-container>
            <h4 style="text-align: left;">{{ $t('dialogModel') }}</h4>
        </el-container>
        <el-main class="custom-padding">
            <div style="display: flex; flex-direction: column;">
                <el-form-item :label="$t('model')">
                    <el-select v-model="llm_chat_value" :placeholder="$t('pleaseSelect')">
                        <el-option v-for="item in llm_options" :key="item.value" :label="item.label" :value="item.value">
                        </el-option>
                    </el-select>
                </el-form-item>
            </div>
        </el-main>

        <el-container>
            <h4 style="text-align: left;">{{ $t('privileges') }}</h4>
        </el-container>
        <el-main class="custom-padding">
            <pre class="file-content">{{ info_privilege }}</pre>
        </el-main>

        <el-footer>
            <el-button @click='saveFunc' type="primary">{{ $t('save') }}</el-button>
            <el-button @click='resetFunc' type="primary">{{ $t('reset') }}</el-button>
            <el-button @click='resetPassword' type="primary">{{ $t('set_password') }}</el-button>
        </el-footer>

    </div>
</template>

<script>
import { checkLogin, getURL, realLoginFunc, realLogoutFunc, parseBackendError } from './conn'
import axios from 'axios';
import { useI18n } from 'vue-i18n';

export default {
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
            llm_chat_value: 'default',
            llm_options: [{ label: this.$t('default'), value: 'default' }],
            voice_settings: 'default',
            voice_value: 'default',
            voice_options: [{ label: this.$t('default'), value: 'default' }],
            engine_value: 'xunfei',
            engine_options: [{ label: this.$t('xunfei'), value: 'xunfei' }, { label: this.$t('google'), value: 'google' }, { label: this.$t('openai'), value: 'openai' }, { label: this.$t('custom'), value: 'mytts' }],
            speed_value: '1.25',
            speed_options: [{ label: this.$t('slow'), value: '0.6' }, { label: this.$t('slower'), value: '0.8' }, { label: this.$t('normal'), value: '1.0' }, { label: this.$t('faster'), value: '1.25' }, { label: this.$t('fast'), value: '1.5' }],
            language_value: 'mix',
            language_options: [{ label: this.$t('chinese'), value: 'zh' }, { label: this.$t('english'), value: 'en' }, { label: this.$t('mixed'), value: 'mix' }],
        };
    },
    methods: {
        engineChangeFunc(value) {
            console.log(value);
            this.loadVoice();
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
        loginFunc() {
            realLoginFunc(this);
        },
        logoutFunc() {
            realLogoutFunc(this);
        },
        loadVoice() {
            const formData = new FormData();
            formData.append('tts_engine', this.engine_value);
            formData.append('rtype', 'get_voice');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log(res);
                console.log(res.data);
                if (res.data.status == "success") {
                    this.voice_options = []
                    this.voice_settings = res.data.info.voice_settings
                    res.data.info.voice_list.forEach((item) => {
                        this.voice_options.push({ label: item['label'], value: item['value'] });
                    });
                    this.resetVoice();
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
        resetPassword() {
            this.$router.push("/set_password?user_id=" + localStorage.getItem('username'));
        },
        resetVoice() {
            let voice_exist = false;
            this.voice_options.forEach((item) => {
                if (item.value === this.voice_settings) {
                    this.voice_value = this.voice_settings;
                    voice_exist = true;
                }
            });
            if (!voice_exist) {
                this.voice_value = this.voice_options[0].value;
            }
        },
        loadSetting() {
            const formData = new FormData();
            formData.append('rtype', 'get_setting');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log(res);
                console.log(res.data);
                if (res.data.status == "success") {
                    this.engine_options = []
                    res.data.info.engine_list.forEach((item) => {
                        this.engine_options.push({ label: item['label'], value: item['value'] });
                    });
                    this.llm_options = []
                    res.data.info.llm_list.forEach((item) => {
                        this.llm_options.push({ label: item['label'], value: item['value'] });
                    });
                    console.log(res.data.data);
                    this.engine_value = res.data.info.setting.tts_engine;
                    this.voice_setting = res.data.info.setting.tts_voice;
                    this.language_value = res.data.info.setting.tts_language;
                    this.speed_value = res.data.info.setting.tts_speed;
                    this.llm_chat_value = res.data.info.setting.llm_chat_model;
                    this.info_privilege = res.data.info.privilege;
                    this.loadVoice();
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
            const formData = new FormData();
            formData.append('rtype', 'save');
            formData.append('tts_engine', this.engine_value);
            formData.append('tts_voice', this.voice_value);
            formData.append('tts_language', this.language_value);
            formData.append('tts_speed', this.speed_value);
            formData.append('llm_chat_model', this.llm_chat_value);
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
        checkLogin(this);
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