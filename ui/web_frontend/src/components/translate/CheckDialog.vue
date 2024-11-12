<template>
    <el-dialog class="my-dialog" v-model="dialogVisible" :title="$t('searchWord')" :width="dialogWidth"
        :before-close="handleClose">
        <div style="display: flex; flex-direction: column; height: 100%;">
            <label>{{ $t('inputEnglish') }}</label>
            <el-input v-model="inputText" type="textarea" :rows="2" :placeholder="$t('placeholderInputWord')"
                style="width: 100%;" @keyup.enter="handleReq" @keydown.enter.prevent></el-input>
            <button @click="handleReq">{{ $t('searchDictionary') }}</button>
            <div style="height: 200px; overflow-y: auto; text-align: left; white-space: pre-line;">
                {{ txtAnswer }}
            </div>
        </div>
    </el-dialog>
</template>

<script>
import { translateFunc } from './TransFunction';
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
        translateCallback(info) {
            this.txtAnswer = info
        },
        handleReq(event) {
            if (event) event.preventDefault();
            translateFunc(this, 'word', this.inputText, null, this.translateCallback);
        }
    }
}
</script>

<style scoped>
.my-dialog .el-dialog__body {
    height: 50%;
}
</style>