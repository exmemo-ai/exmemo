<template>
    <el-form>
        <div class="settings-section">
            <div class="settings-section-header">
                <div class="header-left">
                    <el-select v-model="selectedType" class="type-filter" :placeholder="$t('all')">
                        <el-option value="" :label="$t('all')" />
                        <el-option
                            v-for="type in availableTypes"
                            :key="type"
                            :value="type"
                            :label="$t(type)"
                        />
                    </el-select>
                </div>
                <el-button class="header-button" @click="handleResetPrompt">
                    {{ $t('ai.resetPrompt') }}
                </el-button>
                <el-button class="header-button" @click="handleAdd">
                    {{ $t('ai.addPrompt') }}
                </el-button>
            </div>
            <div class="settings-section-content">
                <div class="prompt-list">
                    <el-table :data="filteredPrompts" style="width: 100%" row-key="idx">
                        <el-table-column :label="$t('scene')" min-width="80" width="80">
                            <template #default="scope">
                                {{ $t(`${scope.row.etype}`) }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="title" :label="$t('title')" min-width="120" width="120" />
                        <el-table-column prop="prompt" :label="$t('prompt')" min-width="200" show-overflow-tooltip>
                            <template #default="scope">
                                <div class="prompt-cell">{{ scope.row.prompt }}</div>
                            </template>
                        </el-table-column>
                        <el-table-column :label="$t('operation')" min-width="60" width="60" fixed="right">
                            <template #default="scope">
                                <div class="operation-buttons">
                                    <el-icon 
                                        class="edit-icon"
                                        @click="handleEdit(scope.row)"
                                    >
                                        <Edit />
                                    </el-icon>
                                    <el-icon 
                                        class="delete-icon"
                                        @click="handleDelete(scope.row)"
                                    >
                                        <Delete />
                                    </el-icon>
                                </div>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>
    </el-form>

    <PromptDialog
        v-model:visible="dialogVisible"
        :is-edit="isEdit"
        :edit-data="currentPrompt"
        @success="handleSuccess"
    />
</template>

<script>
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn'
import axios from 'axios';
import { Delete, Edit } from '@element-plus/icons-vue'
import PromptDialog from '@/components/ai/PromptDialog.vue'

export default {
    name: 'SettingPrompt',
    components: {
        Delete,
        Edit,
        PromptDialog
    },
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        return {
            prompts: [],
            dialogVisible: false,
            isEdit: false,
            currentPrompt: {},
            selectedType: '',
            rules: {
                title: [
                    { required: true, message: this.$t('validation_required'), trigger: 'blur' }
                ],
                prompt: [
                    { required: true, message: this.$t('validation_required'), trigger: 'blur' }
                ],
                etype: [
                    { required: true, message: this.$t('validation_required'), trigger: 'change' }
                ]
            }
        }
    },
    computed: {
        availableTypes() {
            const types = new Set(this.prompts.map(item => item.etype));
            return Array.from(types);
        },
        filteredPrompts() {
            if (!this.selectedType) {
                return this.prompts;
            }
            return this.prompts.filter(item => item.etype === this.selectedType);
        }
    },
    async created() {
        await this.loadPrompts();
    },
    methods: {
        async loadPrompts() {
            try {
                setDefaultAuthHeader();
                const response = await axios.get(getURL() + 'api/ai/prompt/');
                this.prompts = response.data.results || [];
            } catch (error) {
                console.error('Load prompts error:', error);
                ElMessage.error(this.$t('operationFailed'));
            }
        },
        handleAdd() {
            this.isEdit = false
            this.currentPrompt = {}
            this.dialogVisible = true
        },
        handleEdit(row) {
            this.isEdit = true
            this.currentPrompt = { ...row }
            this.dialogVisible = true
        },
        async handleResetPrompt() {
            try {
                await ElMessageBox.confirm(
                    this.$t('ai.resetPromptConfirm'),
                    this.$t('ai.warning'),
                    {
                        confirmButtonText: this.$t('confirm'),
                        cancelButtonText: this.$t('cancel'),
                        type: 'warning',
                    }
                );
                setDefaultAuthHeader();
                await axios.get(getURL() + `api/ai/prompt/reset_prompt`);
                await this.loadPrompts();
                ElMessage.success(this.$t('operationSuccess'));
            } catch (error) {
                if (error === 'cancel') return;
                console.error('Reset prompt error:', error);
                ElMessage.error(parseBackendError(error) || this.$t('operationFailed'));
            }
        },     
        async handleSuccess() {
            await this.loadPrompts()
        },
        async handleDelete(row) {
            try {
                setDefaultAuthHeader();
                await axios.delete(getURL() + `api/ai/prompt/${row.idx}/`);
                await this.loadPrompts();
                ElMessage.success(this.$t('operationSuccess'));
            } catch (error) {
                console.error('Delete error:', error);
                ElMessage.error(parseBackendError(error) || this.$t('operationFailed'));
            }
        }
    }
}
</script>

<style scoped>
.prompt-list {
    margin-bottom: 20px;
}

.add-prompt {
    max-width: 600px;
}

.delete-icon {
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s;
}

.delete-icon:hover {
    transform: scale(1.2);
}

.settings-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    gap: 0px;
}

.header-button {
    margin-left: 5px !important;
}

.operation-buttons {
    display: flex;
    gap: 5px;
}

.edit-icon {
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s;
    color: #409EFF;
}

.edit-icon:hover {
    transform: scale(1.2);
}

.header-left {
    flex-grow: 1;
    display: flex;
    align-items: center;
    gap: 20px;
}

.type-filter {
    width: 150px;
}

.prompt-cell {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}
</style>
