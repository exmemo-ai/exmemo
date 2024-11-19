<template>
    <el-dialog v-model="dialogVisible" :title="form.idx === null ? $t('new') : $t('edit')" :width="dialogWidth"
        :before-close="handleClose">

        <div v-if="form.idx === null" style="display: flex; align-items: center; margin-bottom: 10px">
            <input type="radio" id="upload" value="file" v-model="form.etype">
            <label for="upload">{{ $t('uploadFile') }}</label>

            <input type="radio" id="record" value="record" v-model="form.etype">
            <label for="record">{{ $t('record') }}</label>

            <input type="radio" id="addWeb" value="web" v-model="form.etype">
            <label for="addWeb">{{ $t('addWeb') }}</label>
        </div>
        <div v-if="form.idx !== null" style="display: flex; align-items: center; margin-bottom: 10px">
            <label v-if="form.etype === 'file'"><strong>{{ $t('file') }}</strong></label>
            <label v-if="form.etype === 'record'"><strong>{{ $t('record') }}</strong></label>
            <label v-if="form.etype === 'web'"><strong>{{ $t('web') }}</strong></label>
            <label v-if="form.etype === 'note'"><strong>{{ $t('note') }}</strong></label>
        </div>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <el-input v-if="!form.idx" type="textarea" :rows="6" v-model="form.addr"
                        placeholder="http://"></el-input>
                    <div v-else width="100%">
                        <a :href="form.addr"
                            style="display: block; word-break: break-all; max-height: 6em; overflow: hidden; text-overflow: ellipsis;"
                            width="100%">{{ form.addr }}</a>
                    </div>
                </div>
                <div v-if="form.etype === 'file' || form.etype === 'note'" width="100%">
                    <div v-if="!form.idx">
                        <div>
                            <input type="file" @change="handleFileUpload" width="100%">
                        </div>
                        <div v-if="saveProgress > 0" style="margin: 10px">
                            <progress :value="saveProgress" max="100">{{ saveProgress }}%</progress>
                            <el-button style="margin: 2px;" @click="cancelUpload">{{ $t('cancel') }}</el-button>
                        </div>
                    </div>
                    <span v-else width="100%"
                        style="display: block; word-break: break-all; max-height: 6em; overflow: hidden; text-overflow: ellipsis; white-space: normal;">{{
                            $t('file') }}: {{file_path}}</span>
                </div>
                <div v-if="form.etype === 'record'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.raw" :placeholder="$t('recordContent')"></el-input>
                </div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <el-button style="margin: 2px;" width="100%" type="primary" @click="doSave">{{ $t('save') }}</el-button>
                <el-button style="margin: 2px;" width="100%" @click="extractInfo">{{ $t('extract') }}</el-button>
                <el-button style="margin: 2px;" width="100%" v-if="form.idx" @click="showDeleteConfirmation">{{ $t('delete')
                }}</el-button>
                <el-button style="margin: 2px;" width="100%" v-if="(form.etype === 'file' || form.etype === 'note') && form.idx"
                    @click="downloadFile"> {{ $t('download') }}</el-button>
                <el-button style="margin: 2px;" width="100%" v-if="form.etype === 'file' && form.idx" @click="rename">{{ $t('rename')
                }}</el-button>
            </div>
        </div>

        <hr style="margin: 10px 0;">

        <div style="display: flex;margin-bottom: 5px;">
            <div style="margin-right: 5px; white-space: nowrap;">
                <el-label>{{ $t('title') }}</el-label>
            </div>
            <div style="flex-grow: 1;">
                <el-input v-model="form.title" :placeholder="form.etype === 'file' || form.etype === 'note' ? $t('autoExtract') : ''"
                    :readonly="form.etype === 'file' || form.etype === 'note'"></el-input>
            </div>
        </div>
        <div style="display: flex;margin-bottom: 5px;">
            <div style="margin-right: 5px; white-space: nowrap; display: flex; align-items: center;">
                <el-label>{{ $t('type') }}</el-label>
            </div>
            <div style="flex-grow: 1">
                <el-input v-model="form.ctype" :placeholder="$t('autoExtract')"></el-input>
            </div>
        </div>

        <div style="display: flex;margin-bottom: 5px;">
            <div style="margin-right: 5px; white-space: nowrap; display: flex; align-items: center;">
                <label>{{ $t('source') }}</label>
            </div>
            <div style="flex-grow: 1; display: flex; align-items: flex-start;">
                <el-radio-group v-model="form.atype">
                    <el-radio :label="'subjective'">{{ $t('subjective') }}</el-radio>
                    <el-radio :label="'objective'">{{ $t('objective') }}</el-radio>
                    <el-radio :label="'third_party'">{{ $t('thirdParty') }}</el-radio>
                </el-radio-group>
            </div>
        </div>
        <div style="display: flex;margin-bottom: 5px;">
            <div style="margin-right: 5px; white-space: nowrap; display: flex; align-items: center;">
                <label>{{ $t('status') }}</label>
            </div>
            <div style="flex-grow: 1; display: flex; align-items: flex-start;">
                <el-radio-group v-model="form.status">
                    <el-radio :label="'todo'">{{ $t('toDo') }}</el-radio>
                    <el-radio :label="'collect'">{{ $t('collect') }}</el-radio>
                </el-radio-group>
            </div>
        </div>
        <span class="dialog-footer">
        </span>
    </el-dialog>
</template>
  
<script>
import axios from 'axios';
import { getURL, parseBackendError, parseBlobData } from '@/components/support/conn'
export default {
    data() {
        return {
            isMobile: false,
            parent_obj: null,
            file_path: null,
            file: null,
            dialogVisible: false,
            saveProgress: 0,
            cancelTokenSource: null,
            form: {
                idx: null,
                title: '',
                raw: '',
                ctype: '',
                etype: 'record',
                atype: '',
                level: '-1',
                status: '',
                addr: '',
            },
        };
    },
    methods: {
        openEditDialog(parent_obj, row = null) {
            this.saveProgress = 0;
            this.parent_obj = parent_obj;
            if (row) {
                this.form.idx = row.idx
                this.form.ctype = row.ctype
                this.form.etype = row.etype
                this.form.title = row.title
                this.form.raw = row.raw
                this.form.atype = row.atype
                this.form.status = row.status
                this.form.addr = row.addr
                this.file_path = this.form.addr;
            } else {
                this.form.idx = null
                this.form.ctype = ''
                this.form.etype = 'record'
                this.form.title = ''
                this.form.atype = ''
                this.form.raw = ''
                this.form.status = ''
                this.form.addr = ''
            }
            console.log(this.form)
            this.dialogVisible = true;
        },
        closeEditDialog() {
            this.dialogVisible = false;
        },
        handleClose(done) {
            console.log(this.$t('dialogClosed'));
            this.closeEditDialog();
            done();
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
            if (this.isMobile) {
                this.dialogWidth = '90%';
            } else {
                this.dialogWidth = '60%';
            }
        },
        rename() {
            this.$prompt(this.$t('inputNewFileName'), this.$t('promptTitle'), {
                confirmButtonText: this.$t('confirm'),
                cancelButtonText: this.$t('cancel'),
                //inputPattern: '/^[a-zA-Z0-9_\-\.]+$/', # xieyan 240927 tmp disable
                inputErrorMessage: this.$t('filenamePatternError'),
            }).then(({ value }) => {
                console.log(value);
                let func = 'api/entry/data/'
                const formData = new FormData();
                formData.append('idx', this.form.idx);
                formData.append('addr', value);
                axios.put(getURL() + func + this.form.idx + '/', formData)
                    .then(response => {
                        console.log('success');
                        console.log(response.data);
                        if (response.data.status == 'success') {
                            this.$message({
                                type: 'success',
                                message: this.$t('renameSuccess')
                            });
                            if (this.parent_obj) {
                                this.parent_obj.fetchData();
                            }
                            this.closeEditDialog();
                        } else {
                            this.$message({
                                type: 'error',
                                message: this.$t('renameFail'),
                            });
                        }
                    })
                    .catch(error => {
                        parseBackendError(this, error);
                    });
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: this.$t('renameCancelled'),
                });
            });
        },
        async realSave() {
            let func = 'api/entry/data/'
            const formData = new FormData();
            if (this.form.ctype !== '') {
                formData.append('ctype', this.form.ctype);
            }
            if (this.form.etype !== '') {
                formData.append('etype', this.form.etype);
            }
            if (this.form.title !== '') {
                formData.append('title', this.form.title);
            }
            if (this.form.status !== '') {
                formData.append('status', this.form.status);
            }
            if (this.form.atype !== '') {
                formData.append('atype', this.form.atype);
            }
            if (this.form.idx !== null) {
                formData.append('idx', this.form.idx);
            }
            console.log(this.$t('dialogClosed'));
            console.log(this.form);

            if (this.form.etype === 'record') {
                if (this.form.raw === '') {
                    this.$message({
                        type: 'error',
                        message: this.$t('inputRecordContent'),
                    });
                    return;
                }
                formData.append('raw', this.form.raw);
            } else if (this.form.etype === 'file' && this.form.idx === null) {
                if (!this.file) {
                    this.$message({
                        type: 'error',
                        message: this.$t('selectFileError'),
                    });
                    return;
                }
                formData.append('etype', 'file')
                formData.append('files', this.file);
                formData.append(`filenames`, this.file.name);
                formData.append(`filepaths`, `${this.file.name}`);
            } else if (this.form.etype === 'web') {
                if (this.form.addr === '') {
                    this.$message({
                        type: 'error',
                        message: this.$t('inputWebAddressError'),
                    });
                    return;
                }
                formData.append('addr', this.form.addr);
            }
            this.cancelTokenSource = axios.CancelToken.source();
            if (this.form.idx !== null) {
                func += this.form.idx + '/';
                await axios.put(getURL() + func, formData)
                    .then(response => {
                        console.log('success');
                        console.log(response.data);
                        if (response.data.status == 'success') {
                            this.$message({
                                type: 'success',
                                message: this.$t('updateSuccess'),
                            });
                            if (this.parent_obj) {
                                this.parent_obj.fetchData();
                            }
                        } else {
                            this.$message({
                                type: 'error',
                                message: this.$t('updateFail'),
                            });
                        }
                    })
                    .catch(error => {
                        parseBackendError(this, error);
                    });
            } else {
                await axios.post(getURL() + func, formData, {
                    onUploadProgress: progressEvent => {
                        this.saveProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        console.log('saveProgress' + this.saveProgress)
                    },
                    cancelToken: this.cancelTokenSource.token
                })
                    .then(response => {
                        if (response.data.status == 'success') {
                            this.$message({
                                type: 'success',
                                message: this.$t('saveSuccess'),
                            });
                            if (this.parent_obj) {
                                this.parent_obj.fetchData();
                            }
                        } else {
                            this.$message({
                                type: 'error',
                                message: this.$t('saveFail'),
                            });
                        }
                    })
                    .catch(error => {
                        if (axios.isCancel(error)) {
                            this.$message({
                                type: 'info',
                                message: this.$t('operationCancelled'),
                            });
                        } else {
                            parseBackendError(this, error);
                        }
                    });
            }
        },
        async doSave() {
            console.log("doSave");
            await this.realSave();
            this.closeEditDialog();
        },
        cancelUpload() {
            if (this.cancelTokenSource) {
                this.cancelTokenSource.cancel('cancel by user');
                this.uploadProgress = 0;
            }
        },
        realDownloadFile(obj, idx, filename) {
            console.log(this.$t('downloadFile', { idx, filename }));
            let table_name = 'data'
            axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/' + 'download', {
                responseType: 'blob',
            })
                .then(response => {
                    parseBlobData(response, obj, filename);
                });
        },
        downloadFile() {
            console.log(this.$t('download', { idx: this.form.idx }));
            let filename = this.file_path.split('/').pop();
            this.realDownloadFile(this, this.form.idx, filename);
        },
        showDeleteConfirmation() {
            this.$confirm(this.$t('deleteConfirmation'), this.$t('promptTitle'), {
                confirmButtonText: this.$t('confirm'),
                cancelButtonText: this.$t('cancel'),
                type: 'warning'
            }).then(() => {
                this.realDelete()
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: this.$t('cancelDelete')
                });
            });
        },
        extractInfo() {
            let func = 'api/entry/tool/'
            console.log(getURL() + func)
            const formData = new FormData();
            formData.append('rtype', 'extract');
            formData.append('etype', this.form.etype);
            if (this.form.etype === 'record') {
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
        realDelete() {
            console.log('Delete', this.form.idx);
            let table_name = 'data'
            console.log(getURL() + 'api/entry/' + table_name + '/' + this.form.idx + '/')
            axios.delete(getURL() + 'api/entry/' + table_name + '/' + this.form.idx + '/')
                .then(response => {
                    console.log('response', response);
                    if (response.data.status == 'success') {
                        this.$message({
                            type: 'success',
                            message: this.$t('deleteSuccess')
                        });
                        this.closeEditDialog();
                        if (this.parent_obj) {
                            this.parent_obj.fetchData();
                        }
                    } else {
                        this.$message({
                            type: 'error',
                            message: this.$t('deleteFail')
                        });
                    }
                })
                .catch(error => {
                    parseBackendError(this, error);
                });
        },
        handleFileUpload(event) {
            this.file_path = event.target.files[0].name;
            this.file = event.target.files[0];
        },
    },
    mounted() {
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    },
};
</script>