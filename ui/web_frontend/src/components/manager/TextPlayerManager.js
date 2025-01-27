import { useI18n } from 'vue-i18n'
import { TextSplitter } from '../../utils/TextSplitter'

export class TextPlayerManager {
    constructor(text, lang = 'zh-CN') {
        const { t } = useI18n();
        this.t = t;
        this.lang = lang;
        this.textSplitter = new TextSplitter(lang);
        this.sentences = [];
        this.paragraphs = [];
        this.currentIndex = 0;
        this.utterance = null;
        this.isPlaying = false;
        this.setText(text);
        this.onSpeakCallback = null;
    }

    getText() {
        return this.text;
    }

    setText(text) {
        console.log("setText", text);
        this.text = text || "";
        const { paragraphs, sentences } = this.textSplitter.splitText(this.text);
        this.paragraphs = paragraphs;
        this.sentences = sentences;
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
        this.setText("")
        if (this.onSpeakCallback) {
            this.onSpeakCallback("", -1);
        }        
    }

    nextSentence() {
        if (this.currentIndex < this.sentences.length - 1) {
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
            const nextSentenceIndex = this.sentences.findIndex((_, i) => i > this.currentIndex && this.findParagraphIndex(i) === nextParaIndex);
            this.pause();
            this.speak(nextSentenceIndex);
        }
    }

    prevParagraph() {
        const currentParaIndex = this.findParagraphIndex(this.currentIndex);
        if (currentParaIndex > 0) {
            const prevParaIndex = currentParaIndex - 1;
            const prevSentenceIndex = this.sentences.slice(0, this.currentIndex).reverse().findIndex((_, i) => this.findParagraphIndex(this.currentIndex - i) === prevParaIndex);
            this.pause();
            this.speak(this.currentIndex - prevSentenceIndex - 1);
        }
    }

    setOnSpeakCallback(callback) {
        this.onSpeakCallback = callback;
    }

    speak(index) {
        console.log('speak', index);
        if (index >= 0 && index < this.sentences.length) {
            this.currentIndex = index;
            const text = this.sentences[index];
            
            if (this.onSpeakCallback) {
                this.onSpeakCallback(text, index);
            }

            this.utterance = new SpeechSynthesisUtterance(text);
            this.utterance.lang = this.lang;
            this.utterance.rate = 1.2; // later

            this.utterance.onend = () => {
                if (this.isPlaying && this.currentIndex < this.sentences.length - 1) {
                    this.speak(this.currentIndex + 1);
                } else {
                    this.isPlaying = false;
                }
            };

            window.speechSynthesis.speak(this.utterance);
            console.log('speak', text);
            this.isPlaying = true;
        } else {
            console.log(this.t('viewMarkdown.noTextSelected'));
        }
    }

    findParagraphIndex(sentenceIndex) {
        let total = 0;
        for (let i = 0; i < this.paragraphs.length; i++) {
            const paraLength = this.textSplitter.splitParagraphIntoSentences(this.paragraphs[i]).length;
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
        const canGoNextSentence = this.currentIndex < this.sentences.length - 1;

        return {
            isPlaying: this.isPlaying,
            currentIndex: this.currentIndex,
            sentencesCount: this.sentences.length,
            currentSentence: this.sentences[this.currentIndex] || '',
            currentParagraph: currentParaIndex,
            canGoNextPara: canGoNextPara,
            canGoPrevPara: canGoPrevPara,
            canGoNextSentence: canGoNextSentence,
            canGoPrevSentence: canGoPrevSentence,
        };
    }
}
