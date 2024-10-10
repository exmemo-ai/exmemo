<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
        <el-container>
            <h3 style="text-align: left;">{{ $t('dataManagement') }}</h3>
            <div style="display: flex; align-items: center; justify-content: flex-end; margin-left: auto; max-width: 100%;">
                <el-label type="text" v-if="isLogin" style="margin-right: 5px;">{{ login_user }}</el-label>
                <el-button type="text" @click="logoutFunc" v-if="isLogin">{{ $t('logout') }}</el-button>
                <el-button type="text" @click="loginFunc" v-else>{{ $t('login') }}</el-button>
                <el-button @click="gotoUserSetting" v-if="isLogin">{{ $t('userSetting') }}</el-button>
            </div>
        </el-container>
        <el-container>
            <el-header class="custom-padding">
                <div class="header-buttons" style="float: right;">
                    <el-button @click="gotoReader">{{ $t('readingTools') }}</el-button>
                    <el-button @click="gotoAssistant">{{ $t('assistantTools') }}</el-button>
                    <el-button @click="openEditDialog()">{{ $t('add') }}</el-button>
                    <!--<el-button @click="exportRecord()">{{ $t('export') }}</el-button>-->
                </div>
            </el-header>
        </el-container>
        <el-main class="custom-padding">
            <div class="custom-options" style="display: flex;margin: 5px;">
                <div style="display: flex;" v-if="!isMobile">
                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-label>{{ $t('search') }}</el-label>
                    </div>
                    <div style="flex-grow: 0;margin: 5px;">
                        <el-input v-model="search_text" :placeholder="$t('searchPlaceholder')"></el-input>
                    </div>
                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-label>{{ $t('type') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;margin: 5px;">
                        <el-select v-model="ctype_value" :placeholder="$t('selectPlaceholder')">
                            <el-option v-for="item in ctype_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>

                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-label>{{ $t('data') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;margin: 5px;">
                        <el-select v-model="etype_value" :placeholder="$t('selectPlaceholder')">
                            <el-option v-for="item in etype_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>

                    <div style="flex-shrink: 1;margin: 5px;">
                        <el-label>{{ $t('status') }}</el-label>
                    </div>
                    <div style="flex-grow: 1;margin: 5px;">
                        <el-select v-model="status_value" :placeholder="$t('selectPlaceholder')">
                            <el-option v-for="item in status_options" :key="item.value" :label="item.label"
                                :value="item.value">
                            </el-option>
                        </el-select>
                    </div>
                </div>
                <div style="flex-shrink: 1;margin: 5px;">
                    <el-button @click="searchKeyword">{{ $t('search') }}</el-button>
                </div>
            </div>
            <el-table :data="fileList" @row-click="handleRowClick" style="width: 100%" stripe>
                <el-table-column prop="title" :label="$t('title')">
                    <template v-slot="scope">
                        <div class="ellipsis-container">{{ scope.row.title }}</div>
                    </template>
                </el-table-column>
                <el-table-column prop="ctype" :label="$t('type')" :width=100></el-table-column>
                <el-table-column prop="etype" :label="$t('data')" :width=70 v-if="!isMobile"></el-table-column>
                <el-table-column prop="updated_time" :label="$t('lastUpdated')" :width=100
                    v-if="!isMobile"></el-table-column>
                <el-table-column prop="status" :label="$t('status')" :width=70></el-table-column>
            </el-table>
            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page="currentPage"
                :page-sizes="[10]" :page-size="10" layout="total, sizes, prev, pager, next, jumper" :total="total">
            </el-pagination>
        </el-main>
        <EditDialog ref="editDialog" />
    </div>
</template>

<script>
import axios from 'axios';
import EditDialog from './EditDialog.vue';
import { getURL, parseBackendError, checkLogin, realLoginFunc, realLogoutFunc, gotoAssistantPage, gotoReaderPage } from './conn'
export default {
    name: 'NoteManager',
    components: {
        EditDialog
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
            status_value: '',
            status_options: [],
            ctype_value: '',
            ctype_options: [],
            etype_value: '',
            etype_options: [],
            search_text: '',
            //
            fileList: [],
        };
    },
    methods: {
        gotoUserSetting() {
            this.$router.push('/user_setting');
        },
        gotoReader() {
            gotoReaderPage(this);
        },
        gotoAssistant() {
            gotoAssistantPage(this);
        },
        loginFunc() {
            realLoginFunc(this);
        },
        logoutFunc() {
            realLogoutFunc(this);
        },
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
            let func = 'api/entry/data/'
            let params = {
                keyword: this.search_text, etype: this.etype_value,
                ctype: this.ctype_value, status: this.status_value,
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
        getOptions(obj, ctype) {
            let func = 'api/entry/tool/'
            axios.get(getURL() + func, { params: { ctype: ctype, rtype: 'feature' } })
                .then(response => {
                    console.log('getOptions success');
                    let ret = response.data;
                    if (ctype == 'ctype') {
                        obj.ctype_options = ['', ''];
                        for (let i = 0; i < ret.length; i++) {
                            obj.ctype_options[i + 1] = {
                                value: ret[i],
                                label: ret[i]
                            }
                        }
                    } else if (ctype == 'status') {
                        obj.status_options = ['', ''];
                        for (let i = 0; i < ret.length; i++) {
                            obj.status_options[i + 1] = {
                                value: ret[i],
                                label: ret[i]
                            }
                        }
                    } else if (ctype == 'etype') {
                        obj.etype_options = ['', ''];
                        for (let i = 0; i < ret.length; i++) {
                            obj.etype_options[i + 1] = {
                                value: ret[i],
                                label: ret[i]
                            }
                        }
                    }
                    return response.data;
                })
                .catch(error => {
                    console.log('getOptions error', error);
                });
            return []
        },
        openEditDialog() {
            this.$refs.editDialog.openEditDialog(this);
        },
        handleRowClick(row, column, event) {
            console.log(column, event)
            this.$refs.editDialog.openEditDialog(this, row);
        },
    },
    mounted() {
        this.isLogin = checkLogin(this);
        if (this.isLogin) {
            this.login_user = localStorage.getItem('username');
        }
        this.getOptions(this, "ctype");
        this.getOptions(this, "status");
        this.getOptions(this, "etype");
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
    max-width: 80%;
    margin: 0 auto;
}

@media (max-width: 767px) {
    .desktop-width {
        max-width: 100%;
    }
}

.custom-padding {
    --el-header-padding: 5px;
    --el-main-padding: 5px;
}
</style>