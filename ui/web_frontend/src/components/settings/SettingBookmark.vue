<template>
    <el-form>
        <div class="settings-section">
            <div class="settings-section-header">
                {{ $t('settings.bookmark') }}
            </div>
            <div class="settings-section-content">
              <el-form-item :label="$t('settings.bookmarkDownloadWeb')">
                <el-switch v-model="bookmark_download_web" />
              </el-form-item>
            </div>
        </div>
    </el-form>
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
