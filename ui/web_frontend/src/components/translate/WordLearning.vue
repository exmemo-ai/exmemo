<template>
    <div>
        <component :is="currentComponent" 
                   @update-status="updateStatus"
                   ></component>
    </div>
</template>

<script>
import WordLearningSelect from './WordLearningSelect.vue';
import WordLearningReview from './WordLearningReview.vue';
import WordLearningLearn from './WordLearningLearn.vue';

export default {
    data() {
        return {
            status: 'select', // 'select', 'review', 'learn'
        };
    },
    computed: {
        currentComponent() {
            switch (this.status) {
                case 'review':
                    return WordLearningReview;
                case 'learn':
                    return WordLearningLearn;
                default:
                    return WordLearningSelect;
            }
        }
    },
    methods: {
        updateStatus(newStatus) {
            this.status = newStatus;
        },
    }
};
</script>

<style scoped>
</style>
