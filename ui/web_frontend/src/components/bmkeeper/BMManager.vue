<template>
  <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
    <div style="display: flex; flex-direction: column;">
      <app-navbar :title="$t('bookmarkManager')" :info="'BMManager'" />
    </div>
    <el-main class="main-container">
      <el-container style="display: flex; flex-direction: column; gap: 20px;">
        <!-- 搜索框部分 -->
        <div class="section search-section">
          <div class="search-header">
            <h3 class="search-title">{{ $t('searchTitle') }}</h3>
            <el-input
              v-model="searchQuery"
              :placeholder="$t('search')"
              class="search-input"
              size="medium">
              <template #append>
                <el-button @click="searchBookmarks" type="primary">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
        </div>

        <!-- 搜索结果部分 -->
        <div v-if="searchResults.length > 0 || hasSearched" class="section">
          <ul v-if="searchResults.length > 0" class="result-grid">
            <li v-for="item in searchResults" :key="item.id" class="result-item">
              <div class="link-container">
                <img :src="getFavicon(item.url)" class="favicon" @error="handleFaviconError" :data-url="item.url">
                <a :href="item.url" target="_blank" class="result-title">{{ item.title }}</a>
              </div>
              <p v-if="item.description" class="result-description">{{ item.description }}</p>
            </li>
          </ul>
          <div v-else class="no-results">
            {{ $t('noResults') }}
          </div>
        </div>

        <!-- 快速导航部分 -->
        <div class="section">
          <h3>{{ $t('quickNavigation') }}</h3>
          <div class="bookmark-list">
            <el-card v-for="bookmark in randomBookmarks" :key="bookmark.id" class="bookmark-card">
              <div class="link-container">
                <img :src="getFavicon(bookmark.url)" class="favicon" @error="handleFaviconError" :data-url="bookmark.url">
                <a :href="bookmark.url" target="_blank">{{ bookmark.title }}</a>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 稍后阅读部分 -->
        <div class="section">
          <h3>{{ $t('readLater') }}</h3>
          <div class="bookmark-list">
            <el-card v-for="bookmark in recentReadLater" :key="bookmark.id" class="bookmark-card">
              <div class="link-container">
                <img :src="getFavicon(bookmark.url)" class="favicon" @error="handleFaviconError" :data-url="bookmark.url">
                <a :href="bookmark.url" target="_blank">{{ bookmark.title }}</a>
              </div>
            </el-card>
          </div>
        </div>
      </el-container>
    </el-main>
  </div>
</template>

<script>
import AppNavbar from '@/components/support/AppNavbar.vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  components: {
    AppNavbar,
    Search
  },
  data() {
    return {
      isMobile: false,
      searchQuery: '',
      searchResults: [],
      randomBookmarks: [],
      recentReadLater: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
      hasSearched: false,
      faviconServiceIndex: 0,
      faviconCache: new Map(), // 缓存图标
      faviconQueue: [], // 预加载队列
      faviconLoading: new Set(), // 记录加载状态
    }
  },
  methods: {
    async searchBookmarks() {
      if(!this.searchQuery.trim()) {
        return
      }
      
      try {
        const response = await axios.get(getURL() + 'api/keeper/', {
          params: {
            type: 'search',
            param: this.searchQuery
          }
        })
        
        if(response.data.code === 200) {
          this.searchResults = response.data.data
          this.hasSearched = true
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    async fetchBookmarks(type, count = 5) {
      try {
        let func = 'api/keeper/'
        const params = { 
          type: type,
          param: count.toString()  // param传递数量参数
        }
        const response = await axios.get(getURL() + func, { params })
        console.log(`${type} bookmarks:`, response.data) // 添加日志
        if(response.data.code === 200) {
          const formattedData = response.data.data.map(bookmark => ({
            ...bookmark,
            id: bookmark.id || Math.random(), // 为列表项提供唯一key
            url: bookmark.url,
            title: bookmark.title,
            created_at: bookmark.created_at
          }))
          
          if(type === 'random') {
            this.randomBookmarks = formattedData
          } else if(type === 'readlater') {
            this.recentReadLater = formattedData  
          }
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    handleResize() {
      this.isMobile = window.innerWidth < 768;
    },

    getFavicon(url) {
      try {
        const domain = new URL(url).hostname
        
        // 1. 检查内存缓存
        if (this.faviconCache.has(domain)) {
          return this.faviconCache.get(domain)
        }

        // 2. 添加到预加载队列
        if (!this.faviconLoading.has(domain)) {
          this.faviconQueue.push({domain, url})
          this.startPreload()
        }

        // 3. 返回占位图标
        return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"%3E%3Cpath fill="%23e0e0e0" d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13A6 6 0 118 2a6 6 0 010 12z"/%3E%3C/svg%3E'
        
      } catch {
        return ''
      }
    },

    async startPreload() {
      // 批量处理预加载队列
      while (this.faviconQueue.length > 0) {
        const batch = this.faviconQueue.splice(0, 5) // 每次处理5个
        await Promise.all(batch.map(item => this.loadFavicon(item.domain, item.url)))
      }
    },

    async loadFavicon(domain, url) {
      if (this.faviconLoading.has(domain)) return
      this.faviconLoading.add(domain)

      // 按优先级尝试不同的图标服务
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
            // 强制更新视图
            this.$forceUpdate()
            return
          }
        } catch {}
      }

      // 所有服务都失败时使用默认图标
      this.faviconCache.set(domain, 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"%3E%3Cpath fill="%23999" d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13A6 6 0 118 2a6 6 0 010 12z"/%3E%3C/svg%3E')
      this.faviconLoading.delete(domain)
      this.$forceUpdate()
    },
    
    handleFaviconError(e) {
      const domain = new URL(e.target.dataset.url).hostname
      // 从缓存中移除并重试加载
      this.faviconCache.delete(domain)
      this.faviconLoading.delete(domain)
      this.faviconQueue.push({domain, url: e.target.dataset.url})
      this.startPreload()
    
    }
  },

  async mounted() {
    this.isMobile = window.innerWidth < 768
    window.addEventListener('resize', this.handleResize)
    this.handleResize()

    // 获取初始数据
    await this.fetchBookmarks('random')
    await this.fetchBookmarks('readlater')
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
  }
}
</script>

<style scoped>
.section {
  margin: 5px 0; 
  padding: 15px;
  border-radius: 8px;
  background-color: var(--el-bg-color);
}

.bookmark-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

.bookmark-card {
  padding: 10px;
}

.bookmark-card a {
  text-decoration: none;
  color: var(--el-text-color-primary);
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bookmark-card:hover a {
  text-decoration: underline;
}

.search-input {
  max-width: 600px;
  margin-bottom: 0;  /* 从15px改为0 */
}

.full-width {
    width: 100%;
}

.desktop-width {
    max-width: 100%;
    margin: 0 auto;
}

.main-container {
    max-width: 80%;
    margin: 0 auto;
}

@media (max-width: 767px) {
    .desktop-width {
        max-width: 100%;
    }
    .main-container {
        max-width: 100%;
    }
}

.search-results {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}

.result-card {
  padding: 10px;
}

.result-title a {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}

.result-meta {
  font-size: 0.9em;
  color: var(--el-text-color-secondary);
  margin-top: 5px;
}

.no-results {
  text-align: center;
  padding: 20px;
  color: var(--el-text-color-secondary);
}

.result-list {
  list-style: none;
  padding: 0;
  margin: 15px 0;
}

.result-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.result-title {
  font-size: 14px;
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: normal;
}

.result-title:hover {
  text-decoration: underline;
}

.result-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin: 4px 0 0 24px;
  line-height: 1.4;
}

.result-source {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}

.result-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 5px;
}

.link-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.favicon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  background: #f5f5f5;
  border-radius: 3px;
  transition: opacity 0.2s;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
  list-style: none;
  padding: 0;
  margin: 15px 0;
}

@media (max-width: 767px) {
  .result-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

.search-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-title {
  margin: 0;
  white-space: nowrap;
}

.search-input {
  width: 100%;
}

@media (max-width: 767px) {
  .search-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .search-input {
    width: 100%;
  }
}
</style>
