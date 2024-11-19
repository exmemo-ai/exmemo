<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
        <div style="display: flex; flex-direction: column;">
            <app-navbar :title="t('dataManagement')" :info="'DataManager'" />
        </div>
        <el-main class="main-container custom-options">
            <div class="header-buttons">
                <div class="search-container">
                    <div class="label-container">
                        <el-label>{{ t('search') }}</el-label>
                    </div>
                    <div :class="{'mobile-input': isMobile}">
                        <el-input v-model="search_text" :placeholder="t('searchPlaceholder')"></el-input>
                    </div>
                </div>
                <div style="display: flex; flex-grow: 1; align-items: center; gap: 5px;" v-if="!isMobile">
                    <div class="label-container">
                        <el-label>{{ t('type') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;">
                        <el-select v-if="ctype_options && ctype_options.length > 0" v-model="ctype_value"
                            :placeholder="t('selectPlaceholder')" popper-class="select-dropdown">
                            <el-option v-for="item in ctype_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>

                    <div class="label-container">
                        <el-label>{{ t('data') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;">
                        <el-select v-if="etype_options.length" v-model="etype_value"
                            :placeholder="t('selectPlaceholder')">
                            <el-option v-for="item in etype_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>
                    <div class="label-container">
                        <el-label>{{ t('status') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;">
                        <el-select v-if="status_options.length" v-model="status_value"
                            :placeholder="t('selectPlaceholder')">
                            <el-option v-for="item in status_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>
                </div>
                <div style="display: flex; flex-grow: 0; align-items: center;">
                    <el-button class="icon-button" @click="searchKeyword" icon>
                        <el-icon>
                            <Search />
                        </el-icon>
                    </el-button>
                </div>
                <div style="flex-shrink: 0;">
                    <el-button class="icon-button" @click="openEditDialog" icon>
                        <el-icon>
                            <Plus />
                        </el-icon>
                    </el-button>
                </div>
            </div>
            <el-table :data="fileList" @row-click="handleRowClick" style="width: 100%" stripe>
                <el-table-column prop="title" :label="t('title')">
                    <template v-slot="scope">
                        <div class="ellipsis-container" style="white-space: nowrap;">{{ scope.row.title }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="ctype" :label="t('type')" :width=100>
                    <template v-slot="scope">
                        <div style="white-space: nowrap;">{{ scope.row.ctype }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="etype" :label="t('data')" :width=70 v-if="!isMobile">
                    <template v-slot="scope">
                        <div style="white-space: nowrap;">{{ scope.row.etype }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="updated_time" :label="t('lastUpdated')" :width=100 v-if="!isMobile">
                    <template v-slot="scope">
                        <div style="white-space: nowrap;">{{ scope.row.updated_time }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="status" :label="t('status')" :width=70>
                    <template v-slot="scope">
                        <div style="white-space: nowrap;">{{ scope.row.status }}</div>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                layout="total, sizes, prev, pager, next, jumper" :total="total">
            </el-pagination>
        </el-main>
        <EditDialog ref="editDialog" />
    </div>
</template>

<script>
import { Search, Plus } from '@element-plus/icons-vue'
import axios from 'axios';
import EditDialog from './EditDialog.vue';
import { getURL, parseBackendError } from '@/components/support/conn'
import AppNavbar from '@/components/support/AppNavbar.vue'
import { useI18n } from 'vue-i18n'

export default {
    name: 'NoteManager',
    components: {
        EditDialog,
        AppNavbar,
        Search,
        Plus
    },
    setup() {
        const { t } = useI18n();
        return { t };
    },
    data() {
        const { t } = useI18n();
        return {
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
                    options.push({
                        value: item,
                        label: this.t(item) === item ? item : this.t(item)
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
        openEditDialog() {
            this.$refs.editDialog.openEditDialog(this);
        },
        handleRowClick(row, column, event) {
            console.log(column, event)
            this.$refs.editDialog.openEditDialog(this, row);
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        },
    },
    async mounted() {
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

.custom-options {
    font-size: 12px;
    --el-input-font-size: 12px;
    align-items: center;
}

.full-width {
    width: 100%;
}

.desktop-width {
    max-width: 100%;
    margin: 0 auto;
}

@media (max-width: 767px) {
    .desktop-width {
        max-width: 100%;
    }
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
    max-width: 80%;
    margin: 0 auto;
}

@media (max-width: 767px) {
    .main-container {
        max-width: 100%;
    }
}

.header-buttons {
    display: flex;
    flex-wrap: nowrap;
    gap: 5px;
    align-items: center;
}

.search-container {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-shrink: 0;
}

.mobile-input {
    width: 120px;
}

@media (max-width: 767px) {
    .header-buttons {
        gap: 2px;
    }
}
</style>