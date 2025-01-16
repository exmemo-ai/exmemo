<template>
    <div class="form-row">
        <div class="label-container">
            <strong>{{ $t('metaData') }}</strong>
        </div>
        <div class="content-container right-aligned">
            <el-button type="primary" size="small" @click="extractInfo">{{ $t('autoExtract') }}</el-button>
        </div>
    </div>
    <div class="form-row">
        <div class="label-container">
            <el-text>{{ $t('title') }}</el-text>
        </div>
        <div class="content-container">
            <el-input v-model="form.title" :placeholder="form.etype === 'file' || form.etype === 'note' ? $t('autoExtract') : ''"
                :readonly="form.etype === 'note'"></el-input>
        </div>
    </div>
    <div class="form-row">
        <div class="label-container">
            <el-text>{{ $t('type') }}</el-text>
        </div>
        <div class="content-container">
            <el-input v-model="form.ctype" :placeholder="$t('autoExtract')"></el-input>
        </div>
    </div>

    <div class="form-row">
        <div class="label-container">
            <label>{{ $t('source') }}</label>
        </div>
        <div class="content-container align-start">
            <el-radio-group v-model="form.atype">
                <el-radio value="subjective">{{ $t('subjective') }}</el-radio>
                <el-radio value="objective">{{ $t('objective') }}</el-radio>
                <el-radio value="third_party">{{ $t('thirdParty') }}</el-radio>
            </el-radio-group>
        </div>
    </div>
    <div class="form-row">
        <div class="label-container">
            <label>{{ $t('status') }}</label>
        </div>
        <div class="content-container align-start">
            <el-radio-group v-model="form.status">
                <el-radio value="todo">{{ $t('toDo') }}</el-radio>
                <el-radio value="collect">{{ $t('collect') }}</el-radio>
            </el-radio-group>
        </div>
    </div>

    <div v-if="saveProgress > 0" style="margin: 10px">
        <progress :value="saveProgress" max="100">{{ saveProgress }}%</progress>
        <el-button style="margin: 2px;" @click="cancelUpload">{{ $t('cancel') }}</el-button>
    </div>
</template>

<script>
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn'
import { saveEntry } from './dataUtils';

export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        file_path: {
            type: String,
            default: null
        },
        file: {
            type: Object,
            default: null
        },
        parent_obj: {
            type: Object,
            default: null
        }
    },
    data() {
        return {
            cancelTokenSource: null,
            saveProgress: 0,
        }
    },
    methods: {
        cancelUpload() {
            if (this.cancelTokenSource) {
                this.cancelTokenSource.cancel('cancel by user');
                this.saveProgress = 0;
            }
        },
        extractInfo() {
            let func = 'api/entry/tool/'
            console.log(getURL() + func)
            const formData = new FormData();
            formData.append('rtype', 'extract');
            formData.append('etype', this.form.etype);
            if (this.form.etype === 'record' || this.form.etype === 'chat') {
                formData.append('raw', this.form.raw);
            } else if (this.form.etype === 'web') {
                formData.append('addr', this.form.addr);
            } else if (this.form.etype === 'file') {
                formData.append('addr', this.file_path);
            }
            axios.post(getURL() + func, formData).then(response => {
                console.log('ret1', response);
                console.log('ret2', response.data);
                console.log('ret3', response.data.status);
                if (response.data.status == 'success') {
                    if (response.data.dic.title !== null) {
                        this.form.title = response.data.dic.title;
                    }
                    if (response.data.dic.atype !== null) {
                        this.form.atype = response.data.dic.atype;
                    }
                    if (response.data.dic.ctype !== null) {
                        this.form.ctype = response.data.dic.ctype;
                    }
                    if (response.data.dic.status !== null) {
                        this.form.status = response.data.dic.status;
                    }
                    console.log(this.$t('extractSuccess'));
                } else {
                    this.$message({
                        type: 'error',
                        message: this.$t('extractFail')
                    });
                }
            }).catch(error => {
                parseBackendError(this, error);
            });
        },
        async realSave() {
            return await saveEntry({
                parentObj: this.parent_obj,
                form: this.form,
                file: this.file,
                onProgress: (progress) => {
                    this.saveProgress = progress;
                },
                onUploadStart: (cancelTokenSource) => {
                    this.cancelTokenSource = cancelTokenSource;
                }
            });
        },
        resetProgress() {
            this.saveProgress = 0;
        }
    }
}
</script>

<style scoped>
.form-row {
    display: flex;
    margin-bottom: 5px;
}

.label-container {
    margin-right: 10px;
    white-space: nowrap;
    display: flex;
    align-items: center;
}

.content-container {
    flex-grow: 1;
    display: flex;
}

.right-aligned {
    justify-content: flex-end;
}

.align-start {
    align-items: flex-start;
}

@media screen and (max-width: 768px) {
    :deep(.el-radio) {
        margin-right: 10px;
    }
}
</style>