<template>
    <el-dialog v-model="dialogVisible" :title="$t('new')" :width="dialogWidth"
        :before-close="handleClose">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
            <div style="display: flex; align-items: center; gap: 10px">
                <el-radio-group v-model="form.etype" :disabled="!!force_etype">
                    <el-radio id="upload" value="file" :disabled="!!force_etype">{{ $t('uploadFile') }}</el-radio>
                    <el-radio id="record" value="record" :disabled="!!force_etype">{{ $t('record') }}</el-radio>
                    <el-radio id="addWeb" value="web" :disabled="!!force_etype">{{ $t('addWeb') }}</el-radio>
                    <el-radio id="note" value="note" :disabled="!!force_etype">{{ $t('note') }}</el-radio>
                </el-radio-group>
            </div>
            <el-button size="small" type="primary" @click="doSave">{{ $t('save') }}</el-button>
        </div>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.addr"
                        placeholder="http://"></el-input>
                </div>
                <div v-if="form.etype === 'file'" width="100%">
                    <input type="file" @change="handleFileUpload" width="100%">
                </div>
                <div v-if="form.etype === 'record'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.raw" :placeholder="$t('recordContent')"></el-input>
                </div>
                <div v-if="form.etype === 'note'" width="100%" style="display: flex; gap: 5px; flex-direction: column;">
                    <div class="form-row">
                        <div class="label-container">
                            <el-text>{{ $t('opt.vault') }}</el-text>
                        </div>
                        <div class="content-container">
                            <el-input type="text" v-model="input_vault"></el-input>
                        </div>
                    </div>  
                    <div class="form-row">
                        <div class="label-container">
                            <el-text>{{ $t('opt.path') }}</el-text>
                        </div>
                        <div class="content-container">
                            <el-input type="text" v-model="input_path"></el-input>
                        </div>
                    </div>
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
    </el-dialog>
</template>


<script>
import { ElMessage } from 'element-plus';
import DataEditor from './DataEditor.vue'
import SettingService from '@/components/settings/settingService'
import { confirmOpenNote } from './dataUtils';

export default {
    components: {
        DataEditor
    },
    data() {
        return {
            dialogWidth: '60%',
            isMobile: false,
            onSuccess: null,
            input_vault: null,
            input_path: null,
            file_path: null,
            file: null,
            dialogVisible: false,
            force_etype: null,
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
        openDialog(onSuccess, options = {}) {
            this.onSuccess = onSuccess;
            this.dialogVisible = true;
            this.saveProgress = 0;
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
            this.form.ctype = options?.ctype ?? '';
            this.form.atype = options?.atype ?? '';
            this.form.status = options?.status ?? '';
            this.form.idx = null;
            this.form.title = this.calcTitle(this.input_path);
            this.form.addr = '';
            this.form.raw = ''
            this.calcFilePath();
            console.log(this.form)
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
            const normalizedPath = this.normalizePath(this.input_path);
            this.file_path = this.input_vault + '/' + normalizedPath;
        },
        async doSave() {
            console.log("doSave");
            if (this.form.etype === 'note') {
                if (this.input_vault && this.input_path) {
                    this.calcFilePath();
                } else {
                    ElMessage.error(this.$t('opt.needVaultPath'));
                    return;
                }
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
        handleFileUpload(event) {
            this.file_path = event.target.files[0].name;
            this.file = event.target.files[0];
            this.form.title = this.calcTitle(this.file_path)
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
</style>