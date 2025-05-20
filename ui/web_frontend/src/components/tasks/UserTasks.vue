<template>
  <div class="task-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('task.taskList') }}</span>
          <div class="header-operations">
            <el-button type="danger" size="small" @click="confirmDeleteAll">
              {{ $t('task.deleteAll') }}
            </el-button>
            <el-button type="primary" size="small" @click="refreshTasks">
              <el-icon>
                <Refresh />
              </el-icon>{{ $t('task.refresh') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="tasks.items" v-loading="loading">
        <el-table-column prop="task_name" :label="$t('task.taskName')">
          <template #default="scope">
            {{ $t(`task.${scope.row.task_name}`, scope.row.task_name) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('task.status')">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" :label="$t('task.progress')" width="200">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.progress)" :format="percent => `${percent}%`" />
          </template>
        </el-table-column>
        <el-table-column prop="created_time" :label="$t('task.createdTime')" />
        <el-table-column :label="$t('task.operation')" width="120">
          <template #default="scope">
            <el-tooltip :content="$t('task.deleteRecord')" placement="top">
              <el-icon class="operation-icon" @click="deleteTask(scope.row.task_id)">
                <Delete />
              </el-icon>
            </el-tooltip>
            <el-tooltip v-if="['PENDING', 'STARTED'].includes(scope.row.status)" :content="$t('task.interruptTask')" placement="top">
              <el-icon class="operation-icon" @click="terminateTask(scope.row.task_id)">
                <VideoPause />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="tasks.total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next" @size-change="handleSizeChange"
          @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <el-dialog v-model="deleteConfirmVisible" :title="$t('task.deleteConfirm')" width="30%">
      <span>{{ $t('task.deleteAllConfirm') }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteConfirmVisible = false">{{ $t('cancel') }}</el-button>
          <el-button type="danger" @click="deleteAllTasks">{{ $t('confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, VideoPause, Refresh } from '@element-plus/icons-vue'
import { taskService } from './taskUtils'
import { useI18n } from 'vue-i18n'

const tasks = ref({
  items: [],
  total: 0
})
const loading = ref(false)
const { t } = useI18n()

const getStatusType = (status) => {
  const types = {
    'PENDING': 'info',
    'STARTED': 'warning',
    'SUCCESS': 'success',
    'FAILURE': 'danger'
  }
  return types[status] || ''
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await taskService.getRunningTasks(currentPage.value, pageSize.value)
    tasks.value = {
      items: response.results,
      total: response.count
    }
  } catch (error) {
    console.error('Error fetching tasks:', error)
    ElMessage.error(t('task.taskFetchError'))
  }
  loading.value = false
}

const terminateTask = async (taskId) => {
  try {
    await taskService.terminateTask(taskId)
    ElMessage.success(t('task.taskInterrupted'))
    await fetchTasks()
  } catch (error) {
    console.error('Error terminating task:', error)
    ElMessage.error(t('task.taskTerminateError'))
  }
}

const deleteTask = async (taskId) => {
  try {
    await taskService.deleteTask(taskId)
    ElMessage.success(t('task.taskDeleted'))
    await fetchTasks()
  } catch (error) {
    console.error('Error deleting task:', error)
    ElMessage.error(t('task.taskDeleteError'))
  }
}

const checkTaskTimer = ref(null)
const checkInterval = ref(1000)

const checkTasks = async () => {
  try {
    const response = await taskService.getRunningTasks(currentPage.value, pageSize.value)
    tasks.value = {
      items: response.results,
      total: response.count
    }
    const runningTasks = tasks.value.items.filter(task =>
      ['PENDING', 'STARTED'].includes(task.status)
    )

    if (runningTasks.length === 0 && checkTaskTimer.value) {
      clearInterval(checkTaskTimer.value)
      checkTaskTimer.value = null
      //checkInterval.value = 1000
    } else {
      clearInterval(checkTaskTimer.value)
      //checkInterval.value = Math.min(checkInterval.value * 2, 60000)
      checkTaskTimer.value = setInterval(checkTasks, checkInterval.value)
    }
  } catch (error) {
    console.error('Error checking tasks:', error)
    ElMessage.error(t('task.taskFetchError'))
  }
}

const startTaskCheck = () => {
  if (!checkTaskTimer.value) {
    checkInterval.value = 2000
    checkTaskTimer.value = setInterval(checkTasks, checkInterval.value)
  }
}

const currentPage = ref(1)
const pageSize = ref(10)
const deleteConfirmVisible = ref(false)

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchTasks()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchTasks()
}

const refreshTasks = () => {
  fetchTasks()
  startTaskCheck()
}

const confirmDeleteAll = () => {
  deleteConfirmVisible.value = true
}

const deleteAllTasks = async () => {
  try {
    await taskService.deleteAllCompletedTasks()
    ElMessage.success(t('task.deletedAllCompleted'))
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Error deleting all tasks:', error)
      ElMessage.error(t('task.taskDeleteError'))
    }
  } finally {
    deleteConfirmVisible.value = false
  }
}

onMounted(() => {
  fetchTasks()
  startTaskCheck()
})

onBeforeUnmount(() => {
  if (checkTaskTimer.value) {
    clearInterval(checkTaskTimer.value)
  }
})
</script>

<style scoped>
.task-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-operations {
  display: flex;
  gap: 10px;
}

.operation-icon {
  margin: 0 5px;
  font-size: 18px;
  cursor: pointer;
  color: #606266;
}

.operation-icon:hover {
  color: #409EFF;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
