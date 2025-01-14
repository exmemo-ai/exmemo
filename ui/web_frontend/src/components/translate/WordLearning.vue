<template>
    <div>
        <div class="top-button">
            <el-button @click="handleSelectClick">{{$t('trans.selectWord')}}</el-button>
            <el-button @click="handleLearnClick">{{ $t('trans.wordLearning') }}</el-button>
            <el-button @click="handleReviewClick">{{ $t('trans.reviewWords') }}</el-button>
            <el-button @click="handleWriteClick">{{ $t('trans.writeFromMemory') }}</el-button>
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
                default:
                    return WordLearningSelect;
            }
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
