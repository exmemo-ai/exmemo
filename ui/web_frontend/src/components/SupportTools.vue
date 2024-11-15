<template>
  <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
    <div style="display: flex; flex-direction: column;">
      <app-navbar :title="$t('toolTitle')" :info="'SupportTools'" />
    </div>
    
    <el-container class="main-container">
      <el-aside width="200px" style="background-color: #f5f7fa">
        <el-menu
          :default-active="activeView"
          @select="handleMenuSelect">
          <el-menu-item index="paper">
            <span>{{ $t('paperAnalysis') }}</span>
          </el-menu-item>
          <el-menu-item index="web">
            <span>{{ $t('webTools') }}</span>
          </el-menu-item>
          <el-menu-item index="tts">
            <span>{{ $t('voiceReading') }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main>
        <div v-show="activeView === 'paper'">
          <el-container style="display: flex; flex-direction: column;">
            <div style="display: flex;margin: 5px;">
              <div style="flex-shrink: 1;margin: 5px;">
                <el-label>{{ $t('paperInfo') }}</el-label>
              </div>
              <div style="flex-grow: 1;margin: 5px;">
                <el-input v-model="search_text" :placeholder="$t('paperPlaceholder')"></el-input>
              </div>
              <div style="flex-shrink: 1;margin: 5px;">
                <el-button @click="searchPaper">{{ $t('search') }}</el-button>
              </div>
            </div>
            <div style="margin: 5px;">
              <pre class="file-content">{{ info_content }}</pre>
            </div>
          </el-container>
        </div>

        <div v-show="activeView === 'web'">
          <el-container style="display: flex; flex-direction: column;">
            <div style="display: flex;margin: 5px;">
              <div style="flex-shrink: 1;margin: 5px;">
                <el-label>{{ $t('webAddress') }}</el-label>
              </div>
              <div style="flex-grow: 1;margin: 5px;">
                <el-input v-model="web_addr" placeholder="http://"></el-input>
              </div>
              <div style="flex-shrink: 1;margin: 5px;">
                <el-button @click="getWebContent">{{ $t('getWebContent') }}</el-button>
                <el-button @click="getWebAbstract">{{ $t('getWebAbstract') }}</el-button>
                <el-button @click="getWebSave">{{ $t('saveWeb') }}</el-button>
              </div>
            </div>
            <div style="margin: 5px;">
              <pre class="file-content">{{ web_info }}</pre>
            </div>
          </el-container>
        </div>

        <div v-show="activeView === 'tts'">
          <el-container style="display: flex; flex-direction: column;">
            <div style="display: flex;margin: 5px;">
              <div style="margin: 5px;">
                <el-button @click="doProcess('tts')">{{ $t('convertToSpeech') }}</el-button>
                <el-button @click="doProcess('polish')">{{ $t('polish') }}</el-button>
                <el-button @click="doProcess('gpt')">{{ $t('gpt') }}</el-button>
                <el-button @click="doProcess('translate')">{{ $t('translateToChinese') }}</el-button>
              </div>
            </div>
            <el-input v-model="textarea_value" type="textarea" :rows="8" :placeholder="$t('inputTextPlaceholder')"
              style="width: 100%; margin-top: 10px;"></el-input>
            <div style="margin-top: 10px;">
              <audio ref="audioPlayer" :src="audioSrc" @timeupdate="updateProgress"></audio>
              <el-slider v-model="progress" :max="duration" @change="changeProgress"></el-slider>
              <el-button type="primary" @click="playAudio">{{ $t('play') }}</el-button>
              <el-button type="primary" @click="pauseAudio">{{ $t('pause') }}</el-button>
            </div>
          </el-container>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { getURL, parseBackendError } from './conn'
import axios from 'axios';
import AppNavbar from '@/components/AppNavbar.vue'

export default {
  components: {
    AppNavbar
  },
  data() {
    return {
      isMobile: false,
      isLogin: true,
      activeView: 'paper',
      login_user: '',
      search_text: '',
      info_content: '',
      textarea_value: '',
      web_addr: '',
      web_info: '',
    };
  },
  setup() {
    const audioSrc = ref(getURL() + 'static/audio/xxx.mp3');
    const audioPlayer = ref(null);
    const progress = ref(0);
    const duration = ref(0);

    const playAudio = () => {
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
      playAudio,
      pauseAudio,
      updateProgress,
      changeProgress
    };
  },
  methods: {
    handleMenuSelect(key) {
      this.activeView = key;
    },
    getWebContent() {
      this.webTools('content')
    },
    getWebAbstract() {
      this.webTools('abstract')
    },
    getWebSave() {
      this.webTools('save')
    },
    webTools(rtype) {
      if (this.web_addr === '') {
        this.$message({
          message: this.$t('enterWebAddress'),
          type: 'warning'
        });
        return;
      }
      let func = 'api/web/';
      const formData = new FormData();
      formData.append('content', this.web_addr);
      if (rtype === 'save') {
        func = 'api/entry/data/';
        formData.append('addr', this.web_addr);
        formData.append('etype', 'web');
      }
      formData.append('rtype', rtype)
      axios.post(getURL() + func, formData).then((res) => {
        console.log(res);
        console.log(res.data);
        if (res.data.status == 'success') {
          this.web_info = res.data.info;
          this.$message({
            message: this.$t('operationSuccess'),
            type: 'success'
          });
        }
      }).catch((err) => {
        parseBackendError(this, err);
      });
    },
    searchPaper() {
      console.log('searchPaper');
      if (this.search_text === '') {
        this.$message({
          message: this.$t('enterPaperInfo'),
          type: 'warning'
        });
        return;
      }
      const formData = new FormData();
      formData.append('content', this.search_text);
      formData.append('rtype', 'search')
      console.log(getURL())
      console.log(formData)
      axios.post(getURL() + 'api/paper/', formData).then((res) => {
        console.log(res);
        console.log(res.data);
        if (res.data.status == 'success') {
          this.info_content = res.data.info;
          this.$message({
            message: this.$t('searchSuccess'),
            type: 'success'
          });
        }
      }).catch((err) => {
        parseBackendError(this, err);
      });
    },
    doProcess(rtype) {
      console.log('doProcess ' + rtype);
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
      if (rtype === 'polish') {
        formData.append('rtype', 'polish')
      } else if (rtype === 'translate') {
        formData.append('rtype', 'translate')
      } else if (rtype === 'gpt') {
        formData.append('rtype', 'gpt')
      } else {
        console.log('rtype error' + rtype);
      }
      axios.post(getURL() + 'api/paper/', formData).then((res) => {
        console.log(res);
        console.log(res.data);
        if (res.data.status == 'success') {
          if (rtype === 'polish') {
            this.textarea_value = res.data.info;
          } else if (rtype === 'translate') {
            this.textarea_value = res.data.info;
          } else if (rtype === 'gpt') {
            this.textarea_value = res.data.info;
          } else if (rtype === 'tts') {
            this.audioSrc = getURL() + res.data.audio_url;
            this.$refs.audioPlayer.load();
            //this.playAudio();
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
    },
    convertTTS() {
      console.log('convertTTS');
      if (this.textarea_value === '') {
        this.$message({
          message: this.$t('pleaseEnterText'),
          type: 'warning'
        });
        return;
      }
      const formData = new FormData();
      formData.append('content', this.textarea_value);
      formData.append('rtype', 'tts')
      axios.post(getURL() + 'api/paper/', formData).then((res) => {
        console.log(res);
        console.log(res.data);
        if (res.data.status == 'success') {
          this.audioSrc = getURL() + res.data.audio_url;
          this.$refs.audioPlayer.load();
          this.$message({
            message: this.$t('conversionSuccess'),
            type: 'success'
          });
          //this.playAudio();
        } else {
          this.$message({
            message: res.data.info,
            type: 'success'
          });
        }
      }).catch((err) => {
        parseBackendError(this, err);
      });
    },
  },
  mounted() {
    this.isMobile = window.innerWidth < 768;
  },
}
</script>

<style>
.main-container {
  height: calc(100vh - 60px);
}

.file-content {
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.el-aside {
  border-right: 1px solid #e6e6e6;
}
</style>