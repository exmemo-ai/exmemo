<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('tree.importNote')"
    width="30%"
  >
    <div class="import-form">
      <div v-if="filesCount > 0" class="file-count-tip">
        {{ $t('tree.importConfirmation', { count: filesCount }) }}
      </div>
      <PathSelector
        v-model:vault="form.vault"
        v-model:path="form.path"
        :etype="form.etype"
      />
      <div v-if="isFolder" class="form-item">
        <el-checkbox v-model="form.overwrite">
          {{ $t('tree.overwriteExisting') }}
        </el-checkbox>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="cancel">{{ $t('cancel') }}</el-button>
        <el-button type="primary" @click="confirm">
          {{ $t('confirm') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { t } from '@/utils/i18n'
import PathSelector from '@/components/common/PathSelector.vue'

const dialogVisible = ref(false)
const form = reactive({
  vault: '',
  path: '',
  overwrite: false,
  etype: 'note'
})
const filesCount = ref(0)
const isFolder = ref(false)
let resolvePromise = null

const show = (is_folder, etype, count = 0) => {
  dialogVisible.value = true
  isFolder.value = is_folder
  form.vault = ''
  form.path = ''
  form.overwrite = !is_folder
  if (etype) {
    form.etype = etype
  }
  filesCount.value = count
  return new Promise((resolve) => {
    resolvePromise = resolve
  })
}

const confirm = () => {
  if (!form.vault) {
    ElMessage.error(t('tree.vaultRequired'))
    return
  }
  dialogVisible.value = false
  resolvePromise?.(form)
}

const cancel = () => {
  dialogVisible.value = false
  resolvePromise?.(null)
}

defineExpose({
  show
})
</script>

<style scoped>
.import-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.file-count-tip {
  margin-bottom: 10px;
  font-size: 14px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item span {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.path-input-group {
  display: flex;
  gap: 8px;
}

.manual-input {
  flex: 3;
}

.path-selector {
  flex: 2;
}
</style>
