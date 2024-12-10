<template>
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
    }
  }
}
</script>