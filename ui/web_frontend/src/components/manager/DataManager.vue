<template>
    <div class="full-container">
      <el-container style="flex: 0; width: 100%;">
        <app-navbar :title="t('dataManagement')" :info="'DataManager'" />
      </el-container>
      <el-container style="flex: 1; width: 100%; overflow: hidden;">
        <el-main class="main-container list-options">
            <div class="header-buttons">
                <div class="search-section">
                    <div class="label-container">
                        <el-text>{{ t('search') }}</el-text>
                    </div>
                    <div :class="{'mobile-input': isMobile}">
                        <el-input v-model="search_text" :placeholder="t('searchPlaceholder')"></el-input>
                    </div>
                </div>

                <div class="filter-section">
                    <div class="filter-item">
                        <div class="label-container">
                            <el-text>{{ t('data') }}</el-text>
                        </div>
                        <div class="select-container">
                            <el-select v-if="mounted && etype_options.length" 
                                v-model="etype_value"
                                :placeholder="t('selectPlaceholder')">
                                <el-option v-for="item in etype_options" :key="item.value" 
                                    :label="item.label" :value="item.value">
                                </el-option>
                            </el-select>
                        </div>
                    </div>
                </div>
                <div class="filter-section" v-if="!isMobile">
                    <div class="filter-item">
                        <div class="label-container">
                            <el-text>{{ t('type') }}</el-text>
                        </div>
                        <div class="select-container">
                            <el-select v-if="mounted && ctype_options && ctype_options.length > 0" 
                                v-model="ctype_value"
                                :placeholder="t('selectPlaceholder')" 
                                popper-class="select-dropdown">
                                <el-option v-for="item in ctype_options" :key="item.value" 
                                    :label="item.label" :value="item.value">
                                </el-option>
                            </el-select>
                        </div>
                    </div>
                </div>

                <div class="filter-section" v-if="!isMobile">
                    <div class="filter-item">
                        <div class="label-container">
                            <el-text>{{ t('status') }}</el-text>
                        </div>
                        <div class="select-container">
                            <el-select v-if="mounted && status_options.length" 
                                v-model="status_value"
                                :placeholder="t('selectPlaceholder')">
                                <el-option v-for="item in status_options" :key="item.value" 
                                    :label="item.label" :value="item.value">
                                </el-option>
                            </el-select>
                        </div>
                    </div>
                </div>

                <div class="action-section">
                    <el-button class="icon-button" @click="searchKeyword">
                        <el-icon><Search /></el-icon>
                    </el-button>
                    <el-button class="icon-button" @click="openAddDialog">
                        <el-icon><Plus /></el-icon>
                    </el-button>
                </div>
            </div>
            <el-container class="list-width" style="flex: 1; flex-direction: column; width: 100%;">
                <el-table :data="fileList" @row-click="handleRowClick" stripe>
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
                </el-table>
                <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                    :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                    layout="total, sizes, prev, pager, next, jumper" :total="total">
                </el-pagination>
            </el-container>
        </el-main>
      </el-container>
      <EditDialog ref="editDialog" />
      <AddDialog ref="addDialog" />
    </div>
</template>

<script>
import { Search, Plus } from '@element-plus/icons-vue'
import axios from 'axios';
import EditDialog from './EditDialog.vue';
import AddDialog from './AddDialog.vue';
import { getURL, parseBackendError } from '@/components/support/conn'
import AppNavbar from '@/components/support/AppNavbar.vue'
import { useI18n } from 'vue-i18n'

export default {
    name: 'NoteManager',
    components: {
        EditDialog,
        AddDialog,
        AppNavbar,
        Search,
        Plus
    },
    setup() {
        const { t, te } = useI18n();
        return { t, te };
    },
    data() {
        const { t } = useI18n();
        return {
            mounted: false,
            isMobile: false,
            total: 0,
            currentPage: 1,
            pageSize: 10,
            status_value: t('all'),
            status_options: [],
            ctype_value: t('all'),
            ctype_options: [],
            etype_value: t('all'),
            etype_options: [],
            search_text: '',
            fileList: [],
        };
    },
    methods: {
        handleSizeChange(val) {
            this.pageSize = val;
            this.fetchData();
        },
        handleCurrentChange(val) {
            this.currentPage = val;
            this.fetchData();
        },
        fetchData() {
            console.log('##### fetchData', this);
            let func = 'api/entry/data/'
            let etype_value = this.etype_value === this.t('all') ? '' : this.etype_value;
            let ctype_value = this.ctype_value === this.t('all') ? '' : this.ctype_value;
            let status_value = this.status_value === this.t('all') ? '' : this.status_value;
            let params = {
                keyword: this.search_text, etype: etype_value,
                ctype: ctype_value, status: status_value,
                page: this.currentPage, page_size: this.pageSize
            }
            axios.get(getURL() + func, { params: params })
                .then(response => {
                    console.log('getList success');
                    console.log(response.data);
                    this.total = response.data['count'];
                    this.fileList = response.data['results'];
                })
                .catch(error => {
                    parseBackendError(this, error);
                });
        },
        searchKeyword() {
            this.currentPage = 1;
            this.fetchData();
        },
        async getOptions(obj, ctype) {
            let func = 'api/entry/tool/'
            try {
                const response = await axios.get(getURL() + func, {
                    params: { ctype: ctype, rtype: 'feature' }
                });

                console.log('getOptions success');
                let ret = response.data;
                const options = [{ value: this.t('all'), label: this.t('all') }];

                ret.forEach(item => {
                    const hasTranslation = this.te(item);
                    options.push({
                        value: item,
                        label: hasTranslation ? this.t(item) : item
                    });
                });

                await this.$nextTick();
                if (ctype === 'ctype') {
                    this.ctype_options = options;
                } else if (ctype === 'status') {
                    this.status_options = options;
                } else if (ctype === 'etype') {
                    this.etype_options = options;
                }
            } catch (error) {
                console.log('getOptions error', error);
            }
        },
        openAddDialog() {
            this.$refs.addDialog.openDialog(this);
        },
        handleRowClick(row, column, event) {
            console.log(column, event)
            this.$refs.editDialog.openDialog(this, row);
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
    },
    async mounted() {
        this.mounted = true;
        this.isMobile = window.innerWidth < 768;
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
        await this.getOptions(this, "ctype");
        await this.getOptions(this, "status");
        await this.getOptions(this, "etype");
        await this.$nextTick();
        this.fetchData();
    }
}
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
    flex-shrink: 1;
}

.main-container {
    max-width: 100%;
    margin: 0 auto;
}

.header-buttons {
    display: flex;
    flex-wrap: nowrap;
    gap: 5px;
    margin-left: 5px;
    margin-right: 5px;
    align-items: center;
}

.search-section {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
}

.filter-section {
    display: flex;
    flex-grow: 1;
    align-items: center;
    gap: 5px;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-grow: 1;
}

.select-container {
    flex-grow: 1;
}

.action-section {
    display: flex;
    gap: 0px;
    align-items: center;
    flex-shrink: 0;
}

.mobile-input {
    width: 120px;
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

    .header-buttons {
        gap: 2px;
    }

    :deep(.el-main) {
        padding: 5px;
    }

    :deep(.icon-button.el-button) {
        margin: 0 !important;
    }    
}
</style>