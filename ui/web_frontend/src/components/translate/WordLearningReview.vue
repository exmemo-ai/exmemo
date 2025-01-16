<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.reviewWords') }}</h1>
            <div class="translate-counter">
                {{ finishCount }} / {{ wordList.length }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div v-if="wordList.length > 0" class="translate-word-display">
                <bold>{{ $t('trans.word') }}: {{ wordStr }}</bold>
                <p>{{ $t('trans.exampleSentence') }}: {{ sentence }}</p>
                <p v-if="showTranslation">{{ $t('trans.wordTranslation') }}: {{ transStr }}</p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="toggleTranslation">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="markAsLearned">{{ $t('trans.markAsKnown') }}</el-button>
                <el-button @click="markAsReview">{{ $t('trans.todayLearned') }}</el-button>
                <el-button @click="learnMore">{{ $t('trans.learnMore') }}</el-button>
                <el-button @click="save">{{ $t('save') }}</el-button>
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
            finishCount: 0,
            showTranslation: false,
        };
    },
    methods: {
        toggleTranslation() {
            this.showTranslation = !this.showTranslation;
        },
        markAsReview() {
            this.wordList[this.currentIndex]['flag'] = true;
            this.nextWord()
        },
        markAsLearned() {
            this.wordList[this.currentIndex]['item'].status = 'learned';
            this.nextWord()
        },
        learnMore() {
            this.nextWord()
        },
        nextWord() {
            const startIndex = this.currentIndex;
            do {
                this.currentIndex = (this.currentIndex + 1) % this.wordList.length;
                if (this.wordList[this.currentIndex].flag !== true && this.wordList[this.currentIndex].item.status !== 'learned') {
                    this.updateWordDisplay();
                    this.showTranslation = false;
                    return;
                }
            } while (this.currentIndex !== startIndex);
            this.save();
        },
        updateWordDisplay() {
            if (this.currentIndex < this.wordList.length) {
                const item = this.wordList[this.currentIndex]['item']
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
            this.finishCount = this.wordList.filter(word => word['flag'] === true).length;
        },
        save() {
            let tmpList = []
            for (let i = 0; i < this.wordList.length; i++) {
                tmpList.push(this.wordList[i]['item']);
            }
            realUpdate(tmpList);
            this.$emit('update-status', 'write');
        },
        async fetch() {
            this.wordList = []
            let tmpList = await fetchWordList('review');
            for (let i = 0; i < tmpList.length; i++) {
                this.wordList.push({'item':tmpList[i], 'flag':false});
            }
            this.wordList.sort((a, b) => {
                return b.item.created_time - a.item.created_time;
            });
            this.updateWordDisplay();
        },     
    },
    mounted() {
        this.fetch();
    }
};
</script>

<style scoped>
</style>