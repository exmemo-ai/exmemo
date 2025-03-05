<template>
    <div>
        <div class="translate-header">
            <div class="translate-counter" v-if="wordList.length">
                {{ $t('trans.todayLearn') }}: {{ wordList.length }}, {{ $t('trans.learned') }}: {{ finishCount }}, {{$t('trans.current')}}: {{this.currentIndex+1}}/{{wordList.length}}
            </div>
        </div>
        <div class="translate-common-style">
            <div v-if="wordList.length > 0" class="translate-word-display">
                <p class="word">
                    {{ $t('trans.word') }}: {{ wordStr }}
                    <el-button 
                        type="text" 
                        @click="speakWord">
                        <el-icon>
                            <component :is="isSpeaking ? 'VideoPause' : 'VideoPlay'" />
                        </el-icon>
                    </el-button>
                </p>
                {{ $t('trans.phonetic') }}: {{ wordPhonetic }}
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
                <el-button @click="handleAI" :icon="ChatLineRound">{{ $t('trans.aiSupport') }}</el-button>
            </div>
        </div>
    </div>
    <AIDialog
        v-model="aiDialogVisible"
        :specificContent="wordStr"
        :default-reference-type="defaultReferenceType"
        :etype="etype"
    />
</template>

<script>
import { VideoPlay, VideoPause, ChatLineRound } from '@element-plus/icons-vue'
import { fetchWordList, realUpdate, getExamples, getMeaning } from './WordLearningSupport';
import { getLocale } from '@/main.js'
import AIDialog from '@/components/ai/AIDialog.vue'

export default {
    components: {
        VideoPlay,
        VideoPause,
        AIDialog,
        ChatLineRound,
    },
    data() {
        return {
            wordStr: '',
            wordPhonetic: '',
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
            needSave: false,
            etype: 'translate',
            aiDialogVisible: false,
            defaultReferenceType: 'specific',
        };
    },
    methods: {
        showAnswer() {
            this.showTranslation = true;
        },
        async learned() {
            if (this.wordList.length === 0) {
                return;
            }
            if (this.wordList[this.currentIndex].info.opt == undefined) {
                this.wordList[this.currentIndex].info.opt = {}
            }            
            if ('learn_times' in this.wordList[this.currentIndex].info.opt) {
                this.wordList[this.currentIndex].info.opt['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info.opt['learn_times'] = 1;
            }
            this.wordList[this.currentIndex].info.opt['learn_date'] = new Date().toISOString().split('T')[0];
            this.wordList[this.currentIndex].status = 'review';
            this.needSave = true;
            await this.nextWord();
        },
        async learnMore() {
            if (this.wordList.length === 0) {
                return;
            }
            if (this.wordList[this.currentIndex].info.opt == undefined) {
                this.wordList[this.currentIndex].info.opt = {}
            }            
            if ('learn_times' in this.wordList[this.currentIndex].info.opt) {
                this.wordList[this.currentIndex].info.opt['learn_times'] += 1;
            } else {
                this.wordList[this.currentIndex].info.opt['learn_times'] = 1;
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
                    //this.save(false);
                    return;
                }
            } while (this.currentIndex !== startIndex);
            this.save(true)
        },
        async save(nextStep = true) {
            if (this.wordList.length > 0) {
                localStorage.setItem('learning_word', this.wordList[this.currentIndex].word);
            }
            if (this.needSave) {
                await realUpdate(this.wordList);
                this.needSave = false;
            }
            if (nextStep) {
                this.$emit('update-status', 'write');
            }
        },
        async updateWordDisplay() {
            if (this.wordList.length > 0) {
                this.wordStr = this.wordList[this.currentIndex].word;
                if (this.wordList[this.currentIndex].info.base) {
                    this.wordPhonetic = this.wordList[this.currentIndex].info.base.phonetic;
                } else {
                    this.wordPhonetic = '';
                }
                this.wordTranslation = await getMeaning(this.wordList[this.currentIndex].info);
                this.exampleSentence = '';
                this.sentenceMeaning = '';
                this.transStrInSentence = '';
                if (this.wordList[this.currentIndex].info && this.wordList[this.currentIndex].info.base && this.wordList[this.currentIndex].info.base.example_list) {
                    const examples = this.wordList[this.currentIndex].info.base.example_list;
                    if (examples.length > 0 && 'sentence' in examples[0]) {
                        this.updateExample(examples[Math.floor(Math.random() * examples.length)]);
                        this.updateCount();
                        return;
                    }
                }
                const data = await getExamples(this.wordList[this.currentIndex].word);
                if (data && 'examples' in data && data.word === this.wordList[this.currentIndex].word) {
                    if (this.wordList[this.currentIndex].info.base === undefined) {
                        this.wordList[this.currentIndex].info.base = {}
                    }
                    this.wordList[this.currentIndex].info.base.example_list = data.examples;
                    const examples = this.wordList[this.currentIndex].info.base.example_list;
                    if (examples.length > 0 && 'sentence' in examples[0]) {
                        this.updateExample(examples[Math.floor(Math.random() * examples.length)]);
                        this.updateCount();
                        return;
                    }
                }
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
            this.wordList = await fetchWordList('get_words', 'learning');
            const savedWord = localStorage.getItem('learning_word');
            if (savedWord) {
                const savedWordIndex = this.wordList.findIndex(item => item.word === savedWord);
                if (savedWordIndex !== -1) {
                    this.currentIndex = savedWordIndex;
                }
            }
            await this.updateWordDisplay();
        },
        handleAI() {
            this.aiDialogVisible = true;
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
    },
    expose: ['save'],
};
</script>

<style scoped>
.word {
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>