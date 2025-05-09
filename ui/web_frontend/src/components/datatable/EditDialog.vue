<template>
    <el-dialog v-model="dialogVisible" :title="$t('edit')" :width="dialogWidth"
        :before-close="handleClose">
        <template #header>
            <div class="dialog-header">
                <div class="dialog-title">
                    <strong>
                        <template v-if="form.etype === 'file'">{{ $t('file') }}</template>
                        <template v-if="form.etype === 'record'">{{ $t('record') }}</template>
                        <template v-if="form.etype === 'web'">{{ $t('web') }}</template>
                        <template v-if="form.etype === 'note'">{{ $t('note') }}</template>
                        <template v-if="form.etype === 'chat'">{{ $t('chat') }}</template>
                    </strong>
                </div>
                <div class="action-buttons">
                    <el-button size="small" @click="doSave" :title="$t('save')">
                        <el-icon><SaveIcon /></el-icon>
                    </el-button>
                    <el-button size="small" @click="showDeleteConfirmation" :title="$t('delete')">
                        <el-icon><Delete /></el-icon>
                    </el-button>
                    <el-button v-if="form.etype !== 'record'" size="small" @click="viewContent" :title="$t('view')">
                        <el-icon><View /></el-icon>
                    </el-button>
                    <el-button v-if="(form.etype === 'note' && file_path && file_path.toLowerCase().endsWith('.md'))" 
                              size="small" @click="editNote" :title="$t('edit')">
                        <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button v-if="form.etype === 'file' || form.etype === 'note'" size="small" @click="download" :title="$t('download')">
                        <el-icon><Download /></el-icon>
                    </el-button>
                </div>
            </div>
        </template>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <div width="100%">
                        <a :href="form.addr" target="_blank"
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
                    <el-input type="textarea" :rows="6" v-model="form.content" :placeholder="$t('recordContent')"></el-input>
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
            :onSuccess="onSuccess"
        />
        <span class="dialog-footer">
        </span>
    </el-dialog>
</template>
  
<script>
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn'
import DataEditor from './DataEditor.vue'
import { downloadFile, fetchItem } from './dataUtils'
import { Delete, Edit, View, Download } from '@element-plus/icons-vue'
import SaveIcon from '@/components/icons/SaveIcon.vue'


export default {
    components: {
        DataEditor,
        Delete,
        Edit,
        View,
        Download,
        SaveIcon
    },
    data() {
        return {
            dialogWidth: '60%',
            isMobile: false,
            parent_obj: null,
            file_path: null,
            file: null,
            dialogVisible: false,
            record_content: '',
            form: {
                idx: null,
                title: '',
                raw: '',
                content: '',
                ctype: '',
                etype: 'record',
                atype: '',
                level: '-1',
                status: '',
                addr: '',
            },
            onSuccess: null,
        };
    },
    methods: {
        async openDialog(onSuccess, row) {
            this.onSuccess = onSuccess;
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

            if (this.form.etype === 'record') {
                const result = await fetchItem(this.form.idx);
                if (result.success && result.data.content) {
                    this.form.content = result.data.content;
                }
            }

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
                this.onSuccess?.(response.data);
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
                parseBackendError(error);
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
                    return;
                }
            }
            const success = await this.$refs.typeSelector.realSave();
            if (success) {
                this.closeDialog();
            }
        },
        download() {
            console.log(this.$t('download', { idx: this.form.idx }));
            let filename = this.file_path.split('/').pop();
            downloadFile(this.form.idx, filename);
        },
        viewContent() {
            this.closeDialog();
            console.log(this.$t('view', { idx: this.form.idx }));
            window.open(`${window.location.origin}/view_markdown?idx=${this.form.idx}`, '_blank');
            //window.location.href = `${window.location.origin}/view_markdown?idx=${this.form.idx}`;
        },
        editNote() {
            this.closeDialog();
            window.open(`${window.location.origin}/edit_markdown?idx=${this.form.idx}`, '_blank');
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
                        this.onSuccess?.(response.data);
                    } else {
                        this.$message({
                            type: 'error',
                            message: this.$t('deleteFail')
                        });
                    }
                })
                .catch(error => {
                    parseBackendError(error);
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

<style scoped>
.dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.dialog-title {
    font-size: 18px;
}

.action-buttons {
    display: flex;
    gap: 10px;
}

.action-buttons .el-button {
    margin: 0;
    padding: 0 5px;
}
</style>