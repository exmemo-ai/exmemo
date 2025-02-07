<template>
    <el-form>
        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('voiceSynthesis') }}
          </div>
          <div class="settings-section-content">
            <el-form-item :label="$t('engine')">
                <el-select v-model="engine_value" style="width: 300px;" @change="onEngineChange">
                    <el-option v-for="item in engineOptions" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('language')">
                <el-select v-model="language_value" :placeholder="$t('pleaseSelect')" style="width: 200px;" @change="onLanguageChange">
                    <el-option v-for="item in language_options" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('voice')">
                <el-select v-model="voice_value" :placeholder="$t('pleaseSelect')" style="width: 200px;" @change="onVoiceChange">
                    <el-option v-for="item in voiceOptions" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('speed')">
                <el-slider
                    v-model="speed_value"
                    :min="0.5"
                    :max="2"
                    :step="0.1"
                    style="width: 200px;"
                    :format-tooltip="value => value + 'x'"
                    @change="onSpeedChange"
                />
            </el-form-item>
          </div>
        </div>
    </el-form>
</template>

<script>
import { getURL, parseBackendError } from '@/components/support/conn';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import SettingService from '@/components/settings/settingService';

export default {
    name: 'SettingTTS',
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        return {
            isSettingsLoaded: false,
            engineOptions: [
                { label: this.$t('settings.browserTTS'), value: 'browser' },
            ],
            voiceOptions: [{ label: this.$t('default'), value: 'default' }],
            language_options: [
                { label: this.$t('chinese'), value: 'zh' },
                { label: this.$t('english'), value: 'en' },
                { label: this.$t('mixed'), value: 'mix' }
            ],
            engine_value: 'browser',
            voice_value: 'default',
            speed_value: 1.25,
            language_value: 'mix',
            browser_voices_map: new Map(),
        }
    },
    async created() {
        await this.reload();
    },
    methods: {
        onEngineChange(value) {
            this.engine_value = value;
            SettingService.getInstance().setSetting("tts_engine", value);
            if (value === 'browser') {
                this.loadBrowserVoices();
            } else {
                this.loadVoice();
            }
        },
        onVoiceChange(value) {
            this.voice_value = value;
            SettingService.getInstance().setSetting("tts_voice", this.voice_value);
        },
        onSpeedChange(value) {
            this.speed_value = value;
            SettingService.getInstance().setSetting("tts_speed", value);
        },
        onLanguageChange(value) {
            this.language_value = value;
            SettingService.getInstance().setSetting("tts_language", value);
            if (this.engine_value === 'browser') {
                this.updateBrowserVoiceOptions(value);
            }
        },
        engineChangeFunc(value) {
            if (value === 'browser') {
                this.loadBrowserVoices();
            } else {
                this.loadVoice();
            }
        },
        loadBrowserVoices() {
            const voices = window.speechSynthesis.getVoices();
            this.browser_voices_map.clear();
            
            voices.forEach(voice => {
                const langPrefix = voice.lang.substring(0, 2);
                if (!this.browser_voices_map.has(langPrefix)) {
                    this.browser_voices_map.set(langPrefix, []);
                }
                this.browser_voices_map.get(langPrefix).push(voice);
            });
            
            if (voices.length === 0) {
                window.speechSynthesis.addEventListener('voiceschanged', () => {
                    this.loadBrowserVoices();
                });
            } else {
                this.updateBrowserVoiceOptions(this.language_value);
            }
        },
        updateBrowserVoiceOptions(lang) {
            let voices = [];
            if (lang === 'mix') { // 混合模式显示所有语音
                voices = Array.from(this.browser_voices_map.values()).flat();
            } else {
                voices = this.browser_voices_map.get(lang) || [];
            }
            
            this.voiceOptions = voices.map(voice => ({
                label: `${voice.name} (${voice.lang})`,
                value: voice.name
            }));
            
            if (this.voiceOptions.length > 0) {
                this.voice_value = this.voiceOptions[0].value;
                SettingService.getInstance().setSetting("tts_voice", this.voice_value);
            }
        },
        loadVoice() {
            console.log('loadVoice');
            const formData = new FormData();
            formData.append('tts_engine', this.engine_value);
            formData.append('rtype', 'get_voice');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
                console.log('ret', res.data);
                if (res.data.status == "success") {
                    this.voiceOptions = []
                    res.data.voice_list.forEach((item) => {
                        this.voiceOptions.push({ label: item['label'], value: item['value'] });
                    });
                    this.resetVoice();
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
        resetVoice() {
            let voice_exist = false;
            this.voiceOptions.forEach((item) => {
                if (item.value === this.voice_value) {
                    voice_exist = true;
                }
            });
            if (!voice_exist) {
                this.voice_value = this.voiceOptions[0].value;
                SettingService.getInstance().setSetting("tts_voice", this.voice_value);
            }
        },
        async reload() {
            const settings = await SettingService.getInstance().loadSetting();
            this.engineOptions = settings.engine_list.map(item => ({
                label: item.label,
                value: item.value
            }));
            if ('speechSynthesis' in window) {
                this.engineOptions.unshift({ label: this.$t('settings.browserTTS'), value: 'browser' });
                this.engine_value = settings?.setting?.tts_engine || 'browser';
            } else {
                this.engine_value = settings?.setting?.tts_engine || 'microsoft';
            }            
            if (this.engine_value === 'browser') {
                this.loadBrowserVoices();
            } else {
                this.loadVoice();
            }

            this.voice_value = settings?.setting?.tts_voice || 'default';
            SettingService.getInstance().setSetting("tts_voice", this.voice_value);
            this.speed_value = settings?.setting?.tts_speed || 1.25;
            if (typeof this.speed_value === 'string') {
                this.speed_value = parseFloat(this.speed_value);
            }
            this.language_value = settings?.setting?.tts_language || 'mix';
            this.isSettingsLoaded = true;
        },
    }
}
</script>