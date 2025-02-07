<template>
    <el-dialog v-model="dialogVisible" :title="$t('edit')" width="60%">
        <div class="info-block">
            <p><span class="label">{{ $t('trans.word') }}:</span> {{ editForm.word }}</p>
            <p><span class="label">{{ $t('trans.phonetic') }}:</span> {{ editForm.info.base?.phonetic }}</p>
            <p><span class="label">{{ $t('trans.meaning') }}:</span> {{ editForm.meaning }}</p>
            <p><span class="label">{{ $t('frequency') }}:</span> {{ editForm.freq }}</p>
            <p><span class="label">{{ $t('trans.wfrom') }}:</span> {{ editForm.info.base?.from_list?.join(', ') }}</p>
            <p><span class="label">{{ $t('recordCount') }}:</span> {{ editForm.times }}</p>
            <p><span class="label">{{ $t('trans.learnTimes') }}:</span> {{ editForm.info?.opt?.learn_times }}</p>
            <p><span class="label">{{ $t('trans.learnDate') }}:</span> {{ formatDate(editForm.info?.opt?.learn_date) }}</p>
            <p><span class="label">{{ $t('trans.reviewTimes') }}:</span> {{ editForm.info?.opt?.review_times }}</p>
            <p><span class="label">{{ $t('trans.lastReviewTime') }}:</span> {{ formatDate(editForm.info?.opt?.last_review_time) }}</p>
        </div>
        
        <el-form :model="editForm">
            <el-form-item :label="$t('status')">
                <el-select v-model="editForm.status" style="width: 100%">
                    <el-option :label="$t('trans.not_learned')" value="not_learned"/>
                    <el-option :label="$t('trans.learned')" value="learned"/>
                    <el-option :label="$t('trans.learning')" value="learning"/>
                    <el-option :label="$t('trans.reviewing')" value="reviewing"/>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="removeItem">{{ $t('delete') }}</el-button>
                <el-button @click="dialogVisible = false">{{ $t('cancel') }}</el-button>
                <el-button type="primary" @click="save">{{ $t('save') }}</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import { realUpdate } from './WordLearningSupport';
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn';

export default {
    name: 'WordEditor',
    data() {
        return {
            dialogVisible: false,
            editForm: {
                idx: null,
                word: '',
                status: '',
                freq: 0,
                meaning: '',
                times: 0,
                info: {
                    opt: {
                        last_review_time: null,
                        learn_date: null,
                        learn_times: 0,
                        review_times: 0
                    }
                },
                base: {
                    from_list: [],
                    phonetic: ''
                }
            }
        }
    },
    methods: {
        formatDate(timestamp) {
            console.log('timestamp', timestamp)
            if (!timestamp) return this.$t('trans.null');
            return new Date(timestamp).toLocaleDateString();
        },
        openDialog(word) {
            this.editForm = { ...word };
            this.editForm.info.base.from_list = this.editForm.info.base.from_list.map(item => this.$t(`trans.${item}`));
            this.dialogVisible = true;
        },
        async save() {
            try {
                await realUpdate([this.editForm]);
                this.dialogVisible = false;
                this.$emit('update');
                this.$message.success(this.$t('updateSuccess'));
            } catch (error) {
                this.$message.error(this.$t('updateFailed'));
            }
        },
        async removeItem() {
            let func = 'api/translate/word/' + this.editForm.idx + '/';
            axios.delete(getURL() + func)
                .then(response => {
                    console.log('delete success', response.data);
                    this.dialogVisible = false;
                    this.$emit('update');
                })
                .catch(error => {
                    parseBackendError(this, error);
                });
        }
    }
}
</script>

<style scoped>
.info-block {
    margin-bottom: 1rem;
}
.info-block p {
    margin: 0.5rem 0;
}
.label {
    font-weight: bold;
    margin-right: 0.5rem;
}
</style>
