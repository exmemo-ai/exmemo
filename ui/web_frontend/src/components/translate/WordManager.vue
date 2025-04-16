<template>
    <div style="display: flex; flex-direction: column;  width:100%;">
        <div class="list-options">
            <div class="header-buttons" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 0; width: 100%;">
                    <el-text class="no-shrink">{{ $t('search') }}</el-text>
                    <el-input v-model="search_text" :placeholder="$t('searchPlaceholder')" style="flex: 1; margin-left:5px"/>
                    <el-button class="no-shrink" @click="searchKeyword">
                        <el-icon>
                            <Search />
                        </el-icon>
                    </el-button>
                    <el-select v-model="statusFilter" 
                              style="margin-left: 5px; flex:1;" 
                              @change="searchKeyword"
                              :placeholder="$t('status')">
                        <el-option :label="$t('all')" value=""></el-option>
                        <el-option v-for="status in statusOptions" 
                                 :key="status" 
                                 :label="$t('trans.' + status)" 
                                 :value="status">
                        </el-option>
                    </el-select>
                    <el-button @click="searchWord">
                        <el-icon>
                            <Plus />
                        </el-icon>
                    </el-button>
                    <el-button @click="optWordList">{{ $t('trans.processWordListSimple') }}</el-button>
                </div>
            </div>
            <el-table :data="fileList" @row-click="handleRowClick" style="width: 100%" stripe>
                <el-table-column prop="word" :label="$t('english')" show-overflow-tooltip></el-table-column>
                <el-table-column prop="meaning" :label="$t('translate')" show-overflow-tooltip></el-table-column>
                <el-table-column prop="freq" :label="$t('frequency')" :width=70 show-overflow-tooltip></el-table-column>
                <!--<el-table-column prop="times" :label="$t('recordCount')" :width=100 show-overflow-tooltip></el-table-column>-->
                <el-table-column :label="$t('status')" :width=100 show-overflow-tooltip>
                    <template v-slot="scope">
                        {{ $t("trans."+scope.row.status) }}
                    </template>
                </el-table-column>
                <el-table-column :label="$t('operation')" :width=100>
                    <template v-slot="scope">
                        <el-button link @click.stop="removeItem(scope.row)">{{ $t('delete') }}</el-button>
                    </template>
                </el-table-column>
                <template #empty>
                    <div style="text-align: center; padding: 20px;">
                        <el-empty :description="$t('trans.noWordsYet')">
                            <el-button type="primary" @click="optWordList">
                                {{ $t('trans.importWordList') }}
                            </el-button>
                        </el-empty>
                    </div>
                </template>
            </el-table>
            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                layout="total, prev, pager, next, jumper" :total="total" 
                class="pagination-container">
            </el-pagination>
        </div>
        <WordEditorDialog ref="wordEditorDialog" @update="fetchData" />
        <CheckDialog ref="checkDialog" />
        <OptWordListDialog ref="optWordListDialog" />
    </div>
</template>

<script>
import axios from 'axios';
import CheckDialog from './LookupDialog.vue';
import OptWordListDialog from './OptWordListDialog.vue';
import WordEditorDialog from './WordEditorDialog.vue';
import { getURL, parseBackendError } from '@/components/support/conn';
import { Search, Plus } from '@element-plus/icons-vue';
import { getMeaning } from './WordLearningSupport';

export default {
    name: 'WordManager',
    components: {
        CheckDialog,
        OptWordListDialog,
        WordEditorDialog,
        Search,
        Plus
    },
    data() {
        return {
            isLogin: false,
            login_user: '',
            total: 0,
            currentPage: 1,
            pageSize: 10,
            search_text: '',
            fileList: [],
            statusFilter: '',
            statusOptions: ['learned', 'learning', 'not_learned', 'review'],
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
        async fetchData() {
            console.log('fetchData');
            let func = 'api/translate/word/'
            let params = {
                keyword: this.search_text,
                page: this.currentPage, 
                page_size: this.pageSize,
                status: this.statusFilter
            }
            try {
                const response = await axios.get(getURL() + func, { params: params });
                console.log('getList success', response.data);
                this.total = response.data['count'];
                this.fileList = response.data['results'];
                
                await Promise.all(this.fileList.map(async (item) => {
                    if (item.info.translate) {
                        item.meaning = item.info.translate;
                    } else {
                        if (item.info && item.info.base) {
                            item.meaning = await getMeaning(item.info);
                        }
                    }
                }));
            } catch (error) {
                parseBackendError(error);
            }
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
                    parseBackendError(error);
                });
        },
        handleRowClick(row, column, event) {
            this.$refs.wordEditorDialog.openDialog(row);
        },
        searchWord() {
            this.$refs.checkDialog.openDialog(this);
        },
        optWordList() {
            this.$refs.optWordListDialog.openDialog(this);
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

.search-icon {
    cursor: pointer;
    padding: 0 5px;
}

.search-icon:hover {
    color: var(--el-color-primary);
}

.search-container {
    flex: 1;
}
</style>