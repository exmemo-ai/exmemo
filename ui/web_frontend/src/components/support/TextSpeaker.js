export class TextSpeaker {
    constructor(lang) {
        this.lang = lang;
        this.isSpeaking = false;
        this.isPaused = false;
        this.currentIndex = 0;
        this.sentences = [];
        this.utterance = null;
    }

    splitText(text) {
        // 按句号、问号、感叹号和换行符分割文本
        return text.match(/[^。！？\n]+[。！？\n]|[^。！？\n]+$/g) || [text];
    }

    speak(text) {
        if (this.isSpeaking) {
            this.stop();
        }

        this.sentences = this.splitText(text);
        console.log('Sentences:', this.sentences.length);
        this.currentIndex = 0;
        this.isSpeaking = true;
        this.speakNext();
    }

    speakNext() {
        if (!this.isSpeaking || this.isPaused || this.currentIndex >= this.sentences.length) {
            this.isSpeaking = false;
            return;
        }

        this.utterance = new SpeechSynthesisUtterance(this.sentences[this.currentIndex]);
        this.utterance.lang = this.lang;
        
        this.utterance.onend = () => {
            this.currentIndex++;
            this.speakNext();
        };

        this.utterance.onerror = (event) => {
            console.error('TTS error:', event);
            this.currentIndex++;
            this.speakNext();
        };

        console.log('Speaking:', this.currentIndex + 1, this.sentences[this.currentIndex]);
        window.speechSynthesis.speak(this.utterance);
    }

    pause() {
        if (this.isSpeaking) {
            this.isPaused = true;
            window.speechSynthesis.pause();
        }
    }

    resume() {
        if (this.isSpeaking && this.isPaused) {
            this.isPaused = false;
            window.speechSynthesis.resume();
        }
    }

    stop() {
        this.isSpeaking = false;
        this.isPaused = false;
        this.currentIndex = 0;
        this.sentences = [];
        window.speechSynthesis.cancel();
    }

    getStatus() {
        return {
            isSpeaking: this.isSpeaking,
            isPaused: this.isPaused,
            progress: {
                current: this.currentIndex + 1,
                total: this.sentences.length
            }
        };
    }
}
