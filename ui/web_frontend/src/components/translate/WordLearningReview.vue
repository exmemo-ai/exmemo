<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.reviewWords') }}</h1>
            <div class="translate-counter">
                {{ $t('trans.remainToReview', { count: getShowListLength() }) }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div v-if="getShowListLength() > 0" class="translate-word-display">
                <p>{{ $t('trans.word') }}: {{ wordStr }}</p>
                <p v-if="showTranslation >= 1">
                    {{ $t('trans.exampleSentence') }}: {{ sentence }}
                </p>
                <p v-if="showTranslation === 2">
                    {{ $t('trans.wordTranslation') }}: {{ transStr }}
                </p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="toggleTranslation">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="markAsLearned">{{ $t('trans.markAsKnown') }}</el-button>
                <el-button @click="markAsReview">{{ $t('trans.todayLearned') }}</el-button>
                <el-button @click="learnMore">{{ $t('trans.learnMore') }}</el-button>
            </div>            
        </div>
    </div>
</template>

<script>
import { fetchWordList, realUpdate } from './WordLearningSupport';

export default {
    data() {
        return {
            wordStr: '',
            transStr: '',
            sentence: '',
            wordList: [],
            currentIndex: 0,
            showTranslation: 0,
            finishCount: 0,
            needSave: false,
        };
    },
    methods: {
        toggleTranslation() {
            this.showTranslation += 1;
            if (this.showTranslation > 2) {
                this.showTranslation = 0;
            }
        },
        addReviewTimes() {
            const showList = this.getShowList();
            if ('learn_times' in showList[this.currentIndex].info) {
                showList[this.currentIndex].info['learn_times'] += 1;
            } else {
                showList[this.currentIndex].info['learn_times'] = 1;
            }
        },
        markAsReview() {
            this.addReviewTimes();
            const showList = this.getShowList();
            showList[this.currentIndex].info['last_review_time'] = new Date().toISOString();
            this.needSave = true;
            this.nextWord()
        },
        markAsLearned() {
            this.addReviewTimes();
            const showList = this.getShowList();
            showList[this.currentIndex].status = 'learned';
            this.needSave = true;
            this.nextWord()
        },
        learnMore() {
            this.addReviewTimes();
            this.nextWord()
        },
        getShowListLength() {
            return this.getShowList().length;
        },
        getShowList() {
            const today = new Date().toDateString();
            const showList = this.wordList.filter(word => {
                const lastReviewTime = word.info.last_review_time ? new Date(word.info.last_review_time).toDateString() : null;
                return lastReviewTime !== today && word.status === 'review';
            });
            return showList
        },
        nextWord() {
            if (this.getShowListLength() === 0) {
                this.save(true);
                return;
            }
            const showList = this.getShowList();
            this.currentIndex = (this.currentIndex + 1) % showList.length;
            this.showTranslation = 0
            this.updateWordDisplay();
            //this.save(false);
        },
        updateWordDisplay() {
            const showList = this.getShowList();
            if (this.currentIndex < showList.length) {
                const item = showList[this.currentIndex]
                this.wordStr = item.word;
                this.transStr = item.info.translate;
                if ("examples" in item.info && item.info.examples.length > 0) {
                    this.sentence = item.info.examples[0].sentence;
                } else {
                    this.sentence = '';
                }
                this.updateCount();
            }
        },
        updateCount() {
            return this.currentIndex + 1;
        },
        async save(nextStep = true) {
            if (this.needSave) {
                await realUpdate(this.wordList);
                this.needSave = false;
            }
            if (nextStep) {
                this.$emit('update-status', 'review');
            }
        },
        async fetch() {
            this.wordList = []
            let tmpList = await fetchWordList('review');
            for (let i = 0; i < tmpList.length; i++) {
                if (tmpList[i].info === null) {
                    tmpList[i].info = {};
                }
                this.wordList.push(tmpList[i]);
            }
            this.wordList = [...this.wordList].sort((a, b) => {
                return new Date(b.updated_time) - new Date(a.updated_time);
            });
            this.updateWordDisplay();
        },     
    },
    mounted() {
        this.fetch();
    },
    expose: ['save'],
};
</script>

<style scoped>
</style>