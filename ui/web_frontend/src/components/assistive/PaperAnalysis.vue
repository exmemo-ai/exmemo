<template>
  <el-container style="display: flex; flex-direction: column;">
    <div class="header-buttons">
      <el-text>{{ $t('paperInfo') }}</el-text>
      <el-input v-model="search_text" :placeholder="$t('paperPlaceholder')" />
      <el-button class="icon-button" @click="searchPaper">
        <el-icon>
          <Search />
        </el-icon>
      </el-button>
    </div>
    <div style="margin: 5px;">
      <pre class="file-content">{{ info_content }}</pre>
    </div>
  </el-container>
</template>

<script>
import { getURL, parseBackendError } from '@/components/support/conn'
import axios from 'axios';
import { Search } from '@element-plus/icons-vue'


export default {
  components: {
    Search,
  },
  data() {
    return {
      search_text: '',
      info_content: '',
    };
  },
  methods: {
    searchPaper() {
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
      axios.post(getURL() + 'api/paper/', formData).then((res) => {
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
    }
  }
}
</script>

<style scoped>
.header-buttons {
  display: flex;
  align-items: center;
  padding: 10px 0;
  flex-wrap: nowrap;
  min-width: 0;
  gap: 8px;
}

.el-text {
  white-space: nowrap;
  flex-shrink: 0;
}

:deep(.el-input) {
  flex: 1;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.input-group label {
  white-space: nowrap;
}

.file-content {
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
}

:deep(.el-form-item) {
  margin-right: 0;
}

:deep(.el-form-item__content) {
  margin-right: 0 !important;
}

</style>
