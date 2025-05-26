<template>
  <div class="section search-section">
    <div class="common-header">
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

    <!-- result part -->
    <div v-if="searchResults.length > 0 || hasSearched" class="search-results">
      <ul v-if="searchResults.length > 0" class="search-result-list">
        <li v-for="item in processedResults" :key="item.id" class="search-result-item">
          <div class="search-result-content">
            <div class="search-result-header">
              <img :src="getFavicon(item.url)" class="favicon" @error="handleFaviconError" :data-url="item.url">
              <a :href="item.url" target="_blank" class="search-result-title" v-html="highlightKeyword(item.title)"></a>
            </div>
            <div class="search-result-details">
              <span class="search-result-domain">{{ item.domain }}</span>
              <p v-if="item.description" class="search-result-description">{{ item.description }}</p>
            </div>
          </div>
        </li>
      </ul>
      <div v-else class="search-no-results">
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
        parseBackendError(error)
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

.search-result-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-result-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-result-details {
  margin-left: 26px;
}

.search-result-title span.highlight-keyword {
  color: var(--el-color-primary);
  font-weight: bold;
}
</style>