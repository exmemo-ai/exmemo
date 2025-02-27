<template>
    <el-dialog v-model="dialogVisible" :title="t('aiDialog.title')" width="60%" :before-close="handleClose">
        <div class="common-questions">
            <el-button v-for="q in commonQuestions" :key="q.id" size="small" @click="handleQuestionSelect(q)">
                {{ q.label }}
            </el-button>
        </div>

        <el-input v-model="question" type="textarea" :rows="6" :placeholder="t('aiDialog.questionPlaceholder')" />

        <div class="reference-options">
            <span class="reference-label">{{ t('aiDialog.reference') }}: </span>
            <el-radio-group v-model="referenceType">
                <el-radio :value="'all'">{{ t('aiDialog.all') }}</el-radio>
                <el-radio :value="'selection'">{{ t('aiDialog.referenceSelection') }}</el-radio>
                <el-radio :value="'screen'">{{ t('aiDialog.referenceScreen') }}</el-radio>
                <el-radio :value="'none'">{{ t('aiDialog.referenceNone') }}</el-radio>
            </el-radio-group>
        </div>

        <el-button type="primary" @click="handleSubmit" :loading="loading">
            {{ t('aiDialog.submit') }}
        </el-button>

        <div v-if="answer" class="answer-container">
            <div class="answer-content">{{ answer }}</div>
            <div class="answer-actions">
                <el-button type="primary" size="small" @click="copyAnswer">
                    {{ t('aiDialog.copyAnswer') }}
                </el-button>
                <el-button type="primary" size="small" @click="insertToNote">
                    {{ t('aiDialog.insertToNote') }}
                </el-button>
            </div>
        </div>
    </el-dialog>

    <el-dialog v-model="confirmDialogVisible" :title="t('aiDialog.warning')">
        <p>{{ t('aiDialog.textLengthWarning', { length: checkTextLength(pendingContent) }) }}</p>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="handleCancel">{{ t('cancel') }}</el-button>
                <el-button @click="handleContinue">{{ t('continue') }}</el-button>
                <el-button type="primary" @click="handlePartial">
                    {{ t('aiDialog.usePartial') }}
                </el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>

import axios from 'axios'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getURL, parseBackendError } from '@/components/support/conn'
const { t } = useI18n()

const props = defineProps({
    modelValue: Boolean,
    fullContent: String,
    selectedContent: String,
    screenContent: String,
    defaultReferenceType: {
        type: String,
        default: '', 
        validator: (value) => ['', 'all', 'selection', 'screen', 'none'].includes(value)
    },
    commonQuestions: {
        type: Array,
        default: () => [],
        // format: [{id: string, label: string, question: string}]
    }
})

const emit = defineEmits(['update:modelValue', 'insertNote'])

const dialogVisible = ref(props.modelValue)
const question = ref('')
const answer = ref('')
const loading = ref(false)
const referenceType = ref(props.defaultReferenceType || 'screen')
const confirmDialogVisible = ref(false)
const pendingContent = ref(null)

const handleClose = () => {
    emit('update:modelValue', false)
}

const handleQuestionSelect = (q) => {
    question.value = q.question
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
    if (!question.value) {
        ElMessage({
            message: t('pleaseEnterText'),
            type: 'warning'
        })
        return
    }

    const reference = getReference()
    if (!reference && referenceType.value !== 'none') {
        ElMessage({
            message: t('aiDialog.referenceIsNull'),
            type: 'warning'
        })
        return
    }

    const content = reference ? `${question.value}\n\nContent:\n${reference}` : question.value

    console.log('question length', checkTextLength(content)) // for debug
    if (checkTextLength(content) > 2500) {
        pendingContent.value = content
        confirmDialogVisible.value = true
        return
    }

    await submitQuestion(content)
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
    emit('insertNote', answer.value)
}

watch(() => props.modelValue, (val) => {
    dialogVisible.value = val
    if (val) {
        question.value = ''
        answer.value = ''
        pendingContent.value = null
        referenceType.value = props.defaultReferenceType || (props.selectedContent?.trim() ? 'selection' : 'screen')
    }
})

watch(dialogVisible, (val) => {
    emit('update:modelValue', val)
})
</script>

<style scoped>
.common-questions {
    gap: 5px;
}

.common-questions .el-button {
    margin-left: 5px;
    margin-right: 5px;
    margin-bottom: 10px;
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
</style>
