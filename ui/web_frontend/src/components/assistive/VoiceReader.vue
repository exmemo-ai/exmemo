<template>
  <el-container style="display: flex; flex-direction: column;">
    <div class="header-buttons" style="display: flex;">
      <el-button @click="doProcess('tts')">{{ $t('convertToSpeech') }}</el-button>
      <el-button @click="doProcess('polish')">{{ $t('polish') }}</el-button>
      <el-button @click="doProcess('gpt')">{{ $t('gpt') }}</el-button>
      <el-button @click="doProcess('translate')">{{ $t('translateToChinese') }}</el-button>
    </div>
    <el-input v-model="textarea_value" type="textarea" :rows="8" :placeholder="$t('inputTextPlaceholder')"
      style="width: 100%; margin-top: 10px;"></el-input>
    <div style="margin-top: 10px;">
      <audio ref="audioPlayer" :src="audioSrc" @timeupdate="updateProgress"></audio>
      <el-slider v-model="progress" :max="duration" @change="changeProgress"></el-slider>
      <el-button type="primary" @click="playAudio" :disabled="!hasAudio">{{ $t('play') }}</el-button>
      <el-button type="primary" @click="pauseAudio" :disabled="!hasAudio">{{ $t('pause') }}</el-button>
    </div>
  </el-container>
</template>

<script>
import { ref, onMounted } from 'vue';
import { getURL, parseBackendError } from '@/components/support/conn';
import axios from 'axios';

export default {
  data() {
    return {
      textarea_value: '',
    };
  },
  setup() {
    const audioSrc = ref('');
    const audioPlayer = ref(null);
    const progress = ref(0);
    const duration = ref(0);
    const hasAudio = ref(false);

    const playAudio = () => {
      if (!hasAudio.value) {
        console.log('No audio to play');
        return;
      }
      audioPlayer.value.play();
    };

    const pauseAudio = () => {
      audioPlayer.value.pause();
    };

    const updateProgress = () => {
      progress.value = audioPlayer.value.currentTime;
    };

    const changeProgress = (value) => {
      audioPlayer.value.currentTime = value;
    };

    onMounted(() => {
      audioPlayer.value.onloadedmetadata = () => {
        duration.value = audioPlayer.value.duration;
      };
    });

    return {
      audioSrc,
      audioPlayer,
      progress,
      duration,
      hasAudio,
      playAudio,
      pauseAudio,
      updateProgress,
      changeProgress
    };
  },
  methods: {
    doProcess(rtype) {
      if (this.textarea_value === '') {
        this.$message({
          message: this.$t('pleaseEnterText'),
          type: 'warning'
        });
        return;
      }
      const formData = new FormData();
      formData.append('content', this.textarea_value);
      formData.append('rtype', rtype)

      axios.post(getURL() + 'api/paper/', formData).then((res) => {
        if (res.data.status == 'success') {
          if (rtype === 'tts') {
            this.audioSrc = getURL() + res.data.audio_url;
            this.$refs.audioPlayer.load();
            this.hasAudio = true;
          } else {
            this.textarea_value = res.data.info;
          }
          this.$message({
            message: this.$t('operationSuccess'),
            type: 'success'
          });
        } else {
          this.$message({
            message: this.$t('operationFailed') + ': ' + res.data.info,
            type: 'error'
          });
        }
      }).catch((err) => {
        parseBackendError(this, err);
      });
    }
  }
}
</script>
