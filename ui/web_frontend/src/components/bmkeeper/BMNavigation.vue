<template>
  <div class="section">
    <div class="section-header">
      <h3>{{ $t('quickNavigation') }}</h3>
      <div class="controls">
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
    
    <div class="bookmark-list" ref="bookmarkList">
      <div v-for="bookmark in sortedBookmarks" :key="bookmark.id" class="bookmark-card" :data-id="bookmark.id">
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
                :content="`${$t('clicks')}: ${(bookmark.meta && bookmark.meta.clicks) || 0}`"
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
            <!-- 添加搜索结果计数 -->
            <div v-if="filteredBookmarks.length > 0" class="search-count">
              {{ $t('foundResults', { count: filteredBookmarks.length }) }}
            </div>
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
    </el-dialog>
  </div>
</template>

<script>
import Sortable from 'sortablejs'
import { Histogram, Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'NavigationManager',
  components: { 
    Histogram,
    Search // 注册 Search 组件
  },
  data() {
    return {
      bookmarkLimit: 6,
      sortedBookmarks: [],
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
      customizeDialogVisible: false,
      selectedBookmarks: [], // 已选中的书签列表 
      searchKeyword: '',
      filteredBookmarks: [],
      sortable: null,
      draggedOrder: [], // 存储拖拽后的顺序
    }
  },
  methods: {
    async fetchBookmarks() {
      try {
        const params = { 
          type: 'navigation',
          param: this.bookmarkLimit.toString()
        }
        
        // 如果有自定义书签，添加到请求参数
        const customBookmarks = this.selectedBookmarks.map(b => b.id)
        if (customBookmarks.length > 0) {
          params.custom_ids = customBookmarks.join(',')
        }
        
        const response = await axios.get(getURL() + 'api/keeper/', { params })
        if(response.data.code === 200) {
          this.sortedBookmarks = this.sortBookmarks(response.data.data)
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
      // 如果有保存的顺序,优先使用
      const savedOrder = localStorage.getItem('bookmarkOrder')
      if (savedOrder) {
        const order = JSON.parse(savedOrder)
        return this.reorderBookmarks(bookmarks, order)
      }

      // 否则使用默认排序逻辑
      // 首先获取自定义排序的书签ID
      const customBookmarks = localStorage.getItem('customBookmarks')
      const customIds = customBookmarks ? JSON.parse(customBookmarks) : []
      
      // 分离自定义书签和其他书签
      const customBookmarksList = []
      const otherBookmarksList = []
      
      bookmarks.forEach(bookmark => {
        if (customIds.includes(bookmark.id)) {
          customBookmarksList.push(bookmark)
        } else {
          otherBookmarksList.push(bookmark)
        }
      })

      // 对其他书签进行综合排序
      otherBookmarksList.sort((a, b) => {
        // 计算综合得分: 点击次数(50%) + 最近添加(30%) + 重要程度(20%)
        const getScore = (item) => {
          const clickScore = (item.clicks || 0) * 0.5
          const timeScore = (new Date(item.created_at).getTime() / 1000000) * 0.3
          const weightScore = (item.weight || 0) * 0.2
          return clickScore + timeScore + weightScore
        }
        return getScore(b) - getScore(a)
      })

      // 合并自定义书签和排序后的其他书签
      return [...customBookmarksList, ...otherBookmarksList]
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

    async showCustomizeDialog() {
      this.customizeDialogVisible = true
      this.availableBookmarks = []
      this.filteredBookmarks = []
      
      try {
        // 使用新的API端点获取自定义书签
        const response = await axios.get(getURL() + 'api/keeper/custom-order')
        if (response.data.code === 200) {
          this.selectedBookmarks = response.data.data.map(bookmark => ({
            ...bookmark,
            title: bookmark.title.length > 20 ? 
              bookmark.title.substring(0, 20) + '...' : 
              bookmark.title
          }))
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    async saveCustomization() {
      try {
        const bookmarkIds = this.selectedBookmarks.map(b => b.id)
        
        const response = await axios.post(getURL() + 'api/keeper/custom-order', {
          bookmarkIds: bookmarkIds
        })

        if (response.data.code === 200) {
          // 保存到本地存储
          localStorage.setItem('customBookmarks', JSON.stringify(bookmarkIds))
          this.customizeDialogVisible = false
          
          // 强制重新加载书签列表
          await this.loadSelectedBookmarks()
          await this.fetchBookmarks()
        }
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
          // 获取当前已选择的书签ID列表
          const selectedIds = new Set(this.selectedBookmarks.map(b => b.id))
          
          // 过滤并处理所有搜索结果
          this.filteredBookmarks = response.data.data
            .filter(bookmark => !selectedIds.has(bookmark.id)) // 排除已选择的书签
            .map(bookmark => ({
              ...bookmark,
              title: bookmark.title.length > 20 ? 
                bookmark.title.substring(0, 20) + '...' : 
                bookmark.title
            }))
            
          // 添加日志以便调试
          console.log(`Found ${this.filteredBookmarks.length} matching bookmarks`)
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    async addToSelected(bookmark) {
      // 如果书签已经在选中列表中，则不添加
      if (this.selectedBookmarks.find(b => b.id === bookmark.id)) {
        return;
      }

      // 添加书签到右侧列表
      this.selectedBookmarks.push({
        ...bookmark,
        title: bookmark.title.length > 20 ? 
          bookmark.title.substring(0, 20) + '...' : 
          bookmark.title
      });

      // 只更新当前添加的书签的 custom_order
      try {
        await axios.post(getURL() + 'api/keeper/custom-order', {
          singleBookmark: true, // 新增标记，表示只更新单个书签
          bookmarkId: bookmark.id
        });
      } catch (error) {
        parseBackendError(this, error);
        // 发生错误时从选中列表中移除
        const index = this.selectedBookmarks.findIndex(b => b.id === bookmark.id);
        if (index > -1) {
          this.selectedBookmarks.splice(index, 1);
        }
      }
    },

    async removeFromSelected(bookmark) {
      const index = this.selectedBookmarks.findIndex(b => b.id === bookmark.id)
      if (index > -1) {
        try {
          // 调用后端API移除书签的自定义顺序
          const response = await axios.post(getURL() + 'api/keeper/custom-order', {
            removeId: bookmark.id
          })
          
          if (response.data.code === 200) {
            // 从前端列表中移除
            this.selectedBookmarks.splice(index, 1)
            
            // 清除本地存储中的相关数据
            const savedBookmarks = JSON.parse(localStorage.getItem('customBookmarks') || '[]')
            const updatedBookmarks = savedBookmarks.filter(id => id !== bookmark.id)
            localStorage.setItem('customBookmarks', JSON.stringify(updatedBookmarks))
            
            // 移除拖拽顺序相关数据
            localStorage.removeItem('bookmarkOrder')
            
            // 重新加载书签列表
            await this.fetchBookmarks()
          }
        } catch (error) {
          parseBackendError(this, error)
          // 发生错误时重新加载已选书签列表
          await this.loadSelectedBookmarks()
        }
      }
    },

    async loadSelectedBookmarks() {
      this.selectedBookmarks = []
      
      try {
        const response = await axios.get(getURL() + 'api/keeper/', {
          params: {
            type: 'navigation',
            param: 'all',
            sort: 'custom'
          }
        })
        
        if (response.data.code === 200 && response.data.data) {
          const bookmarks = response.data.data.filter(bm => 
            bm && bm.id && bm.meta && bm.meta.custom_order === true
          )
          
          this.selectedBookmarks = bookmarks.map(bookmark => ({
            ...bookmark,
            title: bookmark.title.length > 20 ? 
              bookmark.title.substring(0, 20) + '...' : 
              bookmark.title
          }))
          
          // 更新本地存储
          const validIds = bookmarks.map(b => b.id)
          localStorage.setItem('customBookmarks', JSON.stringify(validIds))
        }
      } catch (error) {
        parseBackendError(this, error)
        this.selectedBookmarks = []
        localStorage.removeItem('customBookmarks')
      }
    },

    initSortable() {
      if (this.$refs.bookmarkList) {
        this.sortable = Sortable.create(this.$refs.bookmarkList, {
          animation: 150,
          onEnd: this.handleDragEnd
        })
      }
    },

    handleDragEnd(evt) {
      // 获取拖拽后的顺序
      const cards = this.$refs.bookmarkList.getElementsByClassName('bookmark-card')
      const newOrder = Array.from(cards).map(card => card.dataset.id)
      
      // 保存新顺序
      this.draggedOrder = newOrder
      localStorage.setItem('bookmarkOrder', JSON.stringify(newOrder))
      
      // 重新排序书签列表
      this.sortedBookmarks = this.reorderBookmarks(this.sortedBookmarks, newOrder)
    },

    reorderBookmarks(bookmarks, order) {
      // 创建ID到书签的映射
      const bookmarkMap = new Map(bookmarks.map(b => [b.id, b]))
      
      // 按照保存的顺序重新排列
      return order
        .filter(id => bookmarkMap.has(id)) // 只保留存在的书签
        .map(id => bookmarkMap.get(id))
    },
  },
  
  async mounted() {
    await this.loadSelectedBookmarks() // 使用新方法加载已选书签
    await this.fetchBookmarks()
    this.$nextTick(() => {
      this.initSortable()
    })
  },
  
  updated() {
    // 组件更新后重新初始化拖拽
    this.$nextTick(() => {
      this.initSortable()
    })
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

.bookmark-card {
  cursor: move; /* 添加移动光标样式 */
}

.search-count {
  padding: 8px 12px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  border-bottom: 1px solid var(--el-border-color-light);
}
</style>