
<template>
    <el-form>
        <el-form-item :label="$t('chatModel')">
            <el-select v-model="llm_chat_value" style="width: 300px;">
                <el-option v-for="item in llm_chat_options" 
                          :key="item.value" 
                          :label="item.label"
                          :value="item.value">
                </el-option>
            </el-select>
        </el-form-item>
        <el-form-item :label="$t('toolModel')">
            <el-select v-model="llm_tool_value" style="width: 300px;">
                <el-option v-for="item in llm_tool_options" 
                          :key="item.value" 
                          :label="item.label"
                          :value="item.value">
                </el-option>
            </el-select>
        </el-form-item>
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
        return {
            llm_chat_value: 'default',
            llm_tool_value: 'default',
            llm_chat_options: [{ label: this.$t('default'), value: 'default' }],
            llm_tool_options: [{ label: this.$t('default'), value: 'default' }],
            llm_chat_prompt: '请简单回答问题',
            llm_chat_show_count: 50,
            llm_chat_memory_count: 5
        }
    },
    methods: {
        updateSettings(settings) {
            this.llm_chat_options = settings.llm_list.map(item => ({
                label: item.label,
                value: item.value
            }));
            this.llm_tool_options = settings.llm_list.map(item => ({
                label: item.label,
                value: item.value
            }));
            this.llm_chat_value = settings.setting.llm_chat_model;
            this.llm_tool_value = settings.setting.llm_tool_model;
            this.llm_chat_prompt = settings.setting.llm_chat_prompt;
            this.llm_chat_show_count = settings.setting.llm_chat_show_count;
            this.llm_chat_memory_count = settings.setting.llm_chat_memory_count;
        },
        getSettings() {
            return {
                llm_chat_model: this.llm_chat_value,
                llm_tool_model: this.llm_tool_value,
                llm_chat_prompt: this.llm_chat_prompt,
                llm_chat_show_count: this.llm_chat_show_count,
                llm_chat_memory_count: this.llm_chat_memory_count
            }
        }
    }
}
</script>