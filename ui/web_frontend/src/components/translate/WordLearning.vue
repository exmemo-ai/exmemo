<template>
    <div>
        <div class="top-button">
            <el-button :type="selectType" @click="handleSelectClick">{{$t('trans.selectWord')}}</el-button>
            <el-button :type="learnType" @click="handleLearnClick">{{ $t('trans.wordLearning') }}</el-button>
            <el-button :type="reviewType" @click="handleReviewClick">{{ $t('trans.reviewWords') }}</el-button>
            <el-button :type="writeType" @click="handleWriteClick">{{ $t('trans.writeFromMemory') }}</el-button>
            <el-button :type="summaryType" @click="handleSummaryClick">{{ $t('trans.summary') }}</el-button>
        </div>
        <component :is="currentComponent" 
                   @update-status="updateStatus"
                   ></component>
    </div>
</template>

<script>
import WordLearningSelect from './WordLearningSelect.vue';
import WordLearningReview from './WordLearningReview.vue';
import WordLearningLearn from './WordLearningLearn.vue';
import WordLearningWrite from './WordLearningWrite.vue';
import WordLearningSummary from './WordLearningSummary.vue';

export default {
    data() {
        return {
            status: 'select', // 'select', 'review', 'learn', 'write'
        };
    },
    computed: {
        currentComponent() {
            switch (this.status) {
                case 'review':
                    return WordLearningReview;
                case 'learn':
                    return WordLearningLearn;
                case 'write':
                    return WordLearningWrite;
                case 'summary':
                    return WordLearningSummary;
                default:
                    return WordLearningSelect;
            }
        },
        selectType() {
            return this.status === 'select' ? 'primary' : '';
        },
        learnType() {
            return this.status === 'learn' ? 'primary' : '';
        },
        reviewType() {
            return this.status === 'review' ? 'primary' : '';
        },
        writeType() {
            return this.status === 'write' ? 'primary' : '';
        },
        summaryType() {
            return this.status === 'summary' ? 'primary' : '';
        }
    },
    methods: {
        updateStatus(newStatus) {
            this.status = newStatus;
        },
        handleSelectClick() {
            this.status = 'select';
        },
        handleLearnClick() {
            this.status = 'learn';
        },
        handleReviewClick() {
            this.status = 'review';
        },
        handleWriteClick() {
            this.status = 'write';
        },
        handleSummaryClick() {
            this.status = 'summary';
        }
    }
};
</script>

<style scoped>
.top-button {
    top: 20px;
    right: 20px;
}
</style>
