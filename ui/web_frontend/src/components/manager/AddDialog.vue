<template>
    <el-dialog v-model="dialogVisible" :title="$t('new')" :width="dialogWidth"
        :before-close="handleClose">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
            <div style="display: flex; align-items: center; gap: 10px">
            <div>
                <input type="radio" id="upload" value="file" v-model="form.etype">
                <label for="upload">{{ $t('uploadFile') }}</label>
            </div>
            <div>
                <input type="radio" id="record" value="record" v-model="form.etype">
                <label for="record">{{ $t('record') }}</label>
            </div>
            <div>
                <input type="radio" id="addWeb" value="web" v-model="form.etype">
                <label for="addWeb">{{ $t('addWeb') }}</label>
            </div>
            </div>
            <el-button size="small" type="primary" @click="doSave">{{ $t('save') }}</el-button>
        </div>

        <div style="display: flex;margin-bottom: 5px;" width="100%">
            <div style="flex: 3;margin-right: 5px;" width="100%">
                <div v-if="form.etype === 'web'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.addr"
                        placeholder="http://"></el-input>
                </div>
                <div v-if="form.etype === 'file' || form.etype === 'note'" width="100%">
                    <div>
                        <input type="file" @change="handleFileUpload" width="100%">
                    </div>
                    <div v-if="saveProgress > 0" style="margin: 10px">
                        <progress :value="saveProgress" max="100">{{ saveProgress }}%</progress>
                        <el-button style="margin: 2px;" @click="cancelUpload">{{ $t('cancel') }}</el-button>
                    </div>
                </div>
                <div v-if="form.etype === 'record'" width="100%">
                    <el-input type="textarea" :rows="6" v-model="form.raw" :placeholder="$t('recordContent')"></el-input>
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
        openDialog(parent_obj) {
            this.saveProgress = 0;
            this.parent_obj = parent_obj;
            this.form.idx = null
            this.form.ctype = ''
            this.form.etype = 'record'
            this.form.title = ''
            this.form.atype = ''
            this.form.raw = ''
            this.form.status = ''
            this.form.addr = ''
            console.log(this.form)
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
        async doSave() {
            console.log("doSave");
            const success = await this.$refs.typeSelector.realSave();
            if (success) {
                this.closeDialog();
            }
        },
        handleFileUpload(event) {
            this.file_path = event.target.files[0].name;
            this.file = event.target.files[0];
        },
        cancelUpload() {
            if (this.cancelTokenSource) {
                this.cancelTokenSource.cancel('cancel by user');
                this.uploadProgress = 0;
            }
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