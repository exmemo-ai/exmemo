<template>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" :width="dialogWidth"
        :before-close="handleClose">
        <template #header>
            <div class="dialog-header">
                <span class="dialog-title">{{ dialogTitle }}</span>
                <div class="action-buttons">
                    <el-button size="small" type="primary" @click="doSave">
                        <el-icon><SaveIcon /></el-icon>
                    </el-button>
                </div>
            </div>
        </template>

        <div style="display: flex; align-items: center; margin-bottom: 10px">
            <el-radio-group v-model="form.etype" :disabled="!!force_etype">
                <el-radio id="upload" value="file" :disabled="!!force_etype">{{ $t('uploadFile') }}</el-radio>
                <el-radio id="record" value="record" :disabled="!!force_etype">{{ $t('record') }}</el-radio>
                <el-radio id="addWeb" value="web" :disabled="!!force_etype">{{ $t('addWeb') }}</el-radio>
                <el-radio id="note" value="note" :disabled="!!force_etype">{{ $t('note') }}</el-radio>
            </el-radio-group>
        </div>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.addr"
                        placeholder="http://"></el-input>
                </div>
                <div v-if="form.etype === 'file'" width="100%" style="display: flex; gap: 5px; flex-direction: column;">
                    <input type="file" ref="fileInput" @change="handleFileUpload" width="100%">
                    <PathSelector
                        v-model:path="file_input_path"
                        :etype="form.etype"
                    />
                </div>
                <div v-if="form.etype === 'record'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.content" :placeholder="$t('recordContent')"></el-input>
                </div>
                <div v-if="form.etype === 'note'" width="100%" style="display: flex; gap: 5px; flex-direction: column;">
                    <PathSelector
                        v-model:vault="input_vault"
                        v-model:path="input_path"
                        :etype="form.etype"
                    />
                </div>
            </div>
        </div>

        <hr style="margin: 10px 0;">
        <DataEditor 
            ref="dataEditor"
            :form="form"
            :file_path="file_path"
            :file="file"
            :onSuccess="onSuccess"
        />
        <span class="dialog-footer">
        </span>
        <UnzipDialog ref="unzipDialog" />
    </el-dialog>
</template>


<script>
import { ElMessage } from 'element-plus';
import DataEditor from './DataEditor.vue'
import SettingService from '@/components/settings/settingService'
import { confirmOpenNote } from './dataUtils';
import SaveIcon from '@/components/icons/SaveIcon.vue'
import UnzipDialog from './UnzipDialog.vue'
import PathSelector from '@/components/common/PathSelector.vue'

export default {
    components: {
        DataEditor,
        SaveIcon,
        UnzipDialog,
        PathSelector,
    },
    data() {
        return {
            dialogWidth: '60%',
            dialogTitle: '',
            isMobile: false,
            onSuccess: null,
            input_vault: null,
            input_path: null,
            file_input_path: null,
            file_path: null,
            file: null,
            dialogVisible: false,
            force_etype: null,
            form: {
                idx: null,
                title: '',
                content: '',
                ctype: '',
                etype: 'record',
                atype: '',
                level: '-1',
                status: '',
                addr: '',
            },
        };
    },
    watch: {
        input_path(newPath) {
            if (this.form.etype === 'note') {
                this.form.title = this.calcTitle(newPath);
            }
        }
    },
    methods: {
        async openDialog(onSuccess, options = {}) {
            this.onSuccess = onSuccess;
            this.dialogVisible = true;
            this.dialogTitle = options?.title ?? this.$t('new');
            this.saveProgress = 0;
            if (this.$refs.fileInput) {
                this.$refs.fileInput.value = '';
            }
            this.file = null;
            this.file_path = null;
            this.$refs.dataEditor?.resetProgress();

            if (options && options.etype) {
                this.force_etype = options.etype;
                this.form.etype = this.force_etype;
            } else {
                this.force_etype = null;
                this.form.etype = 'record';
            }
            if (options && options.content) {
                const blob = new Blob([options.content], { type: 'text/plain' });
                this.file = new File([blob], 'temp.md', { type: 'text/plain' });
            }
            this.input_vault = options?.vault ?? null;
            this.input_path = options?.path ?? null;
            this.file_input_path = options?.path ?? null;
            this.form.ctype = options?.ctype ?? '';
            this.form.atype = options?.atype ?? '';
            this.form.status = options?.status ?? '';
            this.form.idx = null;
            this.form.title = this.calcTitle(this.input_path);
            this.form.addr = '';
            this.form.content = '';
            this.calcFilePath();
            console.log(this.form);
        },
        closeDialog() {
            this.dialogVisible = false;
            if (this.$refs.fileInput) {
                this.$refs.fileInput.value = '';
            }
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
        normalizePath(path) {
            if (path) {
                let normalized = path.replace(/\\/g, '/');
                normalized = normalized.replace(/\/+/g, '/');
                normalized = normalized.replace(/^\/+/, '');
                normalized = normalized.replace(/\/+$/, '');
                return normalized;
            } else {
                return path;
            }
        },
        async calcFilePath() {
            if (this.form.etype === 'file') {
                this.file_path = this.normalizePath(this.file_input_path);
            } else {
                const normalizedPath = this.normalizePath(this.input_path);
                this.file_path = this.input_vault + '/' + normalizedPath;
                if (this.form.etype === 'note' && this.file_path && !this.file_path.includes('.')) {
                    this.file_path += '.md';
                }
            }
        },
        async doSave() {
            console.log("doSave");
            if (this.form.etype === 'note') {
                if (this.input_vault && this.input_path && !this.input_path.endsWith('/')) {
                    this.calcFilePath();
                } else {
                    ElMessage.error(this.$t('opt.needVaultPath'));
                    return;
                }
            } else if (this.form.etype === 'file') {
                this.calcFilePath();
            }
            await this.$nextTick();
            const ret = await this.$refs.dataEditor.realSave();
            if (ret) {
                if (this.form.etype === 'note' && this.input_vault && this.input_vault.length > 0) {
                    const settingService = SettingService.getInstance();
                    settingService.loadSetting();
                    settingService.setSetting('default_vault', this.input_vault);
                    settingService.saveSetting();
                }
                this.closeDialog();
                if (this.form.etype === 'note') {
                    confirmOpenNote(ret);
                }
            }
        },
        calcTitle(path) {
            if (path) {
                return path.split('\\').pop().split('/').pop();
            }
            return '';
        },
        async handleFileUpload(event) {
            const uploadedFile = event.target.files[0];
            const fileName = uploadedFile.name;
            const fileExt = fileName.split('.').pop().toLowerCase();

            if (['zip', 'rar'].includes(fileExt)) {
                const result = await this.$refs.unzipDialog.show();
                this.form.unzip = result.unzip;
                this.form.createSubDir = result.createSubDir;
            }
            // later add check file size here

            this.file = uploadedFile;
            if (!this.file_input_path) {
                this.file_input_path = fileName;
            } else {
                const hasFileName = this.file_input_path.split('/').pop().includes('.');
                if (!hasFileName) {
                    this.file_input_path = this.file_input_path.replace(/\/+$/, '') + '/' + fileName;
                } else {
                    this.file_input_path = this.file_input_path.replace(/[^/]+$/, fileName);
                }
            }            
            this.file_path = uploadedFile.name;
            this.form.title = this.calcTitle(this.file_path);
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
@media screen and (max-width: 768px) {
    :deep(.el-radio) {
        margin-right: 10px;
    }
}
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

.dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.dialog-title {
    font-size: 18px;
    font-weight: bold;
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