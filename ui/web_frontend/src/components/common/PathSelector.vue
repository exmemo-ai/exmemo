<template>
  <div class="path-selector">
    <template v-if="etype === 'note'">
      <div class="form-item">
        <div class="path-header">
          <span>{{ $t('tree.vault') }}</span>
          <el-radio-group v-model="vaultInputType" size="small">
            <el-radio-button label="manual">{{ $t('tree.manualInput') }}</el-radio-button>
            <el-radio-button label="select">{{ $t('tree.select') }}</el-radio-button>
          </el-radio-group>
        </div>
        <el-input 
          v-if="vaultInputType === 'manual'"
          v-model="localVault" 
          :placeholder="$t('tree.enterVaultName')"
          @update:modelValue="handleVaultChange"
        />
        <el-select
          v-else
          v-model="localVault"
          :placeholder="$t('tree.selectVault')"
          clearable
          @change="handleVaultChange"
        >
          <el-option
            v-for="vault in vaultOptions"
            :key="vault.name"
            :label="vault.name"
            :value="vault.name"
          />
        </el-select>
      </div>
      <div class="form-item" v-if="localVault">
        <div class="path-header">
          <span>{{ $t('tree.path') }}</span>
          <el-radio-group v-model="pathInputType" size="small">
            <el-radio-button label="manual">{{ $t('tree.manualInput') }}</el-radio-button>
            <el-radio-button label="select">{{ $t('tree.select') }}</el-radio-button>
          </el-radio-group>
        </div>
        <el-input 
          v-if="pathInputType === 'manual'"
          v-model="localPath" 
          :placeholder="$t('tree.pathOptional')"
          @update:modelValue="handlePathChange"
        />
        <el-cascader
          v-else
          v-model="selectedPath"
          :options="pathOptions"
          :props="cascaderProps"
          :placeholder="$t('tree.selectPath')"
          clearable
          @change="handleCascaderChange"
        />
      </div>
    </template>
    
    <div class="form-item" v-else>
      <div class="path-header">
        <span>{{ $t('tree.path') }}</span>
        <el-radio-group v-model="pathInputType" size="small">
          <el-radio-button label="manual">{{ $t('tree.manualInput') }}</el-radio-button>
          <el-radio-button label="select">{{ $t('tree.select') }}</el-radio-button>
        </el-radio-group>
      </div>
      <el-input 
        v-if="pathInputType === 'manual'"
        v-model="localPath" 
        :placeholder="$t('tree.pathOptional')"
        @update:modelValue="handlePathChange"
      />
      <el-cascader
        v-else
        v-model="selectedPath"
        :options="pathOptions"
        :props="cascaderProps"
        :placeholder="$t('tree.selectPath')"
        clearable
        @change="handleCascaderChange"
      />
    </div>
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
  emitPath: true
}

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
  const pathValue = value ? value.join('/') : ''
  localPath.value = pathValue
  emit('update:path', pathValue)
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

:deep(.el-radio-button__inner) {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid var(--el-border-color-lighter);
  background-color: transparent;
}

:deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 3px 0 0 3px;
}

:deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 3px 3px 0;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  box-shadow: none;
}
</style>
