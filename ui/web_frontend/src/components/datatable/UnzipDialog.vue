<template>
  <el-dialog
    v-model="dialogVisible"
    :title="$t('compress.unzipSettings')"
    width="30%"
  >
    <div class="unzip-options">
      <el-checkbox v-model="unzip">{{ $t('compress.wantUnzip') }}</el-checkbox>
      <el-checkbox v-model="createSubDir" :disabled="!unzip">
        {{ $t('compress.createSubDir') }}
      </el-checkbox>
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

<script>
export default {
  data() {
    return {
      dialogVisible: false,
      unzip: false,
      createSubDir: true
    }
  },
  methods: {
    show() {
      this.dialogVisible = true
      return new Promise((resolve) => {
        this.resolvePromise = resolve
      })
    },
    confirm() {
      this.dialogVisible = false
      this.resolvePromise?.({
        unzip: this.unzip,
        createSubDir: this.createSubDir
      })
    },
    cancel() {
      this.dialogVisible = false
      this.resolvePromise?.({
        unzip: false,
        createSubDir: false
      })
    }
  }
}
</script>

<style scoped>
.unzip-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
</style>
