<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
        <el-container>
            <h3 style="text-align: left;">{{ $t('articleList') }}</h3>
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
                </div>
            </el-header>
        </el-container>
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
                    <el-table-column prop="title" :label="$t('title')"></el-table-column>
                    <el-table-column prop="created_time" :label="$t('time')" :width=100></el-table-column>
                </el-table>
                <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                    :current-page="currentPage" :page-sizes="[10]" :page-size="10"
                    layout="total, sizes, prev, pager, next, jumper" :total="total">
                </el-pagination>
            </div>
        </el-main>
    </div>
</template>

<script>
import axios from 'axios';
import { getURL, parseBackendError, checkLogin, realLoginFunc, realLogoutFunc, gotoAssistantPage, gotoReaderPage } from '@/components/conn';
export default {
    name: 'ArticleManager',
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
                    parseBackendError(this, error);
                });
        },
        searchKeyword() {
            this.currentPage = 1;
            this.fetchData();
        },
        openEditDialog() {
        },
        handleRowClick(row, column, event) {
            console.log(column, event)
        },
    },
    mounted() {
        this.isLogin = checkLogin(this);
        if (this.isLogin) {
            this.login_user = localStorage.getItem('username');
        }
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