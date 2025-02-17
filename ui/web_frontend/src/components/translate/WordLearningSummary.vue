<template>
    <div>
        <div class="summary-container">
            <div style="font-size: 14px; margin-top: 10px;">
                <pre>{{ summaryStr }}</pre>
            </div>
            <div id="learnChart" style="width: 100%; height: 300px;"></div>
            <div id="reviewChart" style="width: 100%; height: 300px;"></div>
        </div>
    </div>
</template>

<script>
import { getSummary } from './WordLearningSupport';
import * as echarts from 'echarts';

export default {
    data() {
        return {
            summaryStr: '',
            learnData: null,
            reviewData: null,
            learnChart: null,
            reviewChart: null,
        };
    },
    methods: {
        async fetch() {
            const [summary, learnData, reviewData] = await getSummary();
            this.summaryStr = summary;
            this.learnData = learnData;
            this.reviewData = reviewData;
            this.updateCharts();
        },
        initCharts() {
            this.learnChart = echarts.init(document.getElementById('learnChart'));
            this.reviewChart = echarts.init(document.getElementById('reviewChart'));
        },
        updateCharts() {
            if (!this.learnData || !this.learnChart || !this.reviewData || !this.reviewChart) return;

            const learnDates = Object.keys(this.learnData).sort();
            const learnValues = learnDates.map(date => this.learnData[date]);
            
            const learnOption = {
                title: {
                    text: this.$t('trans.learnWordCount'),
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: learnDates,
                    axisLabel: {
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    name: this.$t('trans.wordCount'),
                },
                series: [{
                    data: learnValues,
                    type: 'bar',
                    smooth: true
                }]
            };

            const reviewDates = Object.keys(this.reviewData).sort();
            const reviewValues = reviewDates.map(date => this.reviewData[date]);

            const reviewOption = {
                title: {
                    text: this.$t('trans.reviewWordCount'),
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: reviewDates,
                    axisLabel: {
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    name: this.$t('trans.wordCount'),
                },
                series: [{
                    data: reviewValues,
                    type: 'bar',
                    smooth: true,
                    itemStyle: {
                        color: '#91cc75'
                    }
                }]
            };

            this.learnChart.setOption(learnOption);
            this.reviewChart.setOption(reviewOption);
        }
    },
    mounted() {
        this.initCharts();
        this.fetch();
    },
    beforeDestroy() {
        if (this.learnChart) {
            this.learnChart.dispose();
        }
        if (this.reviewChart) {
            this.reviewChart.dispose();
        }
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

.summary-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    gap: 20px;
}
</style>