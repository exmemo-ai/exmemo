<template>
    <div>
        <div class="list-options">
            <div class="header-buttons" style="display: flex; align-items: center; gap: 0px; margin-bottom: 10px;">
                <el-text style="white-space: nowrap;">{{ $t('search') }}</el-text>
                <el-input v-model="search_text" :placeholder="$t('searchPlaceholder')" style="flex: 1;"></el-input>
                <el-button class="icon-button" @click="searchKeyword">
                    <el-icon><Search /></el-icon>
                </el-button>
            </div>
            <el-table :data="fileList" @row-click="handleRowClick" style="width: 100%" stripe>
                <el-table-column prop="title" :label="$t('title')" show-overflow-tooltip></el-table-column>
                <el-table-column prop="created_time" :label="$t('time')" :width=100 show-overflow-tooltip></el-table-column>
            </el-table>

            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                layout="total, prev, pager, next" :total="total"
                class="pagination-container">
            </el-pagination>
        </div>
        <el-dialog :title="selectedItem.title" v-model="dialogVisible" width="70%">
            <div style="white-space: pre-wrap;">{{ selectedItem.content }}</div>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios';
import { Search } from '@element-plus/icons-vue';
import { getURL, parseBackendError } from '@/components/support/conn';

export default {
    name: 'ArticleManager',
    components: {
        Search,
    },
    data() {
        return {
            isMobile: false,
            isLogin: false,
            login_user: '',
            // table page
            total: 0,
            currentPage: 1,
            pageSize: 10,
            //
            search_text: '',
            //
            fileList: [],
            dialogVisible: false,
            selectedItem: {
                title: '',
                content: ''
            },
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
            console.log('fetchData');
            let func = 'api/translate/article/'
            let params = {
                keyword: this.search_text,
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
                    parseBackendError(error);
                });
        },
        searchKeyword() {
            this.currentPage = 1;
            this.fetchData();
        },
        openEditDialog() {
        },
        handleRowClick(row, column, event) {
            this.selectedItem = row;
            this.dialogVisible = true;
        },
    },
    mounted() {
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

.full-width {
    width: 100%;
}

</style>