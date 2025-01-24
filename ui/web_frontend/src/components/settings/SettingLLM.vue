<template>
    <el-form>
        <div class="settings-section">
            <div class="settings-section-header">
                {{ $t('chatSettings') }}
            </div>
            <div class="settings-section-content">
                <el-form-item :label="$t('prompt')">
                    <el-input v-model="llm_chat_prompt" placeholder="提示词" style="width: 300px;"></el-input>
                </el-form-item>
                <el-form-item :label="$t('showCount')">
                    <el-select v-model="llm_chat_show_count" style="width: 300px;">
                        <el-option label="20" value="20"></el-option>
                        <el-option label="50" value="50"></el-option>
                        <el-option label="100" value="100"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('memoryCount')">
                    <el-select v-model="llm_chat_memory_count" style="width: 300px;">
                        <el-option label="0" value="0"></el-option>
                        <el-option label="5" value="5"></el-option>
                        <el-option label="10" value="10"></el-option>
                        <el-option label="20" value="20"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('maxTokens')">
                    <el-select v-model="llm_chat_max_context_count" style="width: 300px;">
                        <el-option label="512" value="512"></el-option>
                        <el-option label="1024" value="1024"></el-option>
                        <el-option :label="$t('unlimited')" value="-1"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item :label="$t('modelType')">
                    <el-radio-group v-model="llm_chat_type">
                        <el-radio value="default">{{ $t('defaultModel') }}</el-radio>
                        <el-radio value="custom">{{ $t('customModel') }}</el-radio>
                    </el-radio-group>
                </el-form-item>

                <template v-if="llm_chat_type !== 'default'">
                    <el-form-item :label="$t('apiKey')">
                        <el-input v-model="llm_chat_apikey" style="width: 300px;"></el-input>
                    </el-form-item>
                    <el-form-item :label="$t('apiUrl')">
                        <el-input v-model="llm_chat_url" style="width: 300px;"></el-input>
                    </el-form-item>
                    <el-form-item :label="$t('model')">
                        <el-input v-model="llm_chat_model" style="width: 300px;"></el-input>
                    </el-form-item>
                </template>
            </div>
        </div>

        <div class="settings-section">
            <div class="settings-section-header">
                {{ $t('toolSettings') }}
            </div>
            <div class="settings-section-content">
                <el-form-item :label="$t('modelType')">
                    <el-radio-group v-model="llm_tool_type">
                        <el-radio value="default">{{ $t('defaultModel') }}</el-radio>
                        <el-radio value="custom">{{ $t('customModel') }}</el-radio>
                    </el-radio-group>
                </el-form-item>

                <template v-if="llm_tool_type !== 'default'">
                    <el-form-item :label="$t('apiKey')">
                        <el-input v-model="llm_tool_apikey" style="width: 300px;"></el-input>
                    </el-form-item>
                    <el-form-item :label="$t('apiUrl')">
                        <el-input v-model="llm_tool_url" style="width: 300px;"></el-input>
                    </el-form-item>
                    <el-form-item :label="$t('model')">
                        <el-input v-model="llm_tool_model" style="width: 300px;"></el-input>
                    </el-form-item>
                </template>
            </div>
        </div>
    </el-form>
</template>

<script>
import { useI18n } from 'vue-i18n';

export default {
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        const { t } = useI18n();
        return {
            llm_chat_prompt: t('defaultChatPrompt'),
            llm_chat_show_count: 50,
            llm_chat_memory_count: 5,
            llm_chat_max_context_count: '1024',
            llm_chat_type: 'default',
            llm_chat_apikey: '',
            llm_chat_url: '',
            llm_chat_model: '',
            llm_tool_type: 'default',
            llm_tool_apikey: '',
            llm_tool_url: '',
            llm_tool_model: '',
        }
    },
    methods: {
        updateSettings(settings) {
            this.llm_chat_prompt = settings.setting.llm_chat_prompt;
            this.llm_chat_show_count = settings.setting.llm_chat_show_count;
            this.llm_chat_memory_count = settings.setting.llm_chat_memory_count;
            this.llm_chat_max_context_count = settings.setting.llm_chat_max_context_count || '1024';
            let chat_info = settings.setting.llm_chat_model;
            this.llm_chat_type = chat_info.type || 'default';
            this.llm_chat_apikey = chat_info.apikey || '';
            this.llm_chat_url = chat_info.url || '';
            this.llm_chat_model = chat_info.model || '';
            let tool_info = settings.setting.llm_tool_model;
            this.llm_tool_type = tool_info.type || 'default';
            this.llm_tool_apikey = tool_info.apikey || '';
            this.llm_tool_url = tool_info.url || '';
            this.llm_tool_model = tool_info.model || '';
        },
        getSettings() {
            return {
                llm_chat_model: JSON.stringify({
                    type: this.llm_chat_type,
                    apikey: this.llm_chat_apikey,
                    url: this.llm_chat_url,
                    model: this.llm_chat_model
                }),
                llm_tool_model: JSON.stringify({
                    type: this.llm_tool_type,
                    apikey: this.llm_tool_apikey,
                    url: this.llm_tool_url,
                    model: this.llm_tool_model
                }),
                llm_chat_prompt: this.llm_chat_prompt,
                llm_chat_show_count: this.llm_chat_show_count,
                llm_chat_memory_count: this.llm_chat_memory_count,
                llm_chat_max_context_count: this.llm_chat_max_context_count,
            }
        }
    }
}
</script>

<style scoped>
</style>