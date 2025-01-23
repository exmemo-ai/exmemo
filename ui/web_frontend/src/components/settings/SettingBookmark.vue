<template>
  <div class="section-content">
    <el-form>
      <el-form-item :label="$t('settings.bookmarkDownloadWeb')">
        <el-switch v-model="bookmark_download_web" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n';

export default {
  name: 'SettingBookmark',
  setup() {
    const { t } = useI18n();
    return { t };
  },
  data() {
    return {
      bookmark_download_web: false
    }
  },
  methods: {
    updateSettings(settings) {
      this.bookmark_download_web = settings.bookmark_download_web;
    },
    getSettings() {
      return {
        bookmark_download_web: this.bookmark_download_web
      }
    }
  }
}
</script>
