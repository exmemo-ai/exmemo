<template>
  <div class="section">
    <div class="section-header">
      <h3>{{ $t('quickNavigation') }}</h3>
      <div class="controls">
        <el-select v-model="bookmarkSort" size="small" @change="refreshBookmarks">
          <template #prefix>
            <span class="selected-text">{{ $t('sortBy') }}{{ getSortLabel(bookmarkSort) }}</span>
          </template>
          <el-option 
            v-for="(label, value) in sortOptions" 
            :key="value"
            :label="$t(label)"
            :value="value" />
        </el-select>
        <el-select v-model="bookmarkLimit" size="small" @change="refreshBookmarks">
          <template #prefix>
            <span class="selected-text">{{ $t('showLimit') }}</span>
          </template>
          <el-option v-for="n in [3,6,9,12]" :key="n" :label="n" :value="n" />
        </el-select>
        <el-button size="small" @click="showCustomizeDialog">
          {{ $t('customize') }}
        </el-button>
      </div>
    </div>
    
    <div class="bookmark-list">
      <div v-for="bookmark in sortedBookmarks" :key="bookmark.id" class="bookmark-card">
        <div class="bookmark-content">
          <div class="link-container">
            <img 
              :src="getFavicon(bookmark.url)" 
              class="favicon" 
              @error="handleFaviconError" 
              :data-url="bookmark.url"
              :alt="bookmark.title"
            >
            <div class="bookmark-info">
              <a 
                :href="bookmark.url" 
                target="_blank" 
                @click="incrementClickCount(bookmark.id)"
                class="bookmark-title"
                :title="bookmark.title"
              >
                {{ bookmark.title.length > 20 ? bookmark.title.substring(0, 20) + '...' : bookmark.title }}
              </a>
            </div>
            <div class="click-count-container">
              <el-tooltip 
                :content="$t('clicks') + ': ' + (bookmark.clicks || 0)" 
                placement="top"
                effect="light">
                <span class="click-count">
                  <el-icon class="click-icon"><Histogram /></el-icon>
                </span>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 自定义书签对话框 -->
    <el-dialog
      :title="$t('customizeBookmarks')"
      v-model="customizeDialogVisible"
      width="800px"
      class="customize-dialog"
    >
      <div class="customize-container">
        <!-- 左侧搜索面板 -->
        <div class="search-panel">
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('searchBookmarks')"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearchSubmit"
          >
            <template #append>
              <el-button 
                @click="handleSearchSubmit"
                :disabled="searchKeyword.length < 2"
                type="primary"
              >
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="search-results">
            <div v-for="bookmark in filteredBookmarks" 
                 :key="bookmark.id" 
                 class="search-item"
                 @click="addToSelected(bookmark)">
              <span class="bookmark-title">{{ bookmark.title }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧已选列表 -->
        <div class="selected-panel">
          <h4>{{ $t('selectedBookmarks') }}</h4>
          <div class="selected-list">
            <div v-for="bookmark in selectedBookmarks" 
                 :key="bookmark.id"
                 class="selected-item">
              <span class="bookmark-title">{{ bookmark.title }}</span>
              <el-button 
                type="danger" 
                size="small" 
                @click="removeFromSelected(bookmark)"
                icon="Delete"
              />
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelCustomization">{{ $t('cancel') }}</el-button>
          <el-button type="primary" @click="saveCustomization">{{ $t('confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
// 增加 Search 图标导入
import { Histogram, Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'
// 移除 draggable 导入

export default {
  name: 'NavigationManager',
  components: { 
    Histogram,
    Search // 注册 Search 组件
  },
  data() {
    return {
      bookmarkSort: 'clicks',
      bookmarkLimit: 6,
      sortedBookmarks: [],
      sortOptions: {
        'clicks': 'mostClicked',
        'recent': 'recentlyAdded',
        'weight': 'importance',
        'custom': 'customOrder' // 添加自定义排序选项
      },
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
      customizeDialogVisible: false,
      selectedBookmarks: [], // 已选中的书签ID列表
      availableBookmarks: [], // 可选择的书签列表
      isCustomMode: false, // 是否使用自定义模式
      searchKeyword: '',
      filteredBookmarks: [],
    }
  },
  methods: {
    async fetchBookmarks() {
      try {
        const params = { 
          type: 'navigation',
          param: this.bookmarkLimit.toString(),
          sort: this.bookmarkSort,
          custom_ids: this.bookmarkSort === 'custom' ? this.selectedBookmarks.join(',') : undefined
        }
        
        const response = await axios.get(getURL() + 'api/keeper/', { params })
        if(response.data.code === 200) {
          this.sortedBookmarks = response.data.data.map(bookmark => ({
            ...bookmark,
            clicks: bookmark.clicks || 0,
            weight: bookmark.weight || 0
          }))
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    async incrementClickCount(bookmarkId) {
      try {
        await axios.post(getURL() + 'api/keeper/click', {
          id: bookmarkId
        })
      } catch (error) {
        console.error('Failed to increment click count:', error)
      }
    },

    sortBookmarks(bookmarks) {
      switch(this.bookmarkSort) {
        case 'clicks':
          return bookmarks.sort((a, b) => b.clicks - a.clicks)
        case 'recent':
          return bookmarks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        case 'weight':
          return bookmarks.sort((a, b) => b.weight - a.weight)
        default:
          return bookmarks
      }
    },

    refreshBookmarks() {
      this.fetchBookmarks()
    },

    getFavicon(url) {
      try {
        const domain = new URL(url).hostname
        
        if (this.faviconCache.has(domain)) {
          return this.faviconCache.get(domain)
        }

        if (!this.faviconLoading.has(domain)) {
          this.faviconQueue.push({domain, url})
          this.startPreload()
        }

        return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"%3E%3Cpath fill="%23e0e0e0" d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13A6 6 0 118 2a6 6 0 010 12z"/%3E%3C/svg%3E'
        
      } catch {
        return ''
      }
    },

    async startPreload() {
      while (this.faviconQueue.length > 0) {
        const batch = this.faviconQueue.splice(0, 5)
        await Promise.all(batch.map(item => this.loadFavicon(item.domain, item.url)))
      }
    },

    async loadFavicon(domain, url) {
      if (this.faviconLoading.has(domain)) return
      this.faviconLoading.add(domain)

      const services = [
        `https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=${domain}&size=32`,
        `https://icon.horse/icon/${domain}`,
        `https://${domain}/favicon.ico`,
      ]

      for (const service of services) {
        try {
          const response = await fetch(service, { signal: AbortSignal.timeout(1000) })
          if (response.ok) {
            this.faviconCache.set(domain, service)
            this.faviconLoading.delete(domain)
            this.$forceUpdate()
            return
          }
        } catch {}
      }

      this.faviconCache.set(domain, 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"%3E%3Cpath fill="%23999" d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13A6 6 0 118 2a6 6 0 010 12z"/%3E%3C/svg%3E')
      this.faviconLoading.delete(domain)
      this.$forceUpdate()
    },
    
    handleFaviconError(e) {
      const domain = new URL(e.target.dataset.url).hostname
      this.faviconCache.delete(domain)
      this.faviconLoading.delete(domain)
      this.faviconQueue.push({domain, url: e.target.dataset.url})
      this.startPreload()
    
    },
    getSortLabel(value) {
      return this.$t(this.sortOptions[value] || 'mostClicked')
    },

    async showCustomizeDialog() {
      // 重置所有状态
      this.customizeDialogVisible = true
      this.availableBookmarks = []
      this.filteredBookmarks = []
      this.selectedBookmarks = [] // 清空已选列表
      
      // 只有存在已保存的自定义书签时才加载它们
      const savedBookmarks = localStorage.getItem('customBookmarks')
      if (savedBookmarks && savedBookmarks !== '[]') {
        try {
          const savedIds = JSON.parse(savedBookmarks)
          if (savedIds && savedIds.length > 0) {
            // 获取已保存的书签数据
            const response = await axios.get(getURL() + 'api/keeper/', { 
              params: { 
                type: 'navigation',
                sort: 'custom',
                custom_ids: savedIds.join(',')
              } 
            })
            
            if (response.data.code === 200) {
              // 确保返回的数据不为空
              const bookmarks = response.data.data || []
              this.selectedBookmarks = bookmarks.map(bookmark => ({
                ...bookmark,
                title: bookmark.title.length > 20 ? 
                  bookmark.title.substring(0, 20) + '...' : 
                  bookmark.title
              }))
            }
          }
        } catch (error) {
          parseBackendError(this, error)
          this.selectedBookmarks = [] // 出错时确保列表为空
        }
      }
    },

    cancelCustomization() {
      this.customizeDialogVisible = false
      // 恢复之前保存的选择
      const savedBookmarks = localStorage.getItem('customBookmarks')
      if (savedBookmarks) {
        this.selectedBookmarks = JSON.parse(savedBookmarks)
      }
    },

    async saveCustomization() {
      try {
        // 修改API路径从 'custom' 改为 'custom-order'
        const bookmarkIds = this.selectedBookmarks.map(b => b.id)
        
        await axios.post(getURL() + 'api/keeper/custom-order', {
          bookmarkIds: bookmarkIds
        })

        // 保存到本地存储
        localStorage.setItem('customBookmarks', JSON.stringify(bookmarkIds))
        
        this.customizeDialogVisible = false
        this.bookmarkSort = 'custom'
        await this.refreshBookmarks()
        
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    handleSearch(value) {
      if (!value || value.length < 2) {
        this.filteredBookmarks = []
      }
    },

    handleSearchSubmit() {
      if (!this.searchKeyword || this.searchKeyword.length < 2) {
        return
      }
      this.searchBookmarks(this.searchKeyword)
    },

    async searchBookmarks(keyword) {
      try {
        const response = await axios.get(getURL() + 'api/keeper/', {
          params: {
            type: 'search',
            param: keyword
          }
        })
        
        if(response.data.code === 200) {
          this.filteredBookmarks = response.data.data.map(bookmark => ({
            ...bookmark,
            // 限制标题长度为30个字符
            title: bookmark.title.length > 20 ? 
              bookmark.title.substring(0, 20) + '...' : 
              bookmark.title
          }))
          // 过滤掉已经选中的书签
          this.filteredBookmarks = this.filteredBookmarks.filter(
            bookmark => !this.selectedBookmarks.find(b => b.id === bookmark.id)
          )
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    async addToSelected(bookmark) {
      if (!this.selectedBookmarks.find(b => b.id === bookmark.id)) {
        // 添加书签到右侧列表
        this.selectedBookmarks.push({
          ...bookmark,
          title: bookmark.title.length > 20 ? 
            bookmark.title.substring(0, 20) + '...' : 
            bookmark.title
        })
        
        // 立即更新后端
        try {
          await axios.post(getURL() + 'api/keeper/custom-order', {
            bookmarkIds: this.selectedBookmarks.map(b => b.id)
          })
        } catch (error) {
          parseBackendError(this, error)
        }
      }
    },

    async removeFromSelected(bookmark) {
      const index = this.selectedBookmarks.findIndex(b => b.id === bookmark.id)
      if (index > -1) {
        this.selectedBookmarks.splice(index, 1)
        
        // 立即更新后端
        try {
          await axios.post(getURL() + 'api/keeper/custom-order', {
            bookmarkIds: this.selectedBookmarks.map(b => b.id)
          })
        } catch (error) {
          parseBackendError(this, error)
        }
      }
    },

    // 移除 handleDragEnd 方法
  },
  
  async mounted() {
    // 从本地存储恢复自定义选择
    const savedBookmarks = localStorage.getItem('customBookmarks')
    if (savedBookmarks) {
      this.selectedBookmarks = JSON.parse(savedBookmarks)
      this.isCustomMode = this.selectedBookmarks.length > 0
    }
    await this.fetchBookmarks()
  }
}
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.selected-text {
  margin-right: 8px;
  color: #606266;
  font-size: 14px;
}

.dialog-footer {
  padding-top: 20px;
  text-align: right;
}

.customize-container {
  display: flex;
  gap: 20px;
  height: 500px;
}

.left-panel, .right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 10px;
}

.bookmark-search-list, .selected-list {
  flex: 1;
  overflow-y: auto;
  margin-top: 10px;
}

.search-item, .selected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  margin: 4px 0;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-item:hover {
  background-color: var(--el-fill-color-light);
}

.bookmark-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bookmark-url {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: 8px;
}

.selected-item {
  background-color: var(--el-fill-color-lighter);
}

/* 自定义对话框样式 */
.customize-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.customize-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: 500px;
}

.search-panel,
.selected-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 15px;
}

.search-panel .el-input {
  margin-bottom: 15px;
}

.search-results,
.selected-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.search-item,
.selected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 4px;
  background-color: var(--el-fill-color-light);
  cursor: pointer;
  transition: all 0.2s;
}

.search-item:hover {
  background-color: var(--el-fill-color);
}

.bookmark-title {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-panel h4 {
  margin: 0 0 15px 0;
  color: var(--el-text-color-primary);
}

.dialog-footer {
  padding-top: 20px;
  text-align: right;
}
</style>