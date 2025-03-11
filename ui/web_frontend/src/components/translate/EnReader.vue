<template>
    <div style="display: flex; flex-direction: column;">
        <el-button-group style="margin-right: 5px; margin-bottom: 10px;">
            <el-button style="margin-right: 5px;" @click="searchWord">{{ $t('searchWord') }}</el-button>
            <el-button style="margin-right: 5px;" @click="handleSave">{{ $t('saveArticle') }}</el-button>
            <el-button @click="handleAnalysis">{{ $t('AIQA') }}</el-button>
        </el-button-group>

        <div style="display: flex; flex-direction: column;">
            <el-text style="margin: 10px 0;">{{ $t('editArea') }}</el-text>
            <textarea v-model="inputText" @input="handleInput"
                style="width: 100%; height: 20vh; margin-bottom: 10px;"></textarea>
            <el-text style="margin: 10px 0;">{{ $t('operationArea') }} ({{ $t('clickToTranslate') }})</el-text>
            <div
                style="width: 100%; height: 33vh; overflow: auto; text-align: left; white-space: pre-line; margin-top: 10px;">
                <span v-for="word in words" :key="word" @mousedown="handleMouseDown"
                    @mouseup="handleMouseUp($event, word)">
                    {{ word }}&nbsp;
                </span>
            </div>
        </div>

        <div v-if="showPopup"
            :style="{ top: `${popupPosition.y}px`, left: `${popupPosition.x}px`, maxHeight: '200px', height: 'auto', overflow: 'auto' }"
            class="popup">
            <div style="display: flex; flex-direction: column; margin: 5px;">
                <div style="flex-grow: 1;">
                    <button @click="wordInSentence" style="font-size: 12px;">{{ $t('definitionInSentence')
                        }}</button>
                    <button @click="translateSelection" style="font-size: 12px;">{{ $t('translateSelection')
                        }}</button>
                </div>
                <div style="flex-grow: 0; text-align: left; white-space: pre-line;">
                    {{ showText }}
                </div>
            </div>
        </div>

        <CheckDialog ref="checkDialog" />
        <AIDialog
            :full-content="getAllCountent()"
            :selected-content="getSelectedContent()"
            :etype="etype"
            v-model="aiDialogVisible"
            default-reference-type="all"
        />
    </div>
</template>

<script>
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';
import axios from 'axios';
import CheckDialog from './LookupDialog.vue';
import { translateFunc } from './TransFunction';
import AIDialog from '@/components/ai/AIDialog.vue'

export default {
    name: 'EnReader',
    components: {
        CheckDialog,
        AIDialog
    },
    data() {
        return {
            isMobile: false,
            outerMargin: 50,
            inputText: '',
            words: [],
            currentWord: '',
            showPopup: false,
            popupPosition: { x: 0, y: 0 },
            showText: '',
            popupTime: null,
            pressTimer: null,
            etype: 'translate',
            aiDialogVisible: false,
        };
    },
    methods: {
        handleSave() {
            console.log('save:', this.inputText);
            if (this.inputText === '') {
                alert(this.$t('emptyContent'));
                return;
            }
            let func = 'api/translate/article/'
            setDefaultAuthHeader();
            const formData = new FormData();
            let title = this.inputText.split('\n')[0].substring(0, 20);
            formData.append('title', title);
            formData.append('user_id', localStorage.getItem('username'));
            formData.append('content', this.inputText);
            let created_time = new Date().toISOString();
            formData.append('created_time', created_time);
            axios.post(getURL() + func, formData).then((res) => {
                console.log(res.data);
                this.$message({
                    type: 'success',
                    message: this.$t('saveSuccess'),
                });
            }).catch((err) => {
                parseBackendError(this, err);
            });
        },
        handleAnalysis() {
            this.aiDialogVisible = true;
            console.log('analysis:', this.inputText);
        },
        handleInput() {
            //this.words = this.inputText.split(' ');
            this.words = this.inputText.split(/(?<=[^\w\n])|(?=[^\w\n])/);
            this.words = this.words.filter((word) => word !== ' ');
        },
        handleMouseDown() {
            console.log('down')
            this.pressTimer = setTimeout(() => {
                this.pressTimer = null;
            }, 500);
        },
        handleMouseUp(event, word) {
            console.log('Up', word, 'showPopup:', this.showPopup);
            if (this.showPopup) {
                return;
            }
            if (this.pressTimer) {
                clearTimeout(this.pressTimer);
                this.pressTimer = null;
                this.handleShortPress(event, word);
            } else {
                this.handleLongPress(event, word);
            }
        },
        setPos(event) {
            this.popupPosition.x = event.clientX;
            this.popupPosition.y = event.clientY;
            if (this.popupPosition.x + 200 > window.innerWidth) {
                this.popupPosition.x = window.innerWidth - 200;
            } else if (this.popupPosition.x < 0) {
                this.popupPosition.x = 0;
            }
            if (this.popupPosition.y + 100 > window.innerHeight) {
                this.popupPosition.y = window.innerHeight - 100;
            } else if (this.popupPosition.y < 0) {
                this.popupPosition.y = 0;
            }
        },
        handleShortPress(event, word) {
            // Short press to translate word.
            console.log("short press", event, word)
            this.setPos(event);
            this.currentWord = word;
            let sentence = this.getSentence(event.target);
            this.translate('word', word, sentence);
        },
        handleLongPress(event, word) {
            console.log("long press", event, word)
            let selectedText = window.getSelection().toString();
            this.setPos(event);
            if (selectedText) {
                // Long press with selected text.
                console.log(selectedText);
                this.translate('sentence', null, selectedText);
            } else {
                let sentence = this.getSentence(event.target);
                this.translate('word_role', word, sentence)
            }
        },
        wordInSentence() {
            if (this.currentWord === '') {
                alert(this.$t('selectWordAlert'));
            }
            console.log('wordInSentence');
            if (window.getSelection().anchorNode.parentElement === null) {
                return;
            }
            let sentence = this.getSentence(window.getSelection().anchorNode.parentElement);
            this.translate('word_role', this.currentWord, sentence)
        },
        translateSelection() {
            console.log('translateSelection');
            let selectedText = window.getSelection().toString();
            if (selectedText) {
                this.translate('sentence', null, selectedText);
            } else {
                alert(this.$t('selectChineseAlert'));
            }
        },
        getSentence(element) {
            console.log('getSentence:', element);
            let sentence = [];
            let text = [];
            let prev = element.previousSibling;
            while (prev) {
                if (prev.nodeName !== 'SPAN' || this.issymbol(prev.textContent)) {
                    break;
                }
                text = [prev.textContent.trim()].concat(text);
                prev = prev.previousSibling;
            }
            sentence = text.concat([element.textContent.trim()]);
            if (this.issymbol(element.textContent) == false) {
                let next = element.nextSibling;
                text = [];
                while (next) {
                    if (next.nodeName !== 'SPAN') {
                        break;
                    }
                    text = text.concat([next.textContent.trim()]);
                    if (this.issymbol(next.textContent)) {
                        break;
                    }
                    next = next.nextSibling;
                }
                sentence = sentence.concat(text);
            }
            console.log('sentence:', sentence);
            return sentence.join(" ");
        },
        translateCallback(info) {
            console.log(info);
            console.log('post result, showPopup:', this.showPopup);
            this.showPopup = true;
            this.popupTime = new Date().getTime();
            this.showText = info;
        },
        translate(rtype, word, sentence) {
            translateFunc(this, rtype, word, sentence, this.translateCallback);
        },
        issymbol(text) {
            let regex = /[.,;!?]$/;
            return regex.test(text.trim());
        },
        hidePopup(event) {
            console.log('hidePopup, event:', event);
            if (new Date().getTime() - this.popupTime < 1000) {
                return;
            }
            this.showPopup = false;
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
            if (this.isMobile) {
                this.outerMargin = 0;
            } else {
                this.outerMargin = 0;
            }
        },
        searchWord() {
            this.$refs.checkDialog.openDialog(this);
        },
        getAllCountent() {
            return this.inputText;
        },
        getSelectedContent() {
            let selectedText = window.getSelection().toString();
            if (selectedText) {
                return selectedText;
            }
            return this.inputText;
        },
    },
    mounted() {
        this.handleResize()
        window.addEventListener('resize', this.handleResize);
        window.addEventListener('click', this.hidePopup);
    },
    beforeUnmount() {
        window.removeEventListener('click', this.hidePopup);
        window.removeEventListener('resize', this.handleResize);
    },
};
</script>

<style scoped>
.popup {
    margin: 2px;
    position: absolute;
    width: 200px;
    height: 100px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    font-size: 12px;
}
</style>