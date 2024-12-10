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
        <el-select v-model="bookmarkLimit" size="small" @change="refreshBookmarks" class="limit-select" :placeholder="$t('selectPlaceholder')" :teleported="false">
          <el-option v-for="n in [3,6,9,12]" :key="n" :label="n" :value="n" />
        </el-select>
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
              >
                {{ bookmark.title }}
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
  </div>
</template>

<script>
import { Histogram } from '@element-plus/icons-vue'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'NavigationManager',
  components: { Histogram },
  data() {
    return {
      bookmarkSort: 'clicks',
      bookmarkLimit: 6,
      sortedBookmarks: [],
      sortOptions: {
        'clicks': 'mostClicked',
        'recent': 'recentlyAdded',
        'weight': 'importance'
      },
      // 添加这些缓存相关的属性
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
    }
  },
  methods: {
    async fetchBookmarks(type, count = this.bookmarkLimit) {
      try {
        let func = 'api/keeper/'
        const params = { 
          type: type,
          param: count.toString(),
          sort: this.bookmarkSort
        }
        
        const response = await axios.get(getURL() + func, { params })
        console.log(`${type} bookmarks:`, response.data)
        if(response.data.code === 200) {
          const formattedData = response.data.data.map(bookmark => ({
            ...bookmark,
            id: bookmark.id || Math.random(),
            url: bookmark.url,
            title: bookmark.title,
            created_at: bookmark.created_at,
            clicks: bookmark.clicks || 0,
            weight: bookmark.weight || 0
          }))
          
          if(type === 'random') {
            this.sortedBookmarks = this.sortBookmarks(formattedData)
          }
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

    async refreshBookmarks() {
      await this.fetchBookmarks('random')
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
    }
  },

  async mounted() {
    await this.fetchBookmarks('random')
  }
}
</script>