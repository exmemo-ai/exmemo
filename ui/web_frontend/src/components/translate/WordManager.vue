<template>
    <div style="display: flex; flex-direction: column;  width:100%;">
        <div class="list-options">
            <div class="header-buttons" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 0; width: 100%;">
                    <el-text class="no-shrink">{{ $t('search') }}</el-text>
                    <el-input v-model="search_text" :placeholder="$t('searchPlaceholder')" style="flex: 1;"/>
                    <el-button class="no-shrink" @click="searchKeyword">
                        <el-icon>
                            <Search />
                        </el-icon>
                    </el-button>
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
                <el-table-column prop="times" :label="$t('recordCount')" :width=100 show-overflow-tooltip></el-table-column>
                <el-table-column :label="$t('status')" :width=100 show-overflow-tooltip>
                    <template v-slot="scope">
                        {{ $t("trans."+scope.row.status) }}
                    </template>
                </el-table-column>
                <el-table-column :label="$t('operation')" :width=100>
                    <template v-slot="scope">
                        <el-button link @click="removeItem(scope.row)">{{ $t('delete') }}</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                layout="total, prev, pager, next, jumper" :total="total" 
                class="pagination-container">
            </el-pagination>
        </div>
        <el-dialog v-model="editDialogVisible" :title="$t('edit')" width="30%">
            <el-form :model="editForm">
                <el-form-item :label="$t('status')">
                    <el-select v-model="editForm.status" style="width: 100%">
                        <el-option :label="$t('trans.not_learned')" value="not_learned"/>
                        <el-option :label="$t('trans.learned')" value="learned"/>
                        <el-option :label="$t('trans.learning')" value="learning"/>
                        <el-option :label="$t('trans.reviewing')" value="reviewing"/>
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="editDialogVisible = false">{{ $t('cancel') }}</el-button>
                    <el-button type="primary" @click="saveEdit">{{ $t('confirm') }}</el-button>
                </span>
            </template>
        </el-dialog>
        <CheckDialog ref="checkDialog" />
        <OptWordListDialog ref="optWordListDialog" />
    </div>
</template>

<script>
import axios from 'axios';
import CheckDialog from './CheckDialog.vue';
import OptWordListDialog from './OptWordListDialog.vue';
import { getURL, parseBackendError } from '@/components/support/conn';
import { Search, Plus } from '@element-plus/icons-vue';
import { realUpdate, getMeaning } from './WordLearningSupport';

export default {
    name: 'WordManager',
    components: {
        CheckDialog,
        OptWordListDialog,
        Search,
        Plus
    },
    data() {
        return {
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
            editDialogVisible: false,
            editForm: {
                idx: null,
                word: '',
                status: ''
            },
            savedFreq: localStorage.getItem('selectedWordFreq')
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
                    for (let i = 0; i < this.fileList.length; i++) {
                        if (this.fileList[i].info.translate) {
                            this.fileList[i].meaning = this.fileList[i].info.translate;
                        } else {
                            if (this.fileList[i].info && this.fileList[i].info.base) {
                                this.fileList[i].meaning = getMeaning(this.fileList[i].info, this.savedFreq);
                            }
                        }
                    }
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
            this.editForm = { ...row };
            this.editDialogVisible = true;
        },
        async saveEdit() {
            try {
                await realUpdate([this.editForm]);
                this.editDialogVisible = false;
                this.fetchData();
                this.$message.success(this.$t('updateSuccess'));
            } catch (error) {
                this.$message.error(this.$t('updateFailed'));
            }
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