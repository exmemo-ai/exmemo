<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
        <div style="display: flex; flex-direction: column;">
            <app-navbar :title="navTitle" :info="navInfo" />
        </div>
        <el-container>
            <el-aside class="aside-menu" :class="{ 'mobile-aside': isMobile }">
                <el-menu :default-active="activeMenu" @select="handleSelect">
                    <el-menu-item index="reader">
                        <span>{{ $t('englishReading') }}</span>
                    </el-menu-item>
                    <el-menu-item index="word">
                        <span>{{ $t('vocabularyList') }}</span>
                    </el-menu-item>
                    <el-menu-item index="article">
                        <span>{{ $t('articleList') }}</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-main>
                <component :is="currentComponent" ref="currentView"></component>
            </el-main>
        </el-container>
    </div>
</template>

<script>
import EnReader from './EnReader.vue'
import WordManager from './WordManager.vue'
import ArticleManager from './ArticleManager.vue'
import AppNavbar from '@/components/support/AppNavbar.vue'

export default {
    name: 'TranslateMain',
    components: {
        EnReader,
        WordManager,
        ArticleManager,
        AppNavbar
    },
    data() {
        return {
            isMobile: false,
            activeMenu: 'reader',
            currentComponent: 'EnReader',
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