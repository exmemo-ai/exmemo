<template>
    <div>
        <div style="margin-bottom: 10px;">
            <el-text>{{ $t('trans.selectWordList') }}</el-text>
            <el-select v-model="currentVOC" @change="handleVocChange" style="width: 150px; margin-left: 10px;">
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
                {{ $t('trans.todayLearn') }}: {{ selectCount }}, {{ $t('trans.learned') }}: {{ getLearnedCount() }}, {{ $t('trans.options') }}: {{ getTotalCount() }}
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
            lastSavedList: [],
        };
    },
    methods: {
        toggleTranslation() {
            this.showTranslation = !this.showTranslation;
        },
        async markAsKnown() {
            if (this.wordList.length === 0) {
                return;
            }
            this.wordList[this.currentIndex].status = 'learned';
            this.needSave = true;
            await this.nextWord();
            this.updateCount();
        },
        async learnToday() {
            if (this.wordList.length === 0) {
                return;
            }
            this.wordList[this.currentIndex].status = 'learning';
            this.needSave = true;
            await this.nextWord();
            this.updateCount();
        },
        async nextWord() {
            this.currentIndex++;
            this.showTranslation = false;
            if (this.currentIndex < this.wordList.length) {
                this.updateWordDisplay();
                this.save(false);
            } else {
                await this.save(true);
            }
        },
        async save(nextStep = true) {
            if (this.needSave) {
                const changedWords = this.wordList.filter((word, index) => {
                    const lastSaved = this.lastSavedList[index];
                    return !lastSaved || 
                           JSON.stringify(word.status) !== JSON.stringify(lastSaved.status) ||
                           JSON.stringify(word.info) !== JSON.stringify(lastSaved.info);
                });
                
                if (changedWords.length > 0) {
                    await realUpdate(changedWords);
                    this.lastSavedList = JSON.parse(JSON.stringify(this.wordList));
                }
                this.needSave = false;
            }
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
                this.lastSavedList = JSON.parse(JSON.stringify(this.wordList));
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
            const notLearned = this.wordList.filter(word => word.status === 'not_learned');
            return notLearned.length;
        },
        getLearnedCount() {
            return this.wordList.filter(word => word.status === 'learned').length;
        }
    },
    mounted() {
        this.fetch();
    },
    expose: ['save'],
};
</script>

<style scoped>
</style>
