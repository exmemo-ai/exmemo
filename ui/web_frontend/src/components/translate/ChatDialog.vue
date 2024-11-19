<template>
    <el-dialog class="my-dialog" v-model="dialogVisible" :title="$t('intelligentAnalysis')" :width="dialogWidth"
        :before-close="handleClose">
        <div style="display: flex; flex-direction: column; height: 100%;">
            <label>{{ $t('inputQuestion') }}</label>
            <el-input v-model="inputText" type="textarea" :rows="2" :placeholder="$t('placeholderInputQuestion')"
                style="width: 100%;"></el-input>
            <button @click="handleReq">{{ $t('ask') }}</button>
            <div style="height: 200px; overflow-y: auto;">
                {{ txtAnswer }}
            </div>
        </div>
    </el-dialog>
</template>

<script>
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn';
export default {
    data() {
        return {
            dialogVisible: false,
            dialogWidth: '80%',
            inputText: '',
            txtAnswer: '',
            parent_obj: null
        }
    },
    methods: {
        openDialog(parent_obj) {
            console.log(parent_obj)
            this.dialogVisible = true;
            this.parent_obj = parent_obj;
            this.txtAnswer = parent_obj.inputText;
        },
        handleClose(done) {
            this.dialogVisible = false;
            done();
        },
        handleReq() {
            let func = 'api/translate/assistant';
            const formData = new FormData();
            if (this.inputText !== null) {
                formData.append('prompt', this.inputText);
            }
            if (this.parent_obj.inputText !== null) {
                formData.append('content', this.parent_obj.inputText);
            }
            console.log('formData:', formData);
            axios.post(getURL() + func, formData).then((res) => {
                console.log(res.data);
                if (res.data.status == 'success') {
                    this.txtAnswer = res.data.info
                } else {
                    alert(res.data.info);
                }
            }).catch((err) => {
                parseBackendError(this, err);
            });
        }
    }
}
</script>

<style scoped>
.my-dialog .el-dialog__body {
    height: 50%;
}
</style>