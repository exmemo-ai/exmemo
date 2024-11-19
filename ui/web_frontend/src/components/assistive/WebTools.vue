<template>
  <el-container style="display: flex; flex-direction: column;">
    <div gap="5px" class="header-buttons" style="display: flex; align-items: center;">
      <div style="flex-shrink: 1;">
        <el-label>{{ $t('webAddress') }}</el-label>
      </div>
      <div style="flex-grow: 1;">
        <el-input v-model="web_addr" placeholder="http://"></el-input>
      </div>
      <div style="flex-shrink: 1;">
        <el-button @click="getWebContent">{{ $t('getWebContent') }}</el-button>
        <el-button @click="getWebAbstract">{{ $t('getWebAbstract') }}</el-button>
        <el-button @click="getWebSave">{{ $t('saveWeb') }}</el-button>
      </div>
    </div>
    <div style="margin: 5px;">
      <pre class="file-content">{{ web_info }}</pre>
    </div>
  </el-container>
</template>

<script>
import { getURL, parseBackendError } from '@/components/support/conn'
import axios from 'axios';

export default {
  name: 'WebTools',
  data() {
    return {
      web_addr: '',
      web_info: '',
    }
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
    }
  }
}
</script>

<style>
.file-content {
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
