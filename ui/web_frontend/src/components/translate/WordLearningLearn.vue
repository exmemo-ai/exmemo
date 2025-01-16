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
                <bold class="word">
                    {{ $t('trans.word') }}: {{ wordStr }}
                    <el-button 
                        type="text" 
                        @click="speakWord">
                        <el-icon>
                            <component :is="isSpeaking ? 'VideoPause' : 'VideoPlay'" />
                        </el-icon>
                    </el-button>

                </bold>
                <p class="example-sentence">{{ $t('trans.exampleSentence') }}: {{ exampleSentence }}</p>
                <p v-if="showTranslation" >{{ $t('trans.sentenceMeaning') }}: {{ sentenceMeaning }}</p>
                <p v-if="showTranslation" >{{ $t('trans.wordMeaningInSentence') }}: {{ transStrInSentence }}</p>
                <p v-if="showTranslation" >{{ $t('trans.wordTranslation') }}: {{ wordTranslation }}</p>
            </div>
            <div v-else>
                {{ $t('trans.noWordsAvailable') }}
            </div>
            <div class="translate-buttons">
                <el-button @click="showAnswer">{{ $t('trans.showAnswer') }}</el-button>
                <el-button @click="learned">{{ $t('trans.learned') }}</el-button>
                <el-button @click="learnMore">{{ $t('trans.learnMore') }}</el-button>
                <el-button @click="save">{{ $t('save') }}</el-button>
            </div>
        </div>
    </div>
</template>

<script>
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import axios from 'axios';
import { getURL, setDefaultAuthHeader } from '@/components/support/conn';
import { fetchWordList, realUpdate } from './WordLearningSupport';
import { getLocale } from '@/main.js'

export default {
    components: {
        VideoPlay,
        VideoPause
    },
    data() {
        return {
            wordStr: '',
            wordTranslation: '',
            exampleSentence: '',
            sentenceMeaning: '',
            transStrInSentence: '',
            wordList: [],
            currentIndex: 0,
            finishCount: 0,
            showTranslation: false,
            isSpeaking: false,
            speechUtterance: null,
        };
    },
    methods: {
        showAnswer() {
            this.showTranslation = true;
        },
        async learned() {
            if ('learn_times' in this.wordList[this.currentIndex].info) {
                this.wordList[this.currentIndex].info['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info['learn_times'] = 1;
            }
            this.wordList[this.currentIndex].info['learn_date'] = new Date().toISOString().split('T')[0];
            this.wordList[this.currentIndex].status = 'review';
            await this.nextWord();
        },
        async learnMore() {
            if ('learn_times' in this.wordList[this.currentIndex].info) {
                this.wordList[this.currentIndex].info['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info['learn_times'] = 1;
            }
            await this.nextWord();
        },
        async nextWord() {
            this.showTranslation = false;
            let startIndex = this.currentIndex;
            do {
                this.currentIndex = (this.currentIndex + 1) % this.wordList.length;
                if (this.wordList[this.currentIndex].status !== 'review') {
                    await this.updateWordDisplay();
                    return;
                }
            } while (this.currentIndex !== startIndex);
            this.save()
        },
        async save() {
            await realUpdate(this.wordList);
            this.$emit('update-status', 'review');
        },
        async updateWordDisplay() {
            if (this.wordList.length > 0) {
                this.wordStr = this.wordList[this.currentIndex].word;
                this.wordTranslation = this.wordList[this.currentIndex].info.translate;;
                this.exampleSentence = '';
                this.sentenceMeaning = '';
                this.transStrInSentence = '';
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
                    await axios.post(getURL() + func, formData).then((res) => {
                        if ('examples' in res.data) {
                            this.wordList[this.currentIndex].info.examples = res.data.examples;
                            if (this.wordList[this.currentIndex].info.examples.length > 0) {
                                this.updateExample(this.wordList[this.currentIndex].info.examples[Math.floor(Math.random() * this.wordList[this.currentIndex].info.examples.length)]);
                            }
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
            this.sentenceMeaning = data['sentence_meaning']
            this.transStrInSentence = data['word_meaning']
        },
        updateCount() {
            this.finishCount = this.wordList.filter(word => word.status === 'review').length;
        },
        async fetch() {
            this.wordList = await fetchWordList('learning');
            this.updateWordDisplay();
        },
        speakWord() {
            if (this.isSpeaking) {
                window.speechSynthesis.cancel()
                this.isSpeaking = false
                return
            }

            try {
                this.speechUtterance = new SpeechSynthesisUtterance(this.wordStr)
                this.speechUtterance.lang = getLocale()
                
                this.speechUtterance.onend = () => {
                    this.isSpeaking = false
                }
                this.speechUtterance.onerror = () => {
                    this.isSpeaking = false
                    console.error('TTS error:', this.speechUtterance)
                }
                window.speechSynthesis.speak(this.speechUtterance)
                this.isSpeaking = true
            } catch (error) {
                console.error('TTS error:', error)
                this.isSpeaking = false
            }
        },
    },
    beforeUnmount() {
        if (this.isSpeaking) {
            window.speechSynthesis.cancel()
        }
    },
    mounted() {
        this.fetch();
    }
};
</script>

<style scoped>
.word {
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>