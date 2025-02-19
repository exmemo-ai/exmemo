<template>
  <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
    <div style="display: flex; flex-direction: column;">
      <app-navbar :title="navTitle" :info="navInfo" />
    </div>
    <el-container>
      <el-aside class="aside-menu" :class="{ 'mobile-aside': isMobile, 'collapse-aside': isCollapse }">
        <div class="toggle-button-collapse" @click="toggleCollapse">
          <el-icon>
            <Fold v-if="!isCollapse"/>
            <Expand v-else/>
          </el-icon>
        </div>
        <el-menu 
          :default-active="activeMenu" 
          :collapse="isCollapse"
          @select="handleSelect">
          <el-menu-item index="navigation">
            <span>{{ $t('quickNavigation') }}</span>
          </el-menu-item>
          <el-menu-item index="search">
            <span>{{ $t('searchTitle') }}</span>
          </el-menu-item>
          <el-menu-item index="readlater">
            <span>{{ $t('readLater') }}</span>
          </el-menu-item>
          <el-menu-item index="bookmarks">
            <span>{{ $t('bookmarkTree') }}</span>
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
import { Fold, Expand } from '@element-plus/icons-vue'
import AppNavbar from '@/components/support/AppNavbar.vue'
import SearchManager from './BMSearch.vue'
import NavigationManager from './BMNavigation.vue'
import ReadLaterManager from './BMReadLater.vue'
import BookmarkTree from './BMBookmarkTree.vue'

export default {
  name: 'BMManagerMain',
  components: {
    AppNavbar,
    SearchManager,
    SearchManager,
    NavigationManager,
    ReadLaterManager,
    BookmarkTree,
    Fold,
    Expand
  },
  data() {
    return {
      isMobile: false,
      isCollapse: false,
      activeMenu: 'navigation',
      currentComponent: 'NavigationManager',
      navTitle: this.$t('quickNavigation'),
      navInfo: 'BMManager'
    }
  },
  methods: {
    handleSelect(key) {
      this.activeMenu = key;
      switch(key) {
        case 'search':
          this.currentComponent = 'SearchManager';
          this.navTitle = this.$t('bookmarkSearch');
          break;
        case 'navigation':
          this.currentComponent = 'NavigationManager';
          this.navTitle = this.$t('quickNavigation');
          break;
        case 'readlater':
          this.currentComponent = 'ReadLaterManager';
          this.navTitle = this.$t('readLater');
          break;
        case 'bookmarks':
          this.currentComponent = 'BookmarkTree';
          this.navTitle = this.$t('bookmarkTree');
          break;
      }
    },
    handleResize() {
      this.isMobile = window.innerWidth < 768;
    },
    toggleCollapse() {
      this.isCollapse = !this.isCollapse;
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
