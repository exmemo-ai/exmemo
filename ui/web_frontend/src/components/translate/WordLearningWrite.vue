<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.writeFromMemory') }}</h1>
            <div class="translate-counter">
                {{ finishCount }} / {{ wordList.length }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div v-if="wordList && wordList.length > 0" class="translate-word-display">
                <bold>{{ $t('trans.wordTranslation') }}: {{ transStr }}</bold>
                <p>{{ $t('trans.word') }}: {{ wordStr }}</p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="toggleTranslation">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="goPrev">{{ $t('trans.goPrev') }}</el-button>
                <el-button @click="goNext">{{ $t('trans.goNext') }}</el-button>
                <!--
                <el-button @click="save">{{ $t('save') }}</el-button>
                -->
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
            hideStatus: 0,
        };
    },
    methods: {
        toggleTranslation() {
            this.hideStatus = this.hideStatus+1;
            if (this.hideStatus > 2) {
                this.hideStatus = 0;
            }
            this.updateWordDisplay();
        },
        goPrev() {
            this.currentIndex = (this.currentIndex - 1 + this.wordList.length) % this.wordList.length;
            this.hideStatus = 0;
            this.updateWordDisplay();
        },
        goNext() {
            this.currentIndex = (this.currentIndex + 1) % this.wordList.length;
            this.hideStatus = 0;
            this.updateWordDisplay();
        },
        updateWordDisplay() {
            if (this.currentIndex < this.wordList.length) {
                const item = this.wordList[this.currentIndex]['item']
                if (this.hideStatus == 0) {
                    this.wordStr = '_'.repeat(item.word.length);
                } else if (this.hideStatus == 1) {
                    this.wordStr = item.word[0] + ' ' + '_'.repeat(item.word.length - 1);
                } else {
                    this.wordStr = item.word;
                }
                this.transStr = item.info.translate;
                this.updateCount();
            }
        },
        updateCount() {
            this.finishCount = this.currentIndex + 1;
        },
        save() { // not use
            let tmpList = []
            for (let i = 0; i < this.wordList.length; i++) {
                tmpList.push(this.wordList[i]['item']);
            }
            realUpdate(tmpList);
            this.$emit('update-status', 'select');
        },
        async fetch() {
            this.wordList = []
            const dateStr = new Date().toISOString().slice(0, 10);
            let tmpList = await fetchWordList('review', dateStr);
            for (let i = 0; i < tmpList.length; i++) {
                this.wordList.push({'item':tmpList[i], 'flag':false});
            }
            this.wordList.sort((a, b) => {
                return b.item.created_time - a.item.created_time;
            });
            if (this.wordList && this.wordList.length > 0) {
                this.updateWordDisplay();
            } else {
                this.wordStr = '';
                this.transStr = '';
            }
        },     
    },
    mounted() {
        this.fetch();
    }
};
</script>

<style scoped>
</style>