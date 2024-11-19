<template>
    <div class="section-content">
        <el-form>
            <el-form-item :label="$t('engine')">
                <el-select v-model="engine_value" style="width: 300px;" @change="engineChangeFunc">
                    <el-option v-for="item in engineOptions" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('voice')">
                <el-select v-model="voice_value" :placeholder="$t('pleaseSelect')" style="width: 200px;">
                    <el-option v-for="item in voiceOptions" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('language')">
                <el-select v-model="language_value" :placeholder="$t('pleaseSelect')" style="width: 200px;">
                    <el-option v-for="item in language_options" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('speed')">
                <el-select v-model="speed_value" :placeholder="$t('pleaseSelect')" style="width: 200px;">
                    <el-option v-for="item in speedOptions" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>
    </div>
</template>

<script>
import { getURL, parseBackendError } from '@/components/support/conn';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

export default {
    name: 'SettingTTS',
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        return {
            voice_settings: 'default',
            voice_value: 'default',
            engine_value: 'xunfei',
            speed_value: '1.25',
            language_value: 'mix',
            engineOptions: [],
            voiceOptions: [{ label: this.$t('default'), value: 'default' }],
            speedOptions: [
                { label: this.$t('slow'), value: '0.6' },
                { label: this.$t('slower'), value: '0.8' },
                { label: this.$t('normal'), value: '1.0' },
                { label: this.$t('faster'), value: '1.25' },
                { label: this.$t('fast'), value: '1.5' }
            ],
            language_options: [
                { label: this.$t('chinese'), value: 'zh' },
                { label: this.$t('english'), value: 'en' },
                { label: this.$t('mixed'), value: 'mix' }
            ],
        }
    },
    methods: {
        engineChangeFunc(value) {
            console.log(value);
            this.loadVoice();
        },
        loadVoice() {
            const formData = new FormData();
            formData.append('tts_engine', this.engine_value);
            formData.append('rtype', 'get_voice');
            axios.post(getURL() + 'api/setting/', formData).then((res) => {
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
        updateSettings(settings) {
            this.engine_value = settings.tts_engine;
            this.voice_settings = settings.tts_voice;
            this.language_value = settings.tts_language;
            this.speed_value = settings.tts_speed;
            this.engineOptions = settings.engine_list.map(item => ({
                label: item.label,
                value: item.value
            }));
            this.loadVoice();
        },
        getSettings() {
            return {
                tts_engine: this.engine_value,
                tts_voice: this.voice_value,
                tts_language: this.language_value,
                tts_speed: this.speed_value
            }
        }
    }
}
</script>