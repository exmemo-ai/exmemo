<template>
    <el-dialog 
        v-model="dialogVisible" 
        :title="t('ai.title')" 
        :width="dialogWidth"
        :before-close="handleClose"
    >
        <template #header>
            <div class="dialog-header">
                <span class="dialog-title">{{ t('ai.title') }}</span>
                <div class="prompt-actions">
                    <el-tooltip :content="t('ai.addPrompt')" placement="top">
                        <el-button type="primary" size="small" @click="handleAddPrompt">
                            <el-icon><Plus /></el-icon>
                        </el-button>
                    </el-tooltip>
                    <el-tooltip :content="t('ai.savePrompt')" placement="top">
                        <el-button type="primary" size="small" @click="handleSavePrompt" :disabled="!prompt">
                            <el-icon><DocumentAdd /></el-icon>
                        </el-button>
                    </el-tooltip>
                    <el-tooltip :content="t('ai.managePrompts')" placement="top">
                        <el-button type="primary" size="small" @click="handleManagePrompts">
                            <el-icon><Setting /></el-icon>
                        </el-button>
                    </el-tooltip>
                </div>
            </div>
        </template>

        <div class="common-prompts">
            <el-button v-for="q in commonQuestions" :key="q.id" size="small" @click="handleQuestionSelect(q)">
                {{ q.title }}
            </el-button>
        </div>

        <el-input v-model="prompt" type="textarea" :rows="6" :placeholder="t('ai.questionPlaceholder')" />

        <div class="reference-options">
            <span class="reference-label">{{ t('ai.reference') }}: </span>
            <el-radio-group v-model="referenceType">
                <el-radio :value="'all'" v-if="props.fullContent?.trim()">{{ t('ai.all') }}</el-radio>
                <el-radio :value="'selection'" v-if="props.selectedContent?.trim()">{{ t('ai.referenceSelection') }}</el-radio>
                <el-radio :value="'screen'" v-if="props.screenContent?.trim()">{{ t('ai.referenceScreen') }}</el-radio>
                <el-radio :value="'none'">{{ t('ai.referenceNone') }}</el-radio>
                <el-radio :value="'specific'" v-if="props.specificContent?.trim()">{{ specificContent }}</el-radio>
            </el-radio-group>
        </div>

        <el-button type="primary" @click="handleSubmit" :loading="loading">
            {{ t('ai.submit') }}
        </el-button>

        <div v-if="answer" class="answer-container">
            <div class="answer-content">{{ answer }}</div>
            <div class="answer-actions">
                <el-button type="primary" size="small" @click="copyAnswer">
                    {{ t('ai.copyAnswer') }}
                </el-button>
                <el-button type="primary" size="small" @click="insertToNote">
                    {{ t('ai.insertToNote') }}
                </el-button>
            </div>
        </div>
    </el-dialog>

    <el-dialog v-model="confirmDialogVisible" :title="t('ai.warning')">
        <p>{{ t('ai.textLengthWarning', { length: checkTextLength(pendingContent) }) }}</p>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="handleCancel">{{ t('cancel') }}</el-button>
                <el-button @click="handleContinue">{{ t('continue') }}</el-button>
                <el-button type="primary" @click="handlePartial">
                    {{ t('ai.usePartial') }}
                </el-button>
            </span>
        </template>
    </el-dialog>

    <PromptDialog
        v-model:visible="promptDialogVisible"
        :is-edit="false"
        :edit-data="currentPrompt"
        @success="handlePromptSuccess"
        ref="promptDialog"
    />
</template>

<script setup>

import axios from 'axios'
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus, Setting, DocumentAdd } from '@element-plus/icons-vue'
import PromptDialog from '@/components/ai/PromptDialog.vue'
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'

const { t } = useI18n()

const props = defineProps({
    modelValue: Boolean,
    fullContent: String,
    selectedContent: String,
    screenContent: String,
    specificContent: String,
    etype: String,
    defaultReferenceType: {
        type: String,
        default: '', 
        validator: (value) => ['', 'all', 'selection', 'screen', 'none'].includes(value)
    }
})

const emit = defineEmits([
    'update:modelValue', 
    'insert-note',
])

const dialogVisible = ref(props.modelValue)
const idx = ref('')
const prompt = ref('')
const answer = ref('')
const loading = ref(false)
const referenceType = ref(props.defaultReferenceType || 'screen')
const confirmDialogVisible = ref(false)
const pendingContent = ref(null)
const promptDialogVisible = ref(false)
const promptDialog = ref(null)
const currentPrompt = ref(null)
const commonQuestions = ref([])

const dialogWidth = computed(() => {
    return window.innerWidth <= 768 ? '90%' : '60%'
})

onMounted(() => {
    window.addEventListener('resize', () => {
        dialogWidth.value = window.innerWidth <= 768 ? '90%' : '60%'
    })
})

onUnmounted(() => {
    window.removeEventListener('resize', () => {})
})

const handleClose = () => {
    emit('update:modelValue', false)
}

const handleQuestionSelect = (q) => {
    idx.value = q.idx
    prompt.value = q.prompt
}

const getReference = () => {
    switch (referenceType.value) {
        case 'selection':
            if (!props.selectedContent || props.selectedContent.trim() === '') {
                return null
            }
            return props.selectedContent
        case 'screen':
            if (!props.screenContent || props.screenContent.trim() === '') {
                return null
            }
            return props.screenContent
        case 'specific':
            if (!props.specificContent || props.specificContent.trim() === '') {
                return null
            }
            return props.specificContent
        case 'none':
            return null
        default:
            if (!props.fullContent || props.fullContent.trim() === '') {
                return null
            }
            return props.fullContent
    }
}

const checkTextLength = (text) => {
    return text ? text.length : 0
}

const handleCancel = () => {
    confirmDialogVisible.value = false
    pendingContent.value = null
}

const handleContinue = async () => {
    confirmDialogVisible.value = false
    await submitQuestion(pendingContent.value)
}

const handlePartial = async () => {
    confirmDialogVisible.value = false
    const truncatedContent = pendingContent.value.substring(0, 1000)
    await submitQuestion(truncatedContent)
}

const submitQuestion = async (content) => {
    //for test
    //answer.value = content;
    //return;
    loading.value = true
    try {
        const formData = new FormData()
        formData.append('content', content)
        formData.append('rtype', 'gpt')

        const response = await axios.post(getURL() + 'api/paper/', formData)
        
        if (response.data.status === 'success') {
            answer.value = response.data.info
        } else {
            ElMessage({
                message: t('operationFailed') + ': ' + response.data.info,
                type: 'error'
            })
        }
    } catch (err) {
        parseBackendError(err)
    } finally {
        loading.value = false
    }
}

const handleSubmit = async () => {
    if (!prompt.value) {
        ElMessage({
            message: t('pleaseEnterText'),
            type: 'warning'
        })
        return
    }

    const reference = getReference()
    if (!reference && referenceType.value !== 'none') {
        ElMessage({
            message: t('ai.referenceIsNull'),
            type: 'warning'
        })
        return
    }

    const content = reference ? `${prompt.value}\n\nContent:\n${reference}` : prompt.value

    console.log('question length', checkTextLength(content)) // for debug
    if (checkTextLength(content) > 2500) {
        pendingContent.value = content
        confirmDialogVisible.value = true
        return
    }

    await submitQuestion(content)
}

const handleManagePrompts = () => {
    dialogVisible.value = false
    window.open('/user_setting?section=prompt', '_blank')
}

const copyAnswer = () => {
    if (!answer.value) return

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(answer.value)
            .then(() => ElMessage.success(t('copySuccess')))
            .catch(() => fallbackCopyTextToClipboard(answer.value))
    } else {
        fallbackCopyTextToClipboard(answer.value)
    }
}

const fallbackCopyTextToClipboard = (text) => {
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    try {
        const successful = document.execCommand('copy')
        if (successful) {
            ElMessage.success(t('copySuccess'))
        } else {
            ElMessage.error(t('copyFailed'))
        }
    } catch (err) {
        ElMessage.error(t('clipboardNotSupported'))
    }
    document.body.removeChild(textArea)
}

const insertToNote = () => {
    if (!answer.value) return
    emit('insert-note', answer.value)
}

const handleSavePrompt = async () => {
    if (!prompt.value) return
    if (!idx.value) {
        handleAddPrompt()
        return 
    }
    const item = commonQuestions.value.find(q => q.idx === idx.value)
    if (!item) return

    setDefaultAuthHeader()
    const formData = new FormData()
    item.prompt = prompt.value
    for (const key in item) {
        formData.append(key, item[key])
    }
    await axios.put(getURL() + `api/ai/prompt/${idx.value}/`, formData)
    ElMessage.success(t('saveSuccess'))
    loadPrompts();
}

const handleAddPrompt = () => {
    currentPrompt.value = {
        title: '',
        prompt: prompt.value,
        etype: props.etype
    }
    promptDialogVisible.value = true
}

const handlePromptSuccess = () => {
    ElMessage.success(t('saveSuccess'))
    loadPrompts();
}

const loadPrompts = async () => {
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + 'api/ai/prompt/');
        const prompts = response.data.results || [];
        commonQuestions.value = prompts.filter(p => p.etype === props.etype);
    } catch (error) {
        console.error('Load prompts error:', error);
        ElMessage.error(t('operationFailed'));
        commonQuestions.value = [];
    }
}

watch(() => props.modelValue, (val) => {
    dialogVisible.value = val
    if (val) {
        loadPrompts();
        idx.value = ''
        prompt.value = ''
        answer.value = ''
        pendingContent.value = null
        
        const defaultType = props.defaultReferenceType || (props.selectedContent?.trim() ? 'selection' : 'screen')
        if (defaultType !== 'none') {
            const content = getReference()
            if (!content) {
                referenceType.value = 'none'
            } else {
                referenceType.value = defaultType
            }
        }
    }
})

watch(dialogVisible, (val) => {
    emit('update:modelValue', val)
})
</script>

<style scoped>
.common-prompts {
    gap: 5px;
    margin-bottom: 5px;
    max-height: calc(32px * 4 + 4px * 2);
    overflow-y: auto;
    padding: 2px;
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
}

.common-prompts .el-button {
    margin: 2px;
    flex-shrink: 0;
}

.reference-options {
    margin: 15px 0;
}

.answer-container {
    margin-top: 20px;
    padding: 15px;
    background-color: var(--el-bg-color-page);
    border-radius: 4px;
    max-height: 200px;
    overflow-y: auto;
}

.answer-content {
    white-space: pre-wrap;
    word-wrap: break-word;
}

.answer-actions {
    margin-top: 5px;
    display: flex;
    gap: 5px;
    position: sticky;
    bottom: 0;
    background-color: transparent;
    padding-top: 5px;
    justify-content: flex-end;
}

:deep(.el-dialog__body) {
    max-height: calc(80vh - 100px);
    overflow-y: auto;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

:deep(.el-radio) {
    margin-right: 10px;
}

.reference-label {
    margin-right: 10px;
}

.dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.dialog-title {
    font-size: 18px;
    font-weight: bold;
}

.prompt-actions {
    display: flex;
    gap: 2px;
}

.prompt-actions .el-button {
    margin: 0px;
}

</style>
