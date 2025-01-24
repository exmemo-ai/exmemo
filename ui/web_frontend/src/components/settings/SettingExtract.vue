<template>
  <div class="section-content">
    <el-form class="compact-form">
      <h3>{{ $t('settings.batchSetting') }}</h3>
      <el-form-item :label="$t('settings.batchUseLLM')">
        <el-switch v-model="batch_use_llm" />
      </el-form-item>

      <h3>{{ $t('settings.webContent') }}</h3>
      <el-form-item :label="$t('settings.saveContent')">
        <el-switch v-model="web_save_content" />
      </el-form-item>
      <el-form-item :label="$t('settings.getCategory')">
        <el-switch v-model="web_get_category" />
      </el-form-item>
      <el-form-item :label="$t('settings.getAbstract')">
        <el-switch v-model="web_get_abstract" />
      </el-form-item>

      <h3>{{ $t('settings.fileContent') }}</h3>
      <el-form-item :label="$t('settings.saveContent')">
        <el-switch v-model="file_save_content" />
      </el-form-item>
      <el-form-item :label="$t('settings.getCategory')">
        <el-switch v-model="file_get_category" />
      </el-form-item>
      <el-form-item :label="$t('settings.getAbstract')">
        <el-switch v-model="file_get_abstract" />
      </el-form-item>

      <h3>{{ $t('settings.noteContent') }}</h3>
      <el-form-item :label="$t('settings.saveContent')">
        <el-switch v-model="note_save_content" />
      </el-form-item>
      <el-form-item :label="$t('settings.getCategory')">
        <el-switch v-model="note_get_category" />
      </el-form-item>
      <el-form-item :label="$t('settings.getAbstract')">
        <el-switch v-model="note_get_abstract" />
      </el-form-item>

      <h3>{{ $t('settings.truncateSettings') }}</h3>
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
    </el-form>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n';

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
  methods: {
    updateSettings(settings) {
      this.batch_use_llm = settings.batch_use_llm;
      this.web_save_content = settings.web_save_content;
      this.web_get_category = settings.web_get_category;
      this.web_get_abstract = settings.web_get_abstract;
      this.file_save_content = settings.file_save_content;
      this.file_get_category = settings.file_get_category;
      this.file_get_abstract = settings.file_get_abstract;
      this.note_save_content = settings.note_save_content;
      this.note_get_category = settings.note_get_category;
      this.note_get_abstract = settings.note_get_abstract;
      this.truncate_content = settings.truncate_content;
      this.truncate_max_length = settings.truncate_max_length;
      this.truncate_mode = settings.truncate_mode;
    },
    getSettings() {
      return {
        batch_use_llm: this.batch_use_llm,
        web_save_content: this.web_save_content,
        web_get_category: this.web_get_category,
        web_get_abstract: this.web_get_abstract,
        file_save_content: this.file_save_content,
        file_get_category: this.file_get_category,
        file_get_abstract: this.file_get_abstract,
        note_save_content: this.note_save_content,
        note_get_category: this.note_get_category,
        note_get_abstract: this.note_get_abstract,
        truncate_content: this.truncate_content,
        truncate_max_length: this.truncate_max_length,
        truncate_mode: this.truncate_mode
      }
    }
  }
}
</script>

<style scoped>
.compact-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.compact-form h3 {
  margin: 16px 0 8px 0;
}

.compact-form h3:first-child {
  margin-top: 0;
}
</style>
