<template>
    <el-form>
        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('settings.batchSetting') }}
          </div>
          <div class="settings-section-content">
            <el-form-item :label="$t('settings.batchUseLLM')">
              <el-switch v-model="batch_use_llm" />
            </el-form-item>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('settings.webContent') }}
          </div>
          <div class="settings-section-content">
            <el-form-item :label="$t('settings.saveContent')">
              <el-switch v-model="web_save_content" />
            </el-form-item>
            <el-form-item :label="$t('settings.getCategory')">
              <el-switch v-model="web_get_category" />
            </el-form-item>
            <el-form-item :label="$t('settings.getAbstract')">
              <el-switch v-model="web_get_abstract" />
            </el-form-item>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('settings.fileContent') }}
          </div>
          <div class="settings-section-content">
            <el-form-item :label="$t('settings.saveContent')">
              <el-switch v-model="file_save_content" />
            </el-form-item>
            <el-form-item :label="$t('settings.getCategory')">
              <el-switch v-model="file_get_category" />
            </el-form-item>
            <el-form-item :label="$t('settings.getAbstract')">
              <el-switch v-model="file_get_abstract" />
            </el-form-item>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('settings.noteContent') }}
          </div>
          <div class="settings-section-content">
            <el-form-item :label="$t('settings.saveContent')">
              <el-switch v-model="note_save_content" />
            </el-form-item>
            <el-form-item :label="$t('settings.getCategory')">
              <el-switch v-model="note_get_category" />
            </el-form-item>
            <el-form-item :label="$t('settings.getAbstract')">
              <el-switch v-model="note_get_abstract" />
            </el-form-item>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
              {{ $t('settings.truncateSettings') }}
          </div>
          <div class="settings-section-content">
            <div class="section-description">
              {{ $t('settings.truncateDesc') }}
            </div>
            <el-form-item :label="$t('settings.truncateContent')">
              <el-switch v-model="truncate_content" />
            </el-form-item>
            <el-form-item :label="$t('settings.truncateMaxLength')">
              <el-input-number 
                v-model="truncate_max_length" 
                :min="100" 
                :max="10000"
                :disabled="!truncate_content"
              />
            </el-form-item>
            <el-form-item :label="$t('settings.truncateMode')">
              <el-select 
                v-model="truncate_mode"
                :disabled="!truncate_content"
              >
                <el-option :label="$t('settings.truncateFirst')" value="first" />
                <el-option :label="$t('settings.truncateTitleContent')" value="title_content" />
                <el-option :label="$t('settings.truncateFirstLast')" value="first_last" />
              </el-select>
            </el-form-item>            
          </div>
        </div>

    </el-form>
</template>

<script>
import { useI18n } from 'vue-i18n';
import { watch } from 'vue';
import SettingService from '@/components/settings/settingService';

export default {
  name: 'SettingExtract',
  setup() {
    const { t } = useI18n();
    return { t };
  },
  data() {
    return {
      batch_use_llm: false,
      web_save_content: false,
      web_get_category: true,
      web_get_abstract: false,
      file_save_content: false,
      file_get_category: true,
      file_get_abstract: false,
      note_save_content: true,
      note_get_category: true,
      note_get_abstract: false,
      truncate_content: true,
      truncate_max_length: 1024,
      truncate_mode: 'first'
    }
  },
  async created() {
    const settings = await SettingService.getInstance().loadSetting();
    Object.keys(this.$data).forEach(key => {
      if (settings.setting) {
        if (key in settings.setting) {
          this[key] = settings.setting[key];
        }
      }
    });

    Object.keys(this.$data).forEach(key => {
      watch(
        () => this[key],
        (newVal) => {
          SettingService.getInstance().setSetting(key, newVal);
        }
      );
    });
  }
}
</script>

<style scoped>
.section-description {
  color: #999 !important;
  font-size: 12px;
  margin-bottom: 10px;
}
</style>
