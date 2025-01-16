<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.summary') }}</h1>
        </div>
        <div class="content word-learning translate-common-style">
            <pre>{{ summaryStr }}</pre>
        </div>
    </div>
</template>

<script>
import { getSummary } from './WordLearningSupport';

export default {
    data() {
        return {
            summaryStr: '',
        };
    },
    methods: {
        async fetch() {
            this.summaryStr = await getSummary();
        },     
    },
    mounted() {
        this.fetch();
    }
};
</script>

<style scoped>
pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 0;
    font-family: inherit;
}
</style>