<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.selectWord') }}</h1>
            <div class="translate-counter">
                {{ finishCount }} / {{wordList.length }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div class="translate-word-display">
                <bold>{{ $t('trans.word') }}: {{ wordStr }}</bold>
                <p v-if="showTranslation">{{ $t('trans.wordChineseMeaning') }}: {{ transStr }}</p>
            </div>
            <div class="translate-buttons">
                <el-button @click="toggleTranslation">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="markAsKnown">{{ $t('trans.markAsKnown') }}</el-button>
                <el-button @click="learnToday">{{ $t('trans.learnToday') }}</el-button>
                <el-button @click="startLearn">{{ $t('trans.startLearning') }}</el-button>
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
            wordList: [],
            currentIndex: 0,
            finishCount: 0,
            showTranslation: false
        };
    },
    methods: {
        toggleTranslation() {
            this.showTranslation = !this.showTranslation;
        },
        markAsKnown() {
            this.wordList[this.currentIndex].status = 'learned';
            this.nextWord();
            this.updateCount();
        },
        learnToday() {
            this.wordList[this.currentIndex].status = 'learning';
            this.nextWord();
            this.updateCount();
        },
        startLearn() {
            this.selectFinished();
        },
        nextWord() {
            this.currentIndex++;
            this.showTranslation = false;
            if (this.currentIndex < this.wordList.length) {
                this.updateWordDisplay();
            } else {
                this.selectFinished();
            }
        },
        async selectFinished() {
            let updateList = [];
            for (let i = 0; i < this.wordList.length; i++) {
                if (this.wordList[i].status === 'learned' || this.wordList[i].status === 'learning') {
                    updateList.push(this.wordList[i]);
                }
            }
            await realUpdate(updateList);
            this.$emit('update-status', 'learn');
        },
        updateWordDisplay() {
            this.wordStr = this.wordList[this.currentIndex].word;
            this.transStr = this.wordList[this.currentIndex].info.translate;
            this.updateCount();
        },
        async fetch() {
            try {
                this.wordList = await fetchWordList('not_learned');
                if (this.wordList && this.wordList.length > 0) {
                    this.updateWordDisplay();
                } else {
                    this.wordStr = this.$t('trans.noWordsAvailable');
                    this.transStr = '';
                }
            } catch (err) {
                console.error(err);
                this.wordStr = this.$t('trans.errorFetchingWords');
                this.transStr = '';
            }
        },
        updateCount() {
            this.finishCount = this.wordList.filter(word => word.status === 'learning').length;
        }          
    },
    mounted() {
        this.fetch();
    }
};
</script>

<style scoped>
</style>