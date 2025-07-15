<template>
    <div class="app-container">
      <el-container style="flex: 0; width: 100%;">
        <app-navbar ref="navbarRef" :title="t('dataManagement')" :info="'DataManager'" />
      </el-container>
      <el-container style="flex: 1; width: 100%; overflow: hidden;">
        <el-main class="main-container list-options">
            <div class="header-buttons">
                <div class="filter-row">
                    <div class="filter-section">
                        <div class="filter-item">
                            <div class="label-container">
                                <el-text>{{ t('data') }}</el-text>
                            </div>
                            <div class="select-container">
                                <el-select v-if="mounted && etype_options.length" 
                                    v-model="etype_value"
                                    :placeholder="t('selectPlaceholder')"
                                    size="small">
                                    <el-option v-for="item in etype_options" :key="item.value" 
                                        :label="item.label" :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </div>
                    </div>
                    <div class="filter-section">
                        <div class="filter-item">
                            <div class="label-container">
                                <el-text>{{ t('type') }}</el-text>
                            </div>
                            <div class="select-container">
                                <el-select v-if="mounted && ctype_options && ctype_options.length > 0" 
                                    v-model="ctype_value"
                                    :placeholder="t('selectPlaceholder')" 
                                    popper-class="select-dropdown"
                                    size="small">
                                    <el-option v-for="item in ctype_options" :key="item.value" 
                                        :label="item.label" :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </div>
                    </div>
                    <div class="filter-section">
                        <div class="filter-item">
                            <div class="label-container">
                                <el-text>{{ t('status') }}</el-text>
                            </div>
                            <div class="select-container">
                                <el-select v-if="mounted && status_options.length" 
                                    v-model="status_value"
                                    :placeholder="t('selectPlaceholder')"
                                    size="small">
                                    <el-option v-for="item in status_options" :key="item.value" 
                                        :label="item.label" :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="search-row">
                    <div class="date-range-section">
                        <div class="label-container">
                            <el-text>{{ t('datalist.range') }}</el-text>
                        </div>
                        <div class="date-inputs-wrapper">
                            <el-date-picker
                                v-model="dateStart"
                                type="date"
                                :placeholder="t('datalist.startDate')"
                                format="YYYY-MM-DD"
                                value-format="YYYY-MM-DD"
                                size="small"
                            />
                            <el-text>-</el-text>
                            <el-date-picker
                                v-model="dateEnd"
                                type="date"
                                :placeholder="t('datalist.endDate')"
                                format="YYYY-MM-DD"
                                value-format="YYYY-MM-DD"
                                size="small"
                            />
                        </div>
                    </div>
                    
                    <div class="search-controls-row">
                        <div class="search-method-section">
                            <div class="label-container">
                                <el-text>{{ t('datalist.searchMethod') }}</el-text>
                            </div>
                            <div class="select-container">
                                <el-select v-model="searchMethod" :placeholder="t('selectPlaceholder')" size="small">
                                    <el-option
                                        v-for="item in searchMethodOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                    />
                                </el-select>
                            </div>
                        </div>

                        <div class="search-section">
                            <div class="label-container">
                                <el-text>{{ t('search') }}</el-text>
                            </div>
                            <div class="search-input-container">
                                <el-input v-model="search_text" :placeholder="t('searchPlaceholder')" 
                                    @keyup.enter="searchKeyword" size="small"></el-input>
                            </div>
                        </div>                       

                        <div class="action-section">
                            <el-button class="icon-button" @click="searchKeyword" :title="t('datalist.searchButton')">
                                <el-icon><Search /></el-icon>
                            </el-button>
                            <el-button class="icon-button" @click="resetSearchState" :title="t('datalist.resetSearchButton')">
                                <el-icon><RefreshLeft /></el-icon>
                            </el-button>
                            <el-button class="icon-button" @click="openAddDialog" :title="t('datalist.addDataButton')">
                                <el-icon><Plus /></el-icon>
                            </el-button>
                        </div>
                    </div>
                </div>
            </div>
            
            <el-container class="list-width" style="flex: 1; flex-direction: column; width: 100%;">
                <el-table :data="fileList" stripe @row-click="handleRowClick">
                    <el-table-column prop="title" :label="t('title')">
                        <template v-slot="scope">
                            <div class="ellipsis-container nowrap">{{ scope.row.title }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="etype" :label="t('data')" :width=70>
                        <template v-slot="scope">
                            <div class="nowrap">{{ te(scope.row.etype) ? t(scope.row.etype) : scope.row.etype }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="ctype" :label="t('type')" :width=100>
                        <template v-slot="scope">
                            <div class="nowrap">{{ scope.row.ctype }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="updated_time" :label="t('lastUpdated')" :width=100 v-if="!isMobile">
                        <template v-slot="scope">
                            <div class="nowrap">{{ scope.row.updated_time }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="status" :label="t('status')" :width=70 v-if="!isMobile">
                        <template v-slot="scope">
                            <div class="nowrap">{{ te(scope.row.status) ? t(scope.row.status) : scope.row.status }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column :label="t('operation')" width="60" fixed="right" v-if="!isMobile">
                        <template v-slot="scope">
                            <el-icon 
                                class="delete-icon"
                                @click.stop="handleDelete(scope.row)"
                                size="small"
                                :title="t('datalist.deleteButton')"
                            >
                                <el-icon><Delete /></el-icon>
                            </el-icon>
                        </template>
                    </el-table-column>
                </el-table>
                <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                    :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                    layout="total, prev, pager, next" :total="total"
                    class="pagination-container">
                </el-pagination>
            </el-container>
        </el-main>
      </el-container>
      <EditDialog ref="editDialog" />
      <AddDialog ref="addDialog" />
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Search, Plus, Delete, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import EditDialog from './EditDialog.vue'
import AddDialog from './AddDialog.vue'
import { getURL, parseBackendError } from '@/components/support/conn'
import AppNavbar from '@/components/support/AppNavbar.vue'
import { useI18n } from 'vue-i18n'

const { t, te } = useI18n()

// 响应式数据
const mounted = ref(false)
const isMobile = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const status_value = ref(t('all'))
const status_options = ref([])
const ctype_value = ref(t('all'))
const ctype_options = ref([])
const etype_value = ref(t('all'))
const etype_options = ref([])
const search_text = ref('')
const fileList = ref([])
const navbar = ref(null)
const dateStart = ref('')
const dateEnd = ref('')
const searchMethod = ref('keywordOnly')
const STORAGE_KEY = 'dataManager_searchState'

// refs
const editDialog = ref(null)
const addDialog = ref(null)
const navbarRef = ref(null)

// 计算属性
const searchMethodOptions = computed(() => [
    { value: 'keywordOnly', label: t('datalist.keywordOnly') || 'Keyword Only' },
    { value: 'fileSearch', label: t('datalist.fileSearch') || 'File Search' },
    { value: 'tagSearch', label: t('datalist.tagSearch') || 'Tag Search' },
    { value: 'fuzzySearch', label: t('datalist.fuzzySearch') || 'Fuzzy Search' },
    { value: 'embeddingSearch', label: t('datalist.embeddingSearch') || 'Embedding Search' }
])

// 方法
const saveSearchState = () => {
    const searchState = {
        currentPage: currentPage.value,
        search_text: search_text.value,
        etype_value: etype_value.value,
        ctype_value: ctype_value.value,
        status_value: status_value.value,
        dateStart: dateStart.value,
        dateEnd: dateEnd.value,
        searchMethod: searchMethod.value
    }
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(searchState))
    } catch (error) {
        console.warn('Failed to save search state to localStorage:', error)
    }
}

const loadSearchState = () => {
    try {
        const savedState = localStorage.getItem(STORAGE_KEY)
        if (savedState) {
            const searchState = JSON.parse(savedState)
            currentPage.value = searchState.currentPage || 1
            search_text.value = searchState.search_text || ''
            etype_value.value = searchState.etype_value || t('all')
            ctype_value.value = searchState.ctype_value || t('all')
            status_value.value = searchState.status_value || t('all')
            dateStart.value = searchState.dateStart || ''
            dateEnd.value = searchState.dateEnd || ''
            searchMethod.value = searchState.searchMethod || 'keywordOnly'
        }
    } catch (error) {
        console.warn('Failed to load search state from localStorage:', error)
    }
}

const clearSearchState = () => {
    try {
        localStorage.removeItem(STORAGE_KEY)
    } catch (error) {
        console.warn('Failed to clear search state from localStorage:', error)
    }
}

const resetSearchState = () => {
    currentPage.value = 1
    search_text.value = ''
    etype_value.value = t('all')
    ctype_value.value = t('all')
    status_value.value = t('all')
    dateStart.value = ''
    dateEnd.value = ''
    searchMethod.value = 'keywordOnly'
    clearSearchState()
    fetchData()
}

const handleSizeChange = (val) => {
    pageSize.value = val
    fetchData()
}

const handleCurrentChange = (val) => {
    currentPage.value = val
    fetchData()
}

const fetchData = (data = {}) => {
    console.log('##### fetchData')
    let func = 'api/entry/data/'
    let etype_val = etype_value.value === t('all') ? '' : etype_value.value
    let ctype_val = ctype_value.value === t('all') ? '' : ctype_value.value
    let status_val = status_value.value === t('all') ? '' : status_value.value
    let params = {
        keyword: search_text.value,
        etype: etype_val,
        ctype: ctype_val,
        status: status_val,
        page: currentPage.value,
        page_size: pageSize.value,
        start_date: dateStart.value,
        end_date: dateEnd.value,
        method: searchMethod.value
    }
    axios.get(getURL() + func, { params: params })
        .then(response => {
            console.log('getList success')
            console.log(response.data)
            total.value = response.data['count']
            fileList.value = response.data['results']
        })
        .catch(error => {
            parseBackendError(error)
        })
}

const searchKeyword = () => {
    currentPage.value = 1
    saveSearchState()
    fetchData()
}

const parseOptions = (data) => {
    const options = [{ value: t('all'), label: t('all') }]
    data.forEach(item => {
        const hasTranslation = te(item)
        options.push({
            value: item,
            label: hasTranslation ? t(item) : item
        })
    })
    return options
}

const getOptions = async (obj, ctype) => {
    let func = 'api/entry/tool/'
    try {
        const response = await axios.get(getURL() + func, {
            params: { ctype: ctype, rtype: 'feature' }
        })
        console.log('getOptions success')

        if (ctype == 'all') {
            if ('ctype' in response.data) {
                ctype_options.value = parseOptions(response.data['ctype'])
            }
            if ('status' in response.data) {
                status_options.value = parseOptions(response.data['status'])
            }
            if ('etype' in response.data) {
                etype_options.value = parseOptions(response.data['etype'])
            }
        } else {
            const options = parseOptions(response.data)
            await nextTick()
            if (ctype === 'ctype') {
                ctype_options.value = options
            } else if (ctype === 'status') {
                status_options.value = options
            } else if (ctype === 'etype') {
                etype_options.value = options
            }
        }
    } catch (error) {
        console.log('getOptions error', error)
    }
}

const openAddDialog = () => {
    addDialog.value.openDialog((response_data) => {
        if (response_data.task_id) {
            if (navbarRef.value) {
                navbarRef.value.startTaskCheck(response_data.task_id)
            }
            ElMessage({
                type: 'success',
                message: t('task.taskStarted')
            })
        } else {
            fetchData()
        }
    })
}

const handleRowClick = (row) => {
    editDialog.value.openDialog(() => fetchData(), row)
}

const handleDelete = (row) => {
    ElMessageBox.confirm(t('deleteConfirmation'), t('promptTitle'), {
        confirmButtonText: t('confirm'),
        cancelButtonText: t('cancel'),
        type: 'warning'
    }).then(() => {
        deleteData(row.idx)
    }).catch(() => {
        ElMessage({
            type: 'info',
            message: t('cancelDelete')
        })
    })
}

const deleteData = (idx) => {
    let table_name = 'data'
    axios.delete(getURL() + 'api/entry/' + table_name + '/' + idx + '/')
        .then(response => {
            if (response.data.status == 'success') {
                ElMessage({
                    type: 'success',
                    message: t('deleteSuccess')
                })
                fetchData()
            } else {
                ElMessage({
                    type: 'error',
                    message: t('deleteFail')
                })
            }
        })
        .catch(error => {
            parseBackendError(error)
        })
}

const handleResize = () => {
    isMobile.value = window.innerWidth < 768
    const visualHeight = window.innerHeight
    console.log('visualHeight', visualHeight)
    document.documentElement.style.setProperty('--mainHeight', `${visualHeight}px`)
}

watch(status_value, () => {
    if (mounted.value) {
        currentPage.value = 1
        saveSearchState()
        fetchData()
    }
})

watch(ctype_value, () => {
    if (mounted.value) {
        currentPage.value = 1
        saveSearchState()
        fetchData()
    }
})

watch(etype_value, () => {
    if (mounted.value) {
        currentPage.value = 1
        saveSearchState()
        fetchData()
    }
})

watch(search_text, () => {
    if (mounted.value) {
        //currentPage.value = 1
        saveSearchState()
        //fetchData()
    }
})

watch(dateStart, () => {
    if (mounted.value) {
        saveSearchState()
        currentPage.value = 1
        fetchData()
    }
})

watch(dateEnd, () => {
    if (mounted.value) {
        saveSearchState()
        currentPage.value = 1
        fetchData()
    }
})

watch(searchMethod, () => {
    if (mounted.value) {
        saveSearchState()
        currentPage.value = 1
        fetchData()
    }
})

watch(currentPage, () => {
    if (mounted.value) {
        saveSearchState()
    }
})

onMounted(async () => {
    mounted.value = true
    isMobile.value = window.innerWidth < 768
    window.addEventListener('resize', handleResize)
    handleResize()
    
    await getOptions(null, "all")
    await nextTick()
    
    loadSearchState()
    
    fetchData()
    navbar.value = navbarRef.value
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>

.ellipsis-container {
    max-height: 40px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.select-dropdown {
    min-width: 100px !important;
}

.label-container {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    min-width: 40px;
}

.main-container {
    max-width: 100%;
    margin: 0 auto;
}

.header-buttons {
    width: 100%;
    margin-bottom: 8px;
}

.filter-row, .search-row {
    display: flex;
    gap: 4px;
    width: 100%;
    margin-bottom: 4px;
    align-items: center;
}

.search-controls-row {
    display: flex;
    gap: 8px;
    width: 100%;
    align-items: center;
}

.filter-section {
    display: flex;
    flex-grow: 1;
    align-items: center;
    gap: 4px;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-grow: 1;
}

.select-container {
    flex-grow: 1;
}

.search-section {
    display: flex;
    flex-grow: 3;
    align-items: center;
    gap: 4px;
}

.search-input-container {
    flex-grow: 1;
    min-width: 200px;
}

.date-range-section {
    display: flex;
    flex-grow: 0;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    min-width: 280px;
    max-width: 320px;
}

.search-method-section {
    display: flex;
    flex-grow: 2;
    flex-shrink: 1;
    align-items: center;
    gap: 4px;
    min-width: 180px;
}

.date-range-section .label-container {
    min-width: 40px;
    flex-shrink: 0;
}

.search-method-section .label-container {
    min-width: 40px;
    flex-shrink: 0;
}

.search-section .label-container {
    min-width: 40px;
    flex-shrink: 0;
}

.date-inputs-wrapper {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-grow: 1;
    max-width: 250px;
}

.date-inputs-wrapper .el-date-editor {
    max-width: 110px;
}

.action-section {
    display: flex;
    gap: 2px;
    align-items: center;
    flex-shrink: 0;
    min-width: fit-content;
}

.icon-button {
    padding: 6px !important;
    min-height: 24px !important;
    width: 24px !important;
    height: 24px !important;
    margin: 0 0 0 5px !important;
}

:deep(.date-range-section .el-date-editor) {
    max-width: 110px;
}

.list-width {
    max-width: 80%;
    margin: 0 auto;  /* Add this line to center the table */
}

.nowrap {
    white-space: nowrap;
}

@media (max-width: 767px) {
    .list-width {
        max-width: 100%;
    }

    .main-container {
        max-width: 100%;
    }

    .filter-row {
        flex-direction: row;
        gap: 4px;
        margin-bottom: 10px;
        flex-wrap: nowrap;
    }

    .search-row {
        flex-direction: column;
        gap: 8px;
        margin-bottom: 10px;
        align-items: flex-start;
    }

    .filter-section {
        width: 33.33%;
        justify-content: flex-start;
        flex-shrink: 1;
        min-width: 0;
    }

    .date-range-section {
        width: 100%;
        justify-content: flex-start;
    }

    .search-controls-row {
        flex-direction: row;
        gap: 4px;
        width: 100%;
    }

    .search-method-section {
        width: 30%;
        justify-content: flex-start;
        min-width: 0;
    }

    .search-section {
        width: 45%;
        justify-content: flex-start;
        min-width: 0;
    }

    .action-section {
        width: 25%;
        justify-content: center;
        gap: 2px;
        min-width: 0;
    }

    .select-container, .search-input-container {
        width: 100%;
    }

    :deep(.el-input) {
        width: 100%;
    }

    :deep(.el-select) {
        width: 100%;
    }

    .label-container {
        min-width: 30px;
        max-width: 40px;
        font-size: 12px;
        flex-shrink: 0;
    }

    .filter-item {
        flex-direction: row;
        align-items: center;
        gap: 4px;
    }

    .search-method-section .label-container,
    .search-section .label-container {
        min-width: 25px;
        max-width: 35px;
        font-size: 11px;
    }

    .date-range-section .label-container {
        min-width: 30px;
        max-width: 40px;
        font-size: 12px;
        justify-content: flex-start;
    }

    .search-input-container {
        min-width: 0;
    }

    .date-inputs-wrapper {
        width: 100%;
        justify-content: flex-start;
    }

    .date-inputs-wrapper .el-date-editor {
        flex: 1;
        max-width: 45%;
    }

    :deep(.el-text) {
        font-size: 13px;
    }

    :deep(.icon-button.el-button) {
        padding: 4px;
        margin: 0 0 0 5px !important;
    }
}

.delete-icon {
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s;
}

</style>