<template>
    <div style="display: flex; flex-direction: column;">
        <div style="margin-right: 5px; margin-bottom: 10px;">
            <el-button style="margin-right: 5px;" @click="searchWord">{{ $t('searchWord') }}</el-button>
            <el-button style="margin-right: 5px;" @click="handleSave">{{ $t('saveArticle') }}</el-button>
            <el-button size="small" type="primary" circle @click="handleAnalysis">
                {{ $t('viewMarkdown.ai') }}
            </el-button>
        </div>

        <div style="display: flex; flex-direction: column;">
            <el-text style="margin: 10px 0;">{{ $t('editArea') }}</el-text>
            <textarea v-model="inputText" @input="handleInput"
                style="width: 100%; height: 20vh; margin-bottom: 10px;"></textarea>
            <el-text style="margin: 10px 0;">{{ $t('operationArea') }} ({{ $t('clickToTranslate') }})</el-text>
            <div
                style="width: 100%; height: 33vh; overflow: auto; text-align: left; white-space: pre-line; margin-top: 10px;">
                <span v-for="word in words" :key="word" @mouseup="handleMouseUp($event)">
                    {{ word }}&nbsp;
                </span>
            </div>
        </div>

        <TranslatePopup
            :visible="showPopup"
            :position="popupPosition"
            ref="translatePopup"
            @alert="showAlert"
        />

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
import AIDialog from '@/components/ai/AIDialog.vue';
import TranslatePopup from './TranslatePopup.vue';

export default {
    name: 'EnReader',
    components: {
        CheckDialog,
        AIDialog,
        TranslatePopup
    },
    data() {
        return {
            isMobile: false,
            outerMargin: 50,
            inputText: '',
            words: [],
            showPopup: false,
            popupPosition: { x: 0, y: 0 },
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
                parseBackendError(err);
            });
        },
        handleAnalysis() {
            this.aiDialogVisible = true;
            console.log('analysis:', this.inputText);
        },
        handleInput() {
            this.words = this.inputText.split(/(?<=[^\w\n])|(?=[^\w\n])/);
            this.words = this.words.filter((word) => word !== ' ');
        },
        handleMouseUp(event) {
            const selectedText = window.getSelection().toString().trim();            
            this.setPopPosition(event);
            this.showPopup = true;
            
            if (selectedText) {
                this.$refs.translatePopup.translateSelection(selectedText);
            } else {
                const word = event.target.textContent.trim();
                if (word) {
                    this.$refs.translatePopup.translateWord(word, event.target);
                }
            }
        },
        setPopPosition(event) {
            this.popupPosition = {
                x: event.clientX,
                y: event.clientY
            };
            
            if (this.popupPosition.x + 220 > window.innerWidth) {
                this.popupPosition.x = window.innerWidth - 220;
            }
            if (this.popupPosition.y + 200 > window.innerHeight) {
                this.popupPosition.y = window.innerHeight - 200;
            }
        },
        hidePopup(event) {
            const popupTime = this.$refs.translatePopup ? this.$refs.translatePopup.getPopupTime() : 0;
            if (new Date().getTime() - popupTime < 1000) {
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
        showAlert(message) {
            alert(message);
        }
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