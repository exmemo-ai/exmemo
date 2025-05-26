<template>
  <div class="path-selector">
    <template v-if="etype === 'note'">
      <div class="form-item">
        <div class="path-header">
          <span>{{ $t('tree.vault') }}</span>
        </div>
        <div class="input-group">
          <el-input
            v-model="localVault"
            :placeholder="$t('tree.enterVaultName')"
            @update:modelValue="handleVaultChange"
          />
          <el-button @click="showVaultSelect = true">
            {{ $t('tree.select') }}
          </el-button>
        </div>
      </div>
      <div class="form-item" v-if="localVault">
        <div class="path-header">
          <span>{{ $t('tree.path') }}</span>
        </div>
        <div class="input-group">
          <el-input
            v-model="localPath"
            :placeholder="$t('tree.pathOptional')"
            @update:modelValue="handlePathChange"
          />
          <el-button @click="showPathSelect = true">
            {{ $t('tree.select') }}
          </el-button>
        </div>
      </div>
    </template>
    
    <div class="form-item" v-else>
      <div class="path-header">
        <span>{{ $t('tree.path') }}</span>
      </div>
      <div class="input-group">
        <el-input
          v-model="localPath"
          :placeholder="$t('tree.pathOptional')"
          @update:modelValue="handlePathChange"
        />
        <el-button @click="showPathSelect = true">
          {{ $t('tree.select') }}
        </el-button>
      </div>
    </div>

    <el-dialog
      v-model="showVaultSelect"
      :title="$t('tree.selectVault')"
      :width="dialogWidth"
    >
      <el-select
        v-model="localVault"
        :placeholder="$t('tree.selectVault')"
        style="width: 100%"
        @change="handleVaultSelectConfirm"
      >
        <el-option
          v-for="vault in vaultOptions"
          :key="vault.name"
          :label="vault.name"
          :value="vault.name"
        />
      </el-select>
    </el-dialog>

    <el-dialog
      v-model="showPathSelect"
      :title="$t('tree.selectPath')"
      :width="dialogWidth"
    >
      <el-cascader
        v-if="showPathSelect"
        v-model="selectedPath"
        :options="pathOptions"
        :props="cascaderProps"
        style="width: 100%"
        @expand-change="handleExpandChange"
        @change="handleCascaderConfirm"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue'
import { getDir } from '../datatree/apiUtils'

const props = defineProps({
  vault: String,
  path: String,
  etype: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:vault', 'update:path'])

const vaultInputType = ref('manual')
const pathInputType = ref('manual')
const localVault = ref(props.vault || '')
const localPath = ref(props.path || '')
const selectedPath = ref([])
const vaultOptions = ref([])
const pathOptions = ref([])
const currentVaultNode = ref(null)

const cascaderProps = {
  value: 'name',
  label: 'name',
  children: 'children',
  checkStrictly: true,
  emitPath: true,
  multiple: false,
  expandTrigger: 'click'
}

const showVaultSelect = ref(false)
const showPathSelect = ref(false)
const dialogWidth = ref(window.innerWidth <= 768 ? '70%' : '30%')

window.addEventListener('resize', () => {
  dialogWidth.value = window.innerWidth <= 768 ? '70%' : '30%'
})

watch(() => props.etype, async (newEtype) => {
  if (!newEtype) return
  
  const dirlist = await getDir(newEtype)
  if (newEtype === 'note') {
    vaultOptions.value = Object.values(dirlist?.children || {}).map(node => ({
      name: node.name,
      children: node.children
    }))
    vaultInputType.value = vaultOptions.value.length > 0 ? 'select' : 'manual'
    pathOptions.value = []
  } else {
    pathOptions.value = processDirectoryTree(dirlist)
    pathInputType.value = pathOptions.value.length > 0 ? 'select' : 'manual'
    localVault.value = ''
    vaultOptions.value = []
  }
}, { immediate: true })

watch(() => props.vault, (newVault) => {
  if (newVault !== localVault.value) {
    localVault.value = newVault || ''
  }
})

watch(() => props.path, (newPath) => {
  if (newPath !== localPath.value) {
    localPath.value = newPath || ''
  }
})

const processDirectoryTree = (tree) => {
  if (!tree || !tree.children) return []
  return Object.values(tree.children).map(node => ({
    name: node.name,
    children: node.isFile ? [] : Object.values(node.children).length > 0 ? processDirectoryTree(node) : undefined
  }))
}

const handleVaultChange = (value) => {
  emit('update:vault', value)
  if (!value) {
    currentVaultNode.value = null
    pathOptions.value = []
    localPath.value = ''
    selectedPath.value = []
    emit('update:path', '')
    return
  }
  
  const selectedVault = vaultOptions.value.find(v => v.name === value)
  currentVaultNode.value = selectedVault
  pathOptions.value = selectedVault ? processDirectoryTree(selectedVault) : []
  pathInputType.value = pathOptions.value.length > 0 ? 'select' : 'manual'
}

const handlePathChange = (value) => {
  emit('update:path', value)
}

const handleCascaderChange = (value) => {
  let selectedPathValue = value ? value.join('/') : ''
  if (selectedPathValue && !selectedPathValue.endsWith('/')) {
    selectedPathValue += '/'
  }
  
  if (localPath.value) {
    const pathParts = localPath.value.split('/')
    const lastPart = pathParts[pathParts.length - 1]
    
    if (lastPart && lastPart.length > 0) {
      selectedPathValue = selectedPathValue ? `${selectedPathValue}${lastPart}` : lastPart
    }
  }
  
  localPath.value = selectedPathValue
  emit('update:path', selectedPathValue)
}

const handleVaultSelectConfirm = (value) => {
  handleVaultChange(value)
  showVaultSelect.value = false
}

const handleExpandChange = () => {
  // 防止展开时自动关闭对话框
}

const handleCascaderConfirm = (value) => {
  if (!value) return
  handleCascaderChange(value)
  showPathSelect.value = false
}
</script>

<style scoped>
.path-selector {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.path-header span {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.input-group {
  display: flex;
  gap: 8px;
}

.input-group .el-input {
  flex: 1;
}

:deep(.el-dialog__body) {
  padding: 20px;
}
</style>
