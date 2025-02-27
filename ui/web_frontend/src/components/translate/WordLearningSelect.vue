<template>
    <div>
        <div>
            <el-text>{{ $t('trans.selectWordList') }}</el-text>
            <el-select v-model="currentVOC" @change="handleVocChange" style="width: 200px; margin-left: 10px;">
                <el-option 
                    v-for="item in fromList" 
                    :key="item"
                    :label="$t('trans.' + item)"
                    :value="item">
                </el-option>
            </el-select>
        </div>
        <div class="translate-header">
            <div class="translate-counter">
                {{ $t('trans.todayLearn') }}: {{ selectCount }}, {{ $t('trans.options') }}: {{ getTotalCount() }}
            </div>
        </div>
        <div class="translate-common-style">            
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
import { fetchWordList, realUpdate, getMeaning, LEARN_WORD_VOC, LEARN_WORD_VOC_DEFAULT } from './WordLearningSupport';
import { getWordsFrom } from './TransFunction';
import SettingService from '@/components/settings/settingService';

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
            fromList: [],
            currentVOC: '',
        };
    },
    methods: {
        toggleTranslation() {
            this.showTranslation = !this.showTranslation;
        },
        markAsKnown() {
            if (this.wordList.length === 0) {
                return;
            }
            this.wordList[this.currentIndex].status = 'learned';
            this.nextWord();
            this.updateCount();
            this.needSave = true;
        },
        learnToday() {
            if (this.wordList.length === 0) {
                return;
            }
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
        async updateWordDisplay() {
            if (this.wordList.length > 0 && this.currentIndex < this.wordList.length) {
                this.wordStr = this.wordList[this.currentIndex].word;
                this.transStr = await getMeaning(this.wordList[this.currentIndex].info, this.currentVOC);
                this.freqStr = this.wordList[this.currentIndex].freq;
            } else {
                this.wordStr = ""
                this.transStr = ""
                this.freqStr = ""
            }
            this.updateCount();
        },
        async fetch() {
            try {
                this.fromList = await getWordsFrom(this);
                const settingService = SettingService.getInstance();
                await settingService.loadSetting();
                const currentVOC = settingService.getSetting(LEARN_WORD_VOC, LEARN_WORD_VOC_DEFAULT);
                if (currentVOC && this.fromList.includes(currentVOC)) {
                    this.currentVOC = currentVOC;
                } else if (this.fromList.length > 0) {
                    this.currentVOC = this.fromList[0];
                }
                
                this.wordList = await fetchWordList('get_words', 'not_learned', null, this.currentVOC);
                this.updateWordDisplay();
            } catch (err) {
                console.error(err);
                this.wordStr = this.$t('trans.errorFetchingWords');
                this.transStr = '';
            }
        },
        async handleVocChange(newValue) {
            const settingService = SettingService.getInstance();
            settingService.setSetting(LEARN_WORD_VOC, newValue);
            await settingService.saveSetting();
            await this.fetch();
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
