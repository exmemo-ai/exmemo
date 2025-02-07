<template>
    <el-dialog class="my-dialog" v-model="dialogVisible" :title="$t('trans.processWordList')" :width="dialogWidth"
        :before-close="handleClose">
        <div style="display: flex; flex-direction: column; height: 100%;">
            <el-select v-model="selectedWordList" :placeholder="$t('trans.selectWordListPlaceholder')" style="width: 100%;">
                <el-option :label="$t('trans.JHSW_1600')" value="JHSW_1600"></el-option>
                <el-option :label="$t('trans.HSW_3500')" value="HSW_3500"></el-option>
                <el-option :label="$t('trans.BASE_500')" value="BASE_500"></el-option>
                <el-option :label="$t('trans.BASE_1000')" value="BASE_1000"></el-option>
                <el-option :label="$t('trans.BASE_2000')" value="BASE_2000"></el-option>
                <el-option :label="$t('trans.BASE_5000')" value="BASE_5000"></el-option>
            </el-select>
            <button @click="handleReq">{{ $t('trans.importWordList') }}</button>
            <el-select v-model="deleteOption" :placeholder="$t('trans.selectDeleteOption')" style="width: 100%; margin-top: 10px;">
                <el-option :label="$t('trans.deleteLearnedWords')" value="learned"></el-option>
                <el-option :label="$t('trans.deleteUnlearnedWords')" value="not_learned"></el-option>
                <el-option :label="$t('trans.deleteAllWords')" value="all"></el-option>
            </el-select>
            <button @click="handleDelete">{{ $t('trans.deleteWordList') }}</button>
        </div>
    </el-dialog>
</template>

<script>
import { importWordList, deleteWordList } from '@/components/translate/TransFunction';
import { ElMessage } from 'element-plus';

export default {
    data() {
        return {
            dialogVisible: false,
            dialogWidth: '80%',
            selectedWordList: 'JHSW_1600',
            parent_obj: null,
            deleteOption: 'all'
        }
    },
    methods: {
        openDialog(parent_obj) {
            this.dialogVisible = true;
            this.parent_obj = parent_obj;
        },
        handleClose(done) {
            this.dialogVisible = false;
            done();
        },
        async handleReq() {
            try {
                await importWordList(this.parent_obj, this.selectedWordList, (info) => {
                    ElMessage.success(this.$t('trans.importSuccess'));
                    this.parent_obj.fetchData();
                });
                this.dialogVisible = false;
            } catch (error) {
                console.error(error);
            }
        },
        async handleDelete() {
            try {
                await deleteWordList(this.parent_obj, this.deleteOption, (info) => {
                    ElMessage.success(this.$t('trans.deleteSuccess'));
                    this.parent_obj.fetchData();
                });
                this.dialogVisible = false;
            } catch (error) {
                console.error(error);
            }
        }
    }
}
</script>

<style scoped>
.my-dialog .el-dialog__body {
    height: 50%;
}
</style>
