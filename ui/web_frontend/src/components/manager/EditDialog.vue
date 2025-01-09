<template>
    <el-dialog v-model="dialogVisible" :title="$t('edit')" :width="dialogWidth"
        :before-close="handleClose">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
            <div>
                <label v-if="form.etype === 'file'"><strong>{{ $t('file') }}</strong></label>
                <label v-if="form.etype === 'record'"><strong>{{ $t('record') }}</strong></label>
                <label v-if="form.etype === 'web'"><strong>{{ $t('web') }}</strong></label>
                <label v-if="form.etype === 'note'"><strong>{{ $t('note') }}</strong></label>
                <label v-if="form.etype === 'chat'"><strong>{{ $t('chat') }}</strong></label>
            </div>
            <el-button-group>
                <el-button size="small" type="primary" @click="doSave">{{ $t('save') }}</el-button>
                <el-button size="small" @click="showDeleteConfirmation">{{ $t('delete') }}</el-button>
                <el-button size="small" @click="viewContent">{{ $t('view') }}</el-button>
                <el-button size="small" v-if="form.etype === 'file'" @click="downloadFile">{{ $t('download') }}</el-button> 
            </el-button-group>
        </div>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <div width="100%">
                        <a :href="form.addr"
                            style="display: block; word-break: break-all; max-height: 6em; overflow: hidden; text-overflow: ellipsis;"
                            width="100%">{{ form.addr }}</a>
                    </div>
                </div>
                <div v-if="form.etype === 'file' || form.etype === 'note'" width="100%">
                    <span width="100%"
                        style="display: block; word-break: break-all; max-height: 6em; overflow: hidden; text-overflow: ellipsis; white-space: normal;">{{
                            $t('path') }}: {{file_path}}</span>
                </div>
                <div v-if="form.etype === 'record'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.raw" :placeholder="$t('recordContent')"></el-input>
                </div>
                <div v-if="form.etype === 'chat'" width="100%">
                    <div 
                        class="chat-content"
                        style="
                            height: 120px;
                            max-height: 120px;
                            padding: 8px 12px;
                            border: 1px solid #dcdfe6;
                            border-radius: 4px;
                            background-color: #f5f7fa;
                            white-space: pre-wrap;
                            overflow-y: auto;
                        "
                    >{{ form.raw }}</div>
                </div>

            </div>
        </div>

        <hr style="margin: 10px 0;">
        <DataEditor 
            ref="typeSelector"
            :form="form"
            :file_path="file_path"
            :file="file"
            :parent_obj="parent_obj"
            :save-progress="saveProgress"
            @update-progress="progress => saveProgress = progress"
        />
        <span class="dialog-footer">
        </span>
    </el-dialog>
</template>
  
<script>
import axios from 'axios';
import { getURL, parseBackendError, parseBlobData } from '@/components/support/conn'
import DataEditor from './DataEditor.vue'

export default {
    components: {
        DataEditor
    },
    data() {
        return {
            dialogWidth: '60%',
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
        openDialog(parent_obj, row) {
            this.saveProgress = 0;
            this.parent_obj = parent_obj;
            this.form.idx = row.idx;
            this.form.ctype = row.ctype;
            this.form.etype = row.etype;
            this.form.title = row.title;
            this.form.raw = row.raw;
            this.form.atype = row.atype;
            this.form.status = row.status;
            this.form.addr = row.addr;
            this.file_path = this.form.addr;
            this.base_title = row.title;
            console.log(this.form);
            this.dialogVisible = true;
        },
        closeDialog() {
            this.dialogVisible = false;
        },
        handleClose(done) {
            console.log(this.$t('dialogClosed'));
            this.closeDialog();
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
        async realRename(newFileName) {
            let func = 'api/entry/data/'
            const formData = new FormData();
            formData.append('idx', this.form.idx);
            formData.append('addr', newFileName);
            try {
            const response = await axios.put(getURL() + func + this.form.idx + '/', formData);
            if (response.data.status == 'success') {
                this.$message({
                    type: 'success',
                    message: this.$t('renameSuccess')
                });
                if (this.parent_obj) {
                    this.parent_obj.fetchData();
                }
                this.closeDialog();
                return true;
            } else {
                this.$message({
                    type: 'error',
                    message: this.$t('renameFail'),
                });
                return false;
            }
            } catch (error) {
                parseBackendError(this, error);
                return false;
            }
        },
        async doSave() {
            if (this.form.etype === 'file' && this.base_title !== this.form.title) {
                const baseExt = this.file_path.split('.').pop();
                const newExt = this.form.title.split('.').pop();
                if (baseExt !== newExt) {
                    this.form.title = this.form.title + '.' + baseExt;
                }
                const ret = await this.realRename(this.form.title);
                if (!ret) {
                    ELMessage.error(this.$t('renameFail'));
                    return;
                }
            }
            const success = await this.$refs.typeSelector.realSave();
            if (success) {
                this.closeDialog();
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
        viewContent() {
            this.closeDialog();
            console.log(this.$t('view', { idx: this.form.idx }));
            // window.open(`${window.location.origin}/view_markdown?idx=${this.form.idx}`, '_blank');
            window.location.href = `${window.location.origin}/view_markdown?idx=${this.form.idx}`;
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
                        this.closeDialog();
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