<template>
    <div>
        <div class="translate-header">
            <div class="translate-counter">
                {{ $t('trans.remainToReview', { count: getShowListLength() }) }}
            </div>
        </div>
        <div class="translate-common-style">
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
                <el-button @click="setHint">{{ $t('trans.showHint') }}</el-button>
                <el-button @click="markAsLearned">{{ $t('trans.markAsKnown') }}</el-button>
                <el-button @click="markAsReview">{{ $t('trans.todayLearned') }}</el-button>
                <el-button @click="learnMore">{{ $t('trans.learnMore') }}</el-button>
            </div>            
        </div>
    </div>
</template>

<script>
import { fetchWordList, realUpdate, getExamples, getMeaning } from './WordLearningSupport';

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
        setHint() {
            this.showTranslation += 1;
            if (this.showTranslation > 2) {
                this.showTranslation = 0;
            }
        },
        addReviewTimes() {
            const showList = this.getShowList();
            if (showList[this.currentIndex].info.opt == undefined) {
                showList[this.currentIndex].info.opt = {}
            }
            if ('review_times' in showList[this.currentIndex].info.opt) {
                showList[this.currentIndex].info.opt['review_times'] += 1;
            } else {
                showList[this.currentIndex].info.opt['review_times'] = 1;
            }
            if (showList[this.currentIndex].info.opt['review_date_list'] == undefined) {
                showList[this.currentIndex].info.opt['review_date_list'] = []
            }
            showList[this.currentIndex].info.opt['review_date_list'].push(new Date().toISOString());
        },
        markAsReview() {
            const showList = this.getShowList();
            if (showList.length === 0) {
                return;
            }
            this.addReviewTimes();
            if (showList[this.currentIndex].info.opt == undefined) {
                showList[this.currentIndex].info.opt = {}
            }
            showList[this.currentIndex].info.opt['last_review_time'] = new Date().toISOString();
            this.needSave = true;
            this.nextWord()
        },
        markAsLearned() {
            const showList = this.getShowList();
            if (showList.length === 0) {
                return;
            }
            this.addReviewTimes();
            showList[this.currentIndex].status = 'learned';
            this.needSave = true;
            this.nextWord()
        },
        learnMore() {
            const showList = this.getShowList();
            if (showList.length === 0) {
                return;
            }
            this.addReviewTimes();
            this.nextWord()
        },
        getShowListLength() {
            return this.getShowList().length;
        },
        getShowList() {
            const today = new Date().toDateString();
            const showList = this.wordList.filter(word => {
                let lastReviewTime = null;
                if (word.info && word.info.opt && word.info.opt.last_review_time) {
                    lastReviewTime = new Date(word.info.opt.last_review_time).toDateString();
                } else if (word.info && word.info.last_review_time) {
                    lastReviewTime = new Date(word.info.last_review_time).toDateString();
                }
                return lastReviewTime !== today && word.status === 'review';
            });
            return showList
        },
        async nextWord() {
            if (this.getShowListLength() === 0) {
                this.save(true);
                return;
            }
            const showList = this.getShowList();
            this.currentIndex = (this.currentIndex + 1) % showList.length;
            this.showTranslation = 0
            await this.updateWordDisplay();
            //this.save(false);
        },
        async updateWordDisplay() {
            const showList = this.getShowList();
            if (this.currentIndex < showList.length) {
                const item = showList[this.currentIndex]
                this.wordStr = item.word;
                this.transStr = await getMeaning(item.info);
                if (item.info.base && item.info.base.example_list && item.info.base.example_list.length > 0) {
                    this.sentence = item.info.base.example_list[0].sentence;
                } else {
                    const data = await getExamples(item.word);
                    if (data && 'examples' in data && data.word === item.word && data.examples.length > 0) {
                        this.sentence = data.examples[0].sentence;
                        if (item.info.base == undefined) {
                            item.info.base = {}
                        }
                        item.info.base.example_list = data.examples;
                    }
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
                this.$emit('update-status', 'summary');
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
            await this.updateWordDisplay();
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