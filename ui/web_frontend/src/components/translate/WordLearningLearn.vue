<template>
    <div>
        <div class="translate-header">
            <h1>{{ $t('trans.wordLearning') }}</h1>
            <div class="translate-counter" v-if="wordList.length">
                {{ finishCount }} / {{ wordList.length }}
            </div>
        </div>
        <div class="content word-learning translate-common-style">
            <div v-if="wordList.length > 0" class="translate-word-display">
                <bold class="word">{{ $t('trans.word') }}: {{ wordStr }}</bold>
                <p class="example-sentence">{{ $t('trans.exampleSentence') }}: {{ exampleSentence }}</p>
                <p v-if="showTranslation" class="sentence-meaning">{{ $t('trans.sentenceMeaning') }}: {{ sentenceMeaning }}</p>
                <p v-if="showTranslation" class="word-meaning">{{ $t('trans.wordMeaning') }}: {{ transStr }}</p>
                <p v-if="showTranslation" class="word-chinese-meaning">{{ $t('trans.wordChineseMeaning') }}: {{ wordChineseMeaning }}</p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="showAnswer">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="learned">{{ $t('trans.learned') }}</el-button>
                <el-button @click="learnMore">{{ $t('trans.learnMore') }}</el-button>
                <el-button @click="learnFinished">{{ $t('trans.finish') }}</el-button>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';
import { getURL, setDefaultAuthHeader } from '@/components/support/conn';
import { fetchWordList, realUpdate } from './WordLearningSupport';

export default {
    data() {
        return {
            wordStr: '',
            transStr: '',
            exampleSentence: '',
            sentenceMeaning: '',
            wordChineseMeaning: '',
            wordList: [],
            currentIndex: 0,
            finishCount: 0,
            showTranslation: false,
        };
    },
    methods: {
        showAnswer() {
            this.showTranslation = true;
        },
        learned() {
            if ('learn_times' in this.wordList[this.currentIndex].info) {
                this.wordList[this.currentIndex].info['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info['learn_times'] = 1;
            }
            this.wordList[this.currentIndex].info['learn_date'] = new Date().toISOString().split('T')[0];
            this.wordList[this.currentIndex].status = 'review';
            this.nextWord();
        },
        learnMore() {
            if ('learn_times' in this.wordList[this.currentIndex].info) {
                this.wordList[this.currentIndex].info['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info['learn_times'] = 1;
            }
            this.nextWord();
        },
        nextWord() {
            this.showTranslation = false;
            let startIndex = this.currentIndex;
            do {
                this.currentIndex = (this.currentIndex + 1) % this.wordList.length;
                if (this.wordList[this.currentIndex].status !== 'review') {
                    this.updateWordDisplay();
                    return;
                }
            } while (this.currentIndex !== startIndex);
            this.learnFinished()
        },
        async learnFinished() {
            await realUpdate(this.wordList);
            this.$emit('update-status', 'review');
        },
        updateWordDisplay() {
            if (this.wordList.length > 0) {
                this.transStr = this.wordList[this.currentIndex].word;
                this.wordStr = this.wordList[this.currentIndex].word;
                this.sentenceMeaning = this.wordList[this.currentIndex].info.translate;
                this.wordChineseMeaning = this.wordList[this.currentIndex].info.translate || '词的中文意思';
                if ('examples' in this.wordList[this.currentIndex].info) {
                    const examples = this.wordList[this.currentIndex].info.examples;
                    if (examples.length > 0) {
                        this.updateExample(examples[Math.floor(Math.random() * examples.length)]);
                    }
                } else {
                    let func = 'api/translate/learn';
                    setDefaultAuthHeader();
                    const formData = new FormData();
                    formData.append('rtype', 'get_sentence');
                    formData.append('word', this.wordList[this.currentIndex].word);
                    axios.post(getURL() + func, formData).then((res) => {
                        if ('sentence' in res.data) {
                            let example = {
                                'sentence': res.data.sentence,
                                'word_meaning': res.data.word_meaning,
                                'sentence_meaning': res.data.sentence_meaning
                            }
                            this.wordList[this.currentIndex].info.examples = [example];
                        }
                        if (this.wordList[this.currentIndex].info.examples.length > 0) {
                            this.updateExample(this.wordList[this.currentIndex].info.examples[Math.floor(Math.random() * this.wordList[this.currentIndex].info.examples.length)]);
                        }
                    }).catch((err) => {
                        console.error(err);
                    });
                }
                this.updateCount();
            }
        },
        updateExample(data) {
            this.exampleSentence = data['sentence']
            this.transStr = data['word_meaning']
            this.sentenceMeaning = data['sentence_meaning']
        },
        updateCount() {
            this.finishCount = this.wordList.filter(word => word.status === 'review').length;
        },
        async fetch() {
            this.wordList = await fetchWordList('learning');
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