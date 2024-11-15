<template>
    <div>
        <div class="header-buttons" style="float: right; text-align: right;">
            <el-button @click="searchWord">{{ $t('searchWord') }}</el-button>
        </div>
        <el-main class="custom-padding">
            <div class="custom-options" style="display: flex;margin: 5px; flex-direction: column;">
                <div style="display: flex;" v-if="!isMobile">
                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-label>{{ $t('search') }}</el-label>
                    </div>
                    <div style="flex-grow: 0;margin: 5px;">
                        <el-input v-model="search_text" :placeholder="$t('searchPlaceholder')"></el-input>
                    </div>
                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-button @click="searchKeyword">{{ $t('search') }}</el-button>
                    </div>
                </div>
                <el-table :data="fileList" @row-click="handleRowClick" style="width: 100%" stripe>
                    <el-table-column prop="word" :label="$t('english')"></el-table-column>
                    <el-table-column prop="freq" :label="$t('frequency')" :width=70></el-table-column>
                    <el-table-column prop="times" :label="$t('recordCount')" :width=100></el-table-column>
                    <el-table-column :label="$t('operation')" :width=100>
                        <template v-slot="scope">
                            <el-button type="text" @click="removeItem(scope.row)">{{ $t('delete') }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                    :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                    layout="total, sizes, prev, pager, next, jumper" :total="total">
                </el-pagination>
            </div>
        </el-main>
        <CheckDialog ref="checkDialog" />
    </div>
</template>

<script>
import axios from 'axios';
import CheckDialog from './CheckDialog.vue';
import { getURL, parseBackendError } from '@/components/conn';

export default {
    name: 'WordManager',
    components: {
        CheckDialog
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
            let func = 'api/translate/word/'
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
                    parseBackendError(this, error);
                });
        },
        searchKeyword() {
            this.currentPage = 1;
            this.fetchData();
        },
        removeItem(row) {
            console.log(row);
            let func = 'api/translate/word/' + row.idx + '/';
            axios.delete(getURL() + func)
                .then(response => {
                    console.log('delete success', response.data);
                    this.fetchData();
                })
                .catch(error => {
                    parseBackendError(this, error);
                });
        },
        handleRowClick(row, column, event) {
            console.log(column, event)
        },
        searchWord() {
            this.$refs.checkDialog.openDialog(this);
        }
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

.custom-options {
    font-size: 12px;
    --el-input-font-size: 12px;
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

</style>