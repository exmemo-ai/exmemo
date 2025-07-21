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

        <div class="settings-section">
            <div class="settings-section-header">
                {{ $t('settings.embeddingSettings') }}
            </div>
            <div class="settings-section-content">
                <el-form-item :label="$t('settings.serviceType')">
                    <el-radio-group v-model="embedding_type">
                        <el-radio value="ollama">Ollama</el-radio>
                        <el-radio value="openai">OpenAI</el-radio>
                    </el-radio-group>
                </el-form-item>
                
                <el-form-item :label="$t('apiUrl')">
                    <el-input v-model="embedding_url" placeholder="http://localhost:11434" style="width: 300px;"></el-input>
                </el-form-item>
                
                <el-form-item :label="$t('model')">
                    <el-input v-model="embedding_model" placeholder="nomic-embed-text" style="width: 300px;"></el-input>
                </el-form-item>
                
                <el-form-item :label="$t('apiKey')" v-if="embedding_type === 'openai'">
                    <el-input v-model="embedding_apikey" style="width: 300px;"></el-input>
                </el-form-item>
                
                <el-form-item :label="$t('settings.embeddingScope')">
                    <el-radio-group v-model="embedding_scope">
                        <el-radio value="none">{{ $t('settings.noEmbedding') }}</el-radio>
                        <el-radio value="all">{{ $t('settings.allContent') }}</el-radio>
                        <el-radio value="meta">{{ $t('settings.titleAndDescription') }}</el-radio>
                    </el-radio-group>
                </el-form-item>
            </div>
        </div>
    </el-form>
</template>

<script>
import { useI18n } from 'vue-i18n';
import { watch } from 'vue';
import SettingService from '@/components/settings/settingService';

const DEFAULT_EMBEDDING_TYPE = 'openai';
const DEFAULT_EMBEDDING_URL = 'https://api.openai.com/v1'; //'http://localhost:11434';
const DEFAULT_EMBEDDING_MODEL = 'text-embedding-ada-002';
const DEFAULT_EMBEDDING_SCOPE = 'none';

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
            embedding_type: DEFAULT_EMBEDDING_TYPE,
            embedding_url: DEFAULT_EMBEDDING_URL,
            embedding_model: DEFAULT_EMBEDDING_MODEL,
            embedding_apikey: '',
            embedding_scope: DEFAULT_EMBEDDING_SCOPE
        }
    },
    async created() {
        const settings = await SettingService.getInstance().loadSetting();
        if (settings.setting) {
            this.llm_chat_prompt = settings.setting.llm_chat_prompt;
            this.llm_chat_show_count = settings.setting.llm_chat_show_count;
            this.llm_chat_memory_count = settings.setting.llm_chat_memory_count;
            this.llm_chat_max_context_count = settings.setting.llm_chat_max_context_count || '1024';
            
            const chat_info = settings.setting.llm_chat_model || {};
            this.llm_chat_type = chat_info.type || 'default';
            this.llm_chat_apikey = chat_info.apikey || '';
            this.llm_chat_url = chat_info.url || '';
            this.llm_chat_model = chat_info.model || '';
            
            const tool_info = settings.setting.llm_tool_model || {};
            this.llm_tool_type = tool_info.type || 'default';
            this.llm_tool_apikey = tool_info.apikey || '';
            this.llm_tool_url = tool_info.url || '';
            this.llm_tool_model = tool_info.model || '';

            const embedding_info = settings.setting.embedding_model || {};
            this.embedding_type = 'type' in embedding_info ? embedding_info.type : DEFAULT_EMBEDDING_TYPE;
            this.embedding_url = 'url' in embedding_info ? embedding_info.url : DEFAULT_EMBEDDING_URL;
            this.embedding_model = 'model' in embedding_info ? embedding_info.model : DEFAULT_EMBEDDING_MODEL;
            this.embedding_apikey = 'apikey' in embedding_info ? embedding_info.apikey : '';
            this.embedding_scope = 'embedding_scope' in settings.setting ? settings.setting.embedding_scope : DEFAULT_EMBEDDING_SCOPE;
        }

        const basicSettings = ['llm_chat_prompt', 'llm_chat_show_count', 
                             'llm_chat_memory_count', 'llm_chat_max_context_count'];
        basicSettings.forEach(key => {
            watch(() => this[key], (newVal) => {
                SettingService.getInstance().setSetting(key, newVal);
            });
        });

        const chatModelKeys = ['llm_chat_type', 'llm_chat_apikey', 'llm_chat_url', 'llm_chat_model'];
        chatModelKeys.forEach(key => {
            watch(() => this[key], () => {
                const modelInfo = JSON.stringify({
                    type: this.llm_chat_type,
                    apikey: this.llm_chat_apikey,
                    url: this.llm_chat_url,
                    model: this.llm_chat_model
                });
                SettingService.getInstance().setSetting('llm_chat_model', modelInfo);
            });
        });

        const toolModelKeys = ['llm_tool_type', 'llm_tool_apikey', 'llm_tool_url', 'llm_tool_model'];
        toolModelKeys.forEach(key => {
            watch(() => this[key], () => {
                const modelInfo = JSON.stringify({
                    type: this.llm_tool_type,
                    apikey: this.llm_tool_apikey,
                    url: this.llm_tool_url,
                    model: this.llm_tool_model
                });
                SettingService.getInstance().setSetting('llm_tool_model', modelInfo);
            });
        });

        const embeddingModelKeys = ['embedding_type', 'embedding_url', 'embedding_model', 'embedding_apikey'];
        embeddingModelKeys.forEach(key => {
            watch(() => this[key], () => {
                const modelInfo = JSON.stringify({
                    type: this.embedding_type,
                    url: this.embedding_url,
                    model: this.embedding_model,
                    apikey: this.embedding_apikey
                });
                SettingService.getInstance().setSetting('embedding_model', modelInfo);
            });
        });

        watch(() => this.embedding_scope, (newVal) => {
            SettingService.getInstance().setSetting('embedding_scope', newVal);
        });
    }
}
</script>

<style scoped>
</style>