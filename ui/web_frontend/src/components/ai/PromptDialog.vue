<template>
    <el-dialog
        :title="isEdit ? $t('edit') : $t('add')"
        v-model="dialogVisible"
        width="500px"
        @close="handleClose"
    >
        <el-form :model="formData" :rules="rules" ref="promptForm">
            <el-form-item :label="$t('scene')" prop="etype">
                <el-select v-model="formData.etype" :placeholder="$t('pleaseSelect')">
                    <el-option
                        v-for="item in etypeOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    />
                </el-select>
            </el-form-item>
            <el-form-item :label="$t('title')" prop="title">
                <el-input v-model="formData.title" />
            </el-form-item>
            <el-form-item :label="$t('prompt')" prop="prompt">
                <el-input type="textarea" v-model="formData.prompt" :rows="4" />
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="handleClose">{{ $t('cancel') }}</el-button>
                <el-button type="primary" @click="handleSubmit">{{ $t('confirm') }}</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { t } from '@/utils/i18n';

export default {
    name: 'PromptDialog',
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        editData: {
            type: Object,
            default: () => ({})
        },
        isEdit: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            formData: {
                title: '',
                prompt: '',
                etype: ''
            },
            etypeList: [],
            rules: {
                title: [
                    { required: true, message: this.$t('validation_required'), trigger: 'blur' }
                ],
                etype: [
                    { required: true, message: this.$t('validation_required'), trigger: 'change' }
                ],
                prompt: [
                    { required: true, message: this.$t('validation_required'), trigger: 'blur' }
                ]
            }
        }
    },
    async created() {
        await this.loadEtypeList()
    },
    setup() {
        return { t }
    },
    computed: {
        dialogVisible: {
            get() {
                return this.visible
            },
            set(val) {
                this.$emit('update:visible', val)
            }
        },
        etypeOptions() {
            return this.etypeList.map(type => ({
                value: type,
                label: this.$t(`${type}`)
            }))
        }
    },
    watch: {
        visible(val) {
            if (val && this.isEdit) {
                this.formData = { ...this.editData }
            } else if (val) {
                if (Object.keys(this.editData).length) {
                    this.formData = { ...this.editData }
                } else {
                    this.formData = { title: '', prompt: '', etype: '' }
                }
            }
        }
    },
    methods: {
        async loadEtypeList() {
            try {
                setDefaultAuthHeader()
                const response = await axios.get(getURL() + 'api/ai/prompt/get_etype_list/')
                if (response.data.status === 'success') {
                    this.etypeList = response.data.list
                }
            } catch (error) {
                console.error('Load etype list error:', error)
                ElMessage.error(this.$t('loadError'))
            }
        },
        handleClose() {
            this.dialogVisible = false
            this.$refs.promptForm?.resetFields()
        },
        async handleSubmit() {
            try {
                await this.$refs.promptForm.validate()
                await this.submitPrompt()
                this.$emit('success')
                this.handleClose()
            } catch (error) {
                if (error.response) {
                    ElMessage.error(parseBackendError(error) || this.$t('operationFailed'))
                }
                return false
            }
        },
        async submitPrompt() {
            setDefaultAuthHeader()
            if (this.isEdit) {
                await axios.put(getURL() + `api/ai/prompt/${this.editData.idx}/`, this.formData)
            } else {
                await axios.post(getURL() + 'api/ai/prompt/', this.formData)
            }
            ElMessage.success(this.$t('operationSuccess'))
        }
    }
}
</script>
