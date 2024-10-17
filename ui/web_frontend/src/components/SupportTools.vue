<template>
  <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
    <el-container>
      <h3 style="text-align: left;">{{ $t('toolTitle') }}</h3>
      <div style="display: flex; align-items: center; justify-content: flex-end; margin-left: auto; max-width: 100%;">
        <el-label type="text" v-if="isLogin" style="margin-right: 5px;">{{ login_user }}</el-label>
        <el-button type="text" @click="logoutFunc" v-if="isLogin">{{ $t('logout') }}</el-button>
        <el-button type="text" @click="loginFunc" v-else>{{ $t('login') }}</el-button>
        <el-button @click="gotoUserSetting" v-if="isLogin">{{ $t('userSetting') }}</el-button>
      </div>
    </el-container>
    <el-container>
      <el-header class="custom-padding">
        <div class="header-buttons" style="float: right;">
          <el-button @click="gotoDataManager">{{ $t('dataManager') }}</el-button>
        </div>
      </el-header>
    </el-container>

    <el-container>
      <h4 style="text-align: left;">{{ $t('paperAnalysis') }}</h4>
    </el-container>
    <el-container>
      <el-main class="custom-padding">
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
      </el-main>
    </el-container>

    <el-container>
      <h4 style="text-align: left;">{{ $t('webTools') }}</h4>
    </el-container>

    <el-container>
      <el-main class="custom-padding">
        <div style="display: flex;margin: 5px;">
          <div style="flex-shrink: 1;margin: 5px;">
            <el-label>{{ $t('webAddress') }}</el-label>
          </div>
          <div style="flex-grow: 1;margin: 5px;">
            <el-input v-model="web_addr" placeholder="http://"></el-input>
          </div>
          <div style="flex-shrink: 1;margin: 5px;">
            <el-button @click="getWebContent">{{ $t('getWebContent') }}</el-button>
          </div>
          <div style="flex-shrink: 1;margin: 5px;">
            <el-button @click="getWebAbstract">{{ $t('getWebAbstract') }}</el-button>
          </div>
          <div style="flex-shrink: 1;margin: 5px;">
            <el-button @click="getWebSave">{{ $t('saveWeb') }}</el-button>
          </div>
        </div>
        <div style="margin: 5px;">
          <pre class="file-content">{{ web_info }}</pre>
        </div>
      </el-main>
    </el-container>


    <el-container>
      <h4 style="text-align: left;">{{ $t('voiceReading') }}</h4>
    </el-container>

    <el-main class="custom-padding">
      <div style="display: flex;">
        <div style="flex-shrink: 1;margin: 5px;">
          <el-button @click="doProcess('tts')">{{ $t('convertToSpeech') }}</el-button>
        </div>
        <div style="flex-shrink: 1;margin: 5px;">
          <el-button @click="doProcess('polish')">{{ $t('polish') }}</el-button>
        </div>
        <div style="flex-shrink: 1;margin: 5px;">
          <el-button @click="doProcess('gpt')">{{ $t('gpt') }}</el-button>
        </div>
        <div style="flex-shrink: 1;margin: 5px;">
          <el-button @click="doProcess('translate')">{{ $t('translateToChinese') }}</el-button>
        </div>
      </div>

      <el-input v-model="textarea_value" type="textarea" :rows="8" :placeholder="$t('inputTextPlaceholder')"
        style="width: 100%;"></el-input>

      <div style="margin-top: 10px;">
        <audio ref="audioPlayer" :src="audioSrc" @timeupdate="updateProgress"></audio>
        <el-slider v-model="progress" :max="duration" @change="changeProgress"></el-slider>
        <el-button type="primary" @click="playAudio">{{ $t('play') }}</el-button>
        <el-button type="primary" @click="pauseAudio">{{ $t('pause') }}</el-button>
      </div>
    </el-main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { getURL, checkLogin, realLoginFunc, realLogoutFunc, parseBackendError, gotoDataPage, gotoSetting } from './conn'
import axios from 'axios';

export default {
  data() {
    return {
      isMobile: false,
      isLogin: true,
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
    getWebContent() {
      this.webTools('content')
    },
    getWebAbstract() {
      this.webTools('abstract')
    },
    getWebSave() {
      this.webTools('save')
    },
    gotoUserSetting() {
      gotoSetting(this);
    },
    gotoDataManager() {
      gotoDataPage(this);
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
    loginFunc() {
      realLoginFunc(this);
    },
    logoutFunc() {
      realLogoutFunc(this);
    },
  },
  mounted() {
    checkLogin(this);
    this.isMobile = window.innerWidth < 768;
  },
}
</script>

<style>
.file-content {
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>