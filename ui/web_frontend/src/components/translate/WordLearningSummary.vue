<template>
    <div>
        <div class="translate-common-style">
            <div style="font-size: 14px; margin-top: 10px;">
                <pre>{{ summaryStr }}</pre>
            </div>
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