<template>
    <div class="full-container">
        <el-container style="flex: 0; width: 100%;">
            <app-navbar :title="navTitle" :info="navInfo" />
        </el-container>
        <el-container style="flex: 1; width: 100%; overflow: hidden;">
            <el-aside class="aside-menu" :class="{ 'mobile-aside': isMobile }">
                <el-menu :default-active="activeMenu" @select="handleSelect">
                    <el-menu-item index="word">
                        <span>{{ $t('vocabularyList') }}</span>
                    </el-menu-item>
                    <el-menu-item index="learn">
                        <span>{{ $t('learn') }}</span>
                    </el-menu-item>
                    <el-menu-item index="reader">
                        <span>{{ $t('englishReading') }}</span>
                    </el-menu-item>
                    <el-menu-item index="article">
                        <span>{{ $t('articleList') }}</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-container class="right-content">
                <component :is="currentComponent" ref="currentView"></component>
            </el-container>
        </el-container>
    </div>
</template>

<script>
import EnReader from './EnReader.vue'
import WordManager from './WordManager.vue'
import ArticleManager from './ArticleManager.vue'
import WordLearning from './WordLearning.vue'
import AppNavbar from '@/components/support/AppNavbar.vue'

export default {
    name: 'TranslateMain',
    components: {
        WordManager,
        EnReader,
        ArticleManager,
        AppNavbar,
        WordLearning
    },
    data() {
        return {
            isMobile: false,
            activeMenu: 'word',
            currentComponent: 'WordManager',
            navTitle: this.$t('englishReading'),
            navInfo: 'ReadingTools'
        }
    },
    methods: {
        handleSelect(key) {
            this.activeMenu = key;
            switch(key) {
                case 'reader':
                    this.currentComponent = 'EnReader';
                    this.navTitle = this.$t('englishReading');
                    this.navInfo = 'ReadingTools';
                    break;
                case 'word':
                    this.currentComponent = 'WordManager';
                    this.navTitle = this.$t('vocabularyList');
                    this.navInfo = 'VocabularyList';
                    break;
                case 'article':
                    this.currentComponent = 'ArticleManager';
                    this.navTitle = this.$t('articleList');
                    this.navInfo = 'ArticleList';
                    break;
                case 'learn':
                    this.currentComponent = 'WordLearning';
                    this.navTitle = this.$t('wordLearning');
                    this.navInfo = 'WordLearning';
                    break;
            }
        },
        handleResize() {
            this.isMobile = window.innerWidth < 768;
        }
    },
    mounted() {
        this.handleResize();
        window.addEventListener('resize', this.handleResize);
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    }
}
</script>

<style scoped>
.right-content {
    padding: 20px;
    overflow: auto;
    display: flex; 
    flex-direction: column;  
}

@media screen and (max-width: 768px) {
    .right-content {
        padding: 10px;
    }
}
</style>