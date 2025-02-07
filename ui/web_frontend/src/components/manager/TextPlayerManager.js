import { t } from '@/utils/i18n'
import { TextSplitter } from '../../utils/TextSplitter'
import SettingService from '../settings/settingService'

export class TextPlayerManager {
    constructor(text, lang = 'zh-CN') {
        this.t = t;
        this.settingService = SettingService.getInstance();
        this.settingService.loadSetting();
        this.lang = lang;
        this.textSplitter = new TextSplitter(this.lang);
        this.paragraphs = [];
        this.currentIndex = 0;
        this.utterance = null;
        this.isPlaying = false;
        this.onSpeakCallback = null;
    }

    getText() {
        const sentence = this.getCurrentSentence();
        return sentence ? sentence.text : null;
    }

    setContent(data) {
        console.log("setText", data);
        this.paragraphs = [];
        
        if (typeof(data) === 'string') {
            const paragraphs = data.split('\n');
            for (let i = 0; i < paragraphs.length; i++) {
                const paragraphText = paragraphs[i];
                const sentences = this.textSplitter.splitParagraphIntoSentences(paragraphText);
                const paragraph = {
                    text: paragraphText,
                    sentences: sentences.map((sentence, index) => ({
                        text: sentence,
                        node: null,
                        globalIndex: this.paragraphs.reduce((acc, para) => acc + para.sentences.length, 0) + index
                    }))
                };
                this.paragraphs.push(paragraph);
            }
        } else if (data instanceof Node) {
            const startNode = data;
            const previewElement = startNode.getRootNode();
            const walker = document.createTreeWalker(
                previewElement,
                NodeFilter.SHOW_TEXT,
                null
            );
            let node = walker.currentNode;
            while (node && node !== startNode) {
                node = walker.nextNode();
            }
            while (node) {
                const nodeText = node.textContent;
                if (nodeText.trim()) {
                    const sentences = this.textSplitter.splitParagraphIntoSentences(nodeText);
                    const paragraph = {
                        text: nodeText,
                        sentences: sentences.map((sentence, index) => ({
                            text: sentence,
                            node: node,
                            globalIndex: this.paragraphs.reduce((acc, para) => acc + para.sentences.length, 0) + index
                        }))
                    };
                    this.paragraphs.push(paragraph);
                }
                node = walker.nextNode();
            }
        }
        this.currentIndex = 0;
    }

    pause() {
        if (this.isPlaying) {
            this.isPlaying = false;
            window.speechSynthesis.cancel();
        }
    }

    resume() {
        if (!this.isPlaying) {
            this.speak(this.currentIndex);
        }
    }

    stop() {
        this.pause();
        this.currentIndex = -1;
        if (this.onSpeakCallback) {
            this.onSpeakCallback("", -1);
        }        
    }

    nextSentence() {
        if (this.currentIndex < this.getAllSentences().length - 1) {
            this.pause();
            this.speak(this.currentIndex + 1);
        }
    }

    prevSentence() {
        if (this.currentIndex > 0) {
            this.pause();
            this.speak(this.currentIndex - 1);
        }
    }

    nextParagraph() {
        const currentParaIndex = this.findParagraphIndex(this.currentIndex);
        if (currentParaIndex < this.paragraphs.length - 1) {
            const nextParaIndex = currentParaIndex + 1;
            const nextSentenceIndex = this.paragraphs[nextParaIndex].sentences[0].globalIndex;
            this.pause();
            this.speak(nextSentenceIndex);
        }
    }

    prevParagraph() {
        const currentParaIndex = this.findParagraphIndex(this.currentIndex);
        if (currentParaIndex > 0) {
            const prevParaIndex = currentParaIndex - 1;
            const prevSentenceIndex = this.paragraphs[prevParaIndex].sentences[0].globalIndex;
            this.pause();
            this.speak(prevSentenceIndex);
        }
    }

    setOnSpeakCallback(callback) {
        this.onSpeakCallback = callback;
    }

    speak(index) {
        console.log('speak', index);
        const sentence = this.getAllSentences()[index];
        if (sentence) {
            this.currentIndex = index;
            const text = sentence.text;
            
            if (this.containsOnlyPunctuation(text)) {
                console.log('Skipping punctuation-only sentence:', text);
                this.handleSpeechEnd();
                return;
            }

            const node = sentence.node;
            
            if (this.onSpeakCallback) {
                this.onSpeakCallback(text, index, node);
            }

            this.utterance = new SpeechSynthesisUtterance(text);
            const setting = this.settingService.getSettingCache().setting;
            //console.log("setting", setting);
            
            const voices = window.speechSynthesis.getVoices();
            if (setting.tts_voice && voices.length > 0) {
                const selectedVoice = voices.find(voice => voice.name === setting.tts_voice);
                if (selectedVoice) {
                    //console.log('Using voice:', selectedVoice.name);
                    this.utterance.voice = selectedVoice;
                    this.utterance.lang = selectedVoice.lang;
                }
            }
            
            if (setting.tts_language) {
                //console.log('Override language to:', setting.tts_language);
                this.utterance.lang = setting.tts_language;
            } else {
                if (!this.utterance.lang) {
                    this.utterance.lang = this.lang;
                }
            }

            if (typeof(setting.tts_speed) === 'string') {
                setting.tts_speed = parseFloat(setting.tts_speed);
            }
            this.utterance.rate = setting.tts_speed;

            /*
            console.log('Final speech settings:', {
                voice: this.utterance.voice?.name,
                lang: this.utterance.lang,
                rate: this.utterance.rate
            });
            */

            this.utterance.onend = () => this.handleSpeechEnd();

            window.speechSynthesis.speak(this.utterance);
            this.isPlaying = true;
        } else {
            console.log(this.t('viewMarkdown.noTextSelected'));
        }
    }

    handleSpeechEnd() {
        const hasNextSentence = this.currentIndex < this.getAllSentences().length - 1;
        
        if (this.isPlaying && hasNextSentence) {
            this.speak(this.currentIndex + 1);
        } else {
            this.isPlaying = false;
            console.log('Speech playback completed');
        }
    }

    containsOnlyPunctuation(text) {
        // 匹配所有标点符号和空白字符
        const punctuationRegex = /^[\s\p{P}]+$/u;
        return punctuationRegex.test(text.trim());
    }

    findParagraphIndex(sentenceIndex) {
        let total = 0;
        for (let i = 0; i < this.paragraphs.length; i++) {
            const paraLength = this.paragraphs[i].sentences.length;
            total += paraLength;
            if (sentenceIndex < total) return i;
        }
        return this.paragraphs.length - 1;
    }

    updateSettings(voice, rate, volume, pitch) {
        if (this.utterance) {
            if (voice) this.utterance.voice = voice;
            this.utterance.rate = rate;
            this.utterance.volume = volume;
            this.utterance.pitch = pitch;
        }
    }

    getStatus() {
        const currentParaIndex = this.findParagraphIndex(this.currentIndex);
        const canGoPrevPara = currentParaIndex > 0;
        const canGoNextPara = currentParaIndex < this.paragraphs.length - 1;
        const canGoPrevSentence = this.currentIndex > 0;
        const canGoNextSentence = this.currentIndex < this.getAllSentences().length - 1;

        return {
            isPlaying: this.isPlaying,
            currentIndex: this.currentIndex,
            sentencesCount: this.getAllSentences().length,
            currentSentence: this.getText() || '',
            currentParagraph: currentParaIndex,
            canGoNextPara: canGoNextPara,
            canGoPrevPara: canGoPrevPara,
            canGoNextSentence: canGoNextSentence,
            canGoPrevSentence: canGoPrevSentence,
            currentNode: this.getCurrentSentence()?.node || null,
        };
    }

    getAllSentences() {
        return this.paragraphs.flatMap(p => p.sentences);
    }

    getCurrentSentence() {
        return this.getAllSentences()[this.currentIndex];
    }
}
