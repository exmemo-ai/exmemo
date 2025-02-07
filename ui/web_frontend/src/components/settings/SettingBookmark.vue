<template>
    <el-form>
        <div class="settings-section">
            <div class="settings-section-header">
                {{ $t('settings.bookmark') }}
            </div>
            <div class="settings-section-content">
              <el-form-item :label="$t('settings.bookmarkDownloadWeb')">
                <el-switch v-model="bookmark_download_web" @change="handleChange"></el-switch>
              </el-form-item>
            </div>
        </div>
    </el-form>
</template>

<script>
import { useI18n } from 'vue-i18n';
import SettingService from '@/components/settings/settingService';

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
  async created() {
    const settings = await SettingService.getInstance().loadSetting();
    this.bookmark_download_web = settings?.setting?.bookmark_download_web || false;
  },
  methods: {
    handleChange() {
      SettingService.getInstance().setSetting("bookmark_download_web", this.bookmark_download_web);
    }
  }
}
</script>
