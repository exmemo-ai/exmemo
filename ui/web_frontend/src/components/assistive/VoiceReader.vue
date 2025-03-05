<template>
  <el-container style="display: flex; flex-direction: column;">
    <div class="header-buttons" style="display: flex;">
      <el-button @click="handleTTS">{{ $t('convertToSpeech') }}</el-button>
      <el-button @click="doProcess('polish')">{{ $t('polish') }}</el-button>
      <el-button @click="doProcess('gpt')">{{ $t('gpt') }}</el-button>
      <el-button @click="doProcess('translate')">{{ $t('translateToChinese') }}</el-button>
    </div>
    <el-input v-model="textarea_value" type="textarea" :rows="8" :placeholder="$t('inputTextPlaceholder')"
      style="width: 100%; margin-top: 10px;"></el-input>
    
    <div v-if="showPlayer" class="player-container">
      <TextSpeakPlayer
        :text="textarea_value"
        :lang="getLocale()"
        :getContentCallback="getContent"
        ref="speakerPlayer"
      />
    </div>
  </el-container>
</template>

<script>
import { ref, onMounted } from 'vue';
import { getURL, parseBackendError } from '@/components/support/conn';
import TextSpeakPlayer from '@/components/manager/TextPlayer.vue'
import { getLocale } from '@/main.js'
import axios from 'axios';

export default {
  components: {
    TextSpeakPlayer
  },
  setup() {
    const textarea_value = ref('');
    const showPlayer = ref(false);
    const speakerPlayer = ref(null);

    const getContent = () => {
      return textarea_value.value;
    };

    return {
      textarea_value,
      showPlayer,
      speakerPlayer,
      getContent,
      getLocale
    };
  },
  methods: {
    handleTTS() {
      if (this.textarea_value === '') {
        this.$message({
          message: this.$t('pleaseEnterText'),
          type: 'warning'  
        });
        return;
      }
      this.showPlayer = true;
    },

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
          this.textarea_value = res.data.info;
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

<style scoped>
.player-container {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>
