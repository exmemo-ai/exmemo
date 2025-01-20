<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.selectWord') }}</h1>
            <div class="translate-counter">
                {{ selectCount }} / {{ getTotalCount() }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div v-if="wordList.length > 0" class="translate-word-display">
                <p>{{ $t('trans.word') }}: {{ wordStr }}</p>
                <p>{{ $t('trans.freq') }}: {{ freqStr }}</p>
                <p v-if="showTranslation">{{ $t('trans.wordTranslation') }}: {{ transStr }}</p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="toggleTranslation">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="markAsKnown">{{ $t('trans.markAsKnown') }}</el-button>
                <el-button @click="learnToday">{{ $t('trans.learnToday') }}</el-button>
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
            freqStr: '',
            wordList: [],
            currentIndex: 0,
            selectCount: 0,
            showTranslation: false,
            needSave: false,
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
            this.needSave = true;
        },
        learnToday() {
            this.wordList[this.currentIndex].status = 'learning';
            this.nextWord();
            this.updateCount();
            this.needSave = true;
        },
        nextWord() {
            this.currentIndex++;
            this.showTranslation = false;
            if (this.currentIndex < this.wordList.length) {
                this.updateWordDisplay();
                //this.save(false);
            } else {
                this.save(true);
            }
        },
        async save(nextStep = true) {
            let updateList = [];
            for (let i = 0; i < this.wordList.length; i++) {
                if (this.wordList[i].status === 'learned' || this.wordList[i].status === 'learning') {
                    updateList.push(this.wordList[i]);
                }
            }
            await realUpdate(updateList);
            if (nextStep) {
                this.$emit('update-status', 'learn');
            }
        },
        updateWordDisplay() {
            this.wordStr = this.wordList[this.currentIndex].word;
            this.transStr = this.wordList[this.currentIndex].info.translate;
            this.freqStr = this.wordList[this.currentIndex].freq;
            this.updateCount();
        },
        async fetch() {
            try {
                this.wordList = await fetchWordList('not_learned');
                this.updateWordDisplay();
            } catch (err) {
                console.error(err);
                this.wordStr = this.$t('trans.errorFetchingWords');
                this.transStr = '';
            }
        },
        updateCount() {
            this.selectCount = this.wordList.filter(word => word.status === 'learning').length;
        },
        getTotalCount() {
            const notLearned = this.wordList.filter(word => word.status !== 'learned');
            return notLearned.length;
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