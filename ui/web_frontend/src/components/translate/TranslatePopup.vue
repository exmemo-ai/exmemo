<template>
  <div v-if="visible"
    :style="{ top: `${position.y}px`, left: `${position.x}px` }"
    class="popup" :class="{ show: visible }">
    <div style="display: flex; flex-direction: column; margin: 5px;">
      <div v-if="isTranslating" class="popup-loading">
        <div class="spinner"></div>
        <p>{{ $t('trans.translating') || 'Translating...' }}</p>
      </div>
      <div v-else>
        <p style="margin-bottom: 8px; white-space: pre-line;">{{ translatedText }}</p>
        <div class="popup-buttons" v-if="!isSentenceMode">
          <el-button type="primary" size="small" @click="translateSentence">
            {{ $t('trans.translateSentence') }}
          </el-button>
          <el-button type="info" size="small" @click="wordInSentence">
            {{ $t('trans.definitionInSentence') }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { translateFunc } from './TransFunction';

export default {
  name: 'TranslatePopup',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    position: {
      type: Object,
      default: () => ({ x: 0, y: 0 })
    }
  },
  data() {
    return {
      translatedText: '',
      isTranslating: false,
      currentWord: '',
      currentElement: null,
      popupTime: null,
      isSentenceMode: false
    };
  },
  methods: {
    translateWord(word, element) {
      this.isTranslating = true;
      this.currentWord = word;
      this.currentElement = element;
      this.isSentenceMode = false;
      const sentence = this.getSentence(element);
      this.translate('word', word, sentence);
    },
    translateSelection(selectedText) {
      this.isTranslating = true;
      this.isSentenceMode = true;
      this.translate('sentence', null, selectedText);
    },
    translate(rtype, word, sentence) {
      this.popupTime = new Date().getTime();
      translateFunc(this, rtype, word, sentence, this.translateCallback);
    },
    translateCallback(info) {
      this.translatedText = info;
      this.isTranslating = false;

      this.$nextTick(() => {
        const popup = document.querySelector('.popup');
        if (popup) {
          popup.classList.add('show');
        }
      });
    },
    wordInSentence() {
      if (!this.currentWord) {
        this.$emit('alert', this.$t('selectWordAlert'));
        return;
      }
      this.isTranslating = true;
      const sentence = this.getSentence(this.currentElement);
      this.translate('word_role', this.currentWord, sentence);
    },
    translateSentence() {
      if (!this.currentElement) return;
      this.isTranslating = true;
      const sentence = this.getSentence(this.currentElement);
      this.translate('sentence', null, sentence);
    },
    getSentence(element) {
      if (!element) return '';
      
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
      return sentence.join(" ");
    },
    issymbol(text) {
      let regex = /[.,;!?]$/;
      return regex.test(text.trim());
    },
    getPopupTime() {
      return this.popupTime || 0;
    }
  }
};
</script>

<style scoped>
.popup {
  margin: 2px;
  position: absolute;
  width: 220px;
  height: auto;
  max-height: 200px;
  background-color: #ffffff;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  padding: 10px;
  overflow: auto;
  transition: opacity 0.3s ease, transform 0.3s ease;
  opacity: 0;
  transform: translateY(-10px);
}

.popup.show {
  opacity: 1;
  transform: translateY(0);
}

.popup-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  justify-content: space-between;
}

.popup-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
