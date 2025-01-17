<template>
  <div class="section search-section">
    <div class="search-header">
      <h3 class="search-title">{{ $t('searchTitle') }}</h3>
      <el-input
        v-model="searchQuery"
        :placeholder="$t('search')"
        class="search-input"
        size="medium"
        @keyup.enter="searchBookmarks">
        <template #append>
          <el-button @click="searchBookmarks" type="primary">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 搜索结果部分 -->
    <div v-if="searchResults.length > 0 || hasSearched" class="search-results">
      <ul v-if="searchResults.length > 0" class="result-list">
        <li v-for="item in processedResults" :key="item.id" class="result-item">
          <div class="result-content">
            <div class="result-header">
              <img :src="getFavicon(item.url)" class="favicon" @error="handleFaviconError" :data-url="item.url">
              <a :href="item.url" target="_blank" class="result-title" v-html="highlightKeyword(item.title)"></a>
            </div>
            <div class="result-details">
              <span class="result-domain">{{ item.domain }}</span>
              <p v-if="item.description" class="result-description">{{ item.description }}</p>
            </div>
          </div>
        </li>
      </ul>
      <div v-else class="no-results">
        {{ $t('noResults') }}
      </div>
    </div>
  </div>
</template>

<script>
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'SearchManager',
  components: { Search },
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      hasSearched: false,
      // 添加searchTitle属性
      searchTitle: this.$t('searchTitle'),
      faviconServiceIndex: 0,
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
    }
  },
  computed: {
    processedResults() {
      return this.searchResults.map(item => ({
        ...item,
        domain: this.extractDomain(item.url)
      }))
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
    highlightKeyword(title) {
      if (!this.searchQuery || !title) return title;
      const keywords = this.searchQuery.trim().split(/\s+/);
      let highlightedTitle = title;
      keywords.forEach(keyword => {
        if (keyword) {
          const regex = new RegExp(keyword, 'gi');
          highlightedTitle = highlightedTitle.replace(regex, match => 
            `<span class="highlight-keyword">${match}</span>`);
        }
      });
      return highlightedTitle;
    },
    extractDomain(url) {
      try {
        return new URL(url).hostname
      } catch {
        return ''
      }
    }
  }
}
</script>

<style>
.link-container a.result-title {
  color: #333;
  text-decoration: none;
}

/* 关键词高亮样式 */
.link-container a.result-title span.highlight-keyword {
  color: #409EFF;
  font-weight: bold;
}

/* 搜索结果容器 */
.search-results-container {
  margin-top: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 16px;
}

/* 搜索结果列表 */
.search-results-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

/* 搜索结果项 */
.search-result-item {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s ease;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: var(--el-fill-color-light);
}

/* 结果内容布局 */
.result-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-title {
  font-size: 15px;
  color: var(--el-text-color-primary);
  text-decoration: none;
  line-height: 1.4;
}

.result-description {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.result-url {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.result-title span.highlight-keyword {
  color: var(--el-color-primary);
  font-weight: bold;
}

.no-results {
  text-align: center;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.favicon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 2px;
}

.search-results {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.result-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.result-item {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.result-item:last-child {
  border-bottom: none;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-title {
  font-size: 15px;
  color: var(--el-text-color-primary);
  text-decoration: none;
  line-height: 1.4;
}

.result-title:hover {
  text-decoration: underline;
}

.result-title span.highlight-keyword {
  color: var(--el-color-primary);
  font-weight: bold;
}

.result-details {
  margin-left: 26px;
}

.result-domain {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: block;
  margin-bottom: 4px;
}

.result-description {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.favicon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 2px;
}

.no-results {
  text-align: center;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.result-title {
  color: #333333 !important;
  text-decoration: none;
}

.result-title span.highlight-keyword {
  color: var(--el-color-primary);
  font-weight: bold;
}
</style>