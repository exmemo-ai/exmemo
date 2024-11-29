<template>
  <div class="desktop-width">
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
          <div class="section-header">
            <h3>{{ $t('quickNavigation') }}</h3>
            <div class="controls">
              <el-select 
                v-model="bookmarkSort" 
                size="small" 
                @change="refreshBookmarks">
                <template #prefix>
                  <span class="selected-text">{{ $t('sortBy') }}{{ getSortLabel(bookmarkSort) }}</span>
                </template>
                <el-option 
                  v-for="(label, value) in sortOptions" 
                  :key="value"
                  :label="$t(label)"
                  :value="value" />
              </el-select>
              <el-select 
                v-model="bookmarkLimit" 
                size="small" 
                @change="refreshBookmarks"
                class="limit-select"
                :placeholder="$t('selectPlaceholder')"
                :teleported="false">
                <el-option v-for="n in [3,6,9,12]" :key="n" :label="n" :value="n" />
              </el-select>
            </div>
          </div>
          <!-- 快速导航的结果列表 -->
          <div class="bookmark-list">
            <div 
              v-for="bookmark in sortedBookmarks" 
              :key="bookmark.id" 
              class="bookmark-card">
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

        <!-- 稍后阅读部分 -->
        <div class="section">
          <h3>{{ $t('readLater') }}</h3>
          <div class="bookmark-list">
            <el-card v-for="bookmark in recentReadLater" :key="bookmark.id" class="bookmark-card">
              <div class="link-container">
                <div class="bookmark-left">
                  <img :src="getFavicon(bookmark.url)" class="favicon" @error="handleFaviconError" :data-url="bookmark.url">
                  <div class="bookmark-content">
                    <a :href="bookmark.url" target="_blank" class="bookmark-title">{{ bookmark.title }}</a>
                    <p v-if="bookmark.summary" class="bookmark-summary">{{ bookmark.summary }}</p>
                  </div>
                </div>
                <div class="bookmark-actions">
                  <el-tooltip :content="$t('addSummary')" placement="top">
                    <el-button size="small" @click="handleAddSummary(bookmark)">
                      <el-icon><DocumentAdd /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip :content="$t('moveToBookmark')" placement="top">
                    <el-button size="small" @click="handleMoveToBookmarks(bookmark)">
                      <el-icon><FolderAdd /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip :content="$t('deleteBookmark')" placement="top">
                    <el-button size="small" type="danger" @click="handleDelete(bookmark)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>
            </el-card>
          </div>
          <!-- 添加分页组件 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="readLaterPage"
              v-model:page-size="readLaterPageSize"
              :page-sizes="[5, 10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              :total="readLaterTotal"
              @size-change="handleReadLaterSizeChange"
              @current-change="handleReadLaterPageChange"
            />
          </div>
        </div>
      </el-container>
    </el-main>
  </div>
</template>

<script>
import AppNavbar from '@/components/support/AppNavbar.vue'
import { Search, Histogram, DocumentAdd, FolderAdd, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'
import './BMManagerStyles.css'

export default {
  components: {
    AppNavbar,
    Search,
    Histogram,
    DocumentAdd,
    FolderAdd,
    Delete
  },
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      randomBookmarks: [],
      recentReadLater: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
      hasSearched: false,
      faviconServiceIndex: 0,
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
      bookmarkSort: 'clicks',
      bookmarkLimit: 6,
      sortedBookmarks: [],
      sortOptions: {
        'clicks': 'mostClicked',
        'recent': 'recentlyAdded',
        'weight': 'importance'
      },
      readLaterPage: 1,
      readLaterPageSize: 10,
      readLaterTotal: 0,
    }
  },
  computed: {
    currentSortName() {
      const sortMap = {
        'clicks': this.$t('mostClicked'),
        'recent': this.$t('recentlyAdded'),
        'weight': this.$t('importance')
      }
      return sortMap[this.bookmarkSort] || this.$t('mostClicked')
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

    async fetchBookmarks(type, count = this.bookmarkLimit) {
      try {
        let func = 'api/keeper/'
        const params = { 
          type: type,
          param: count.toString(),
          sort: this.bookmarkSort
        }
        
        // 为稍后阅读添加分页参数
        if (type === 'readlater') {
          params.page = this.readLaterPage
          params.page_size = this.readLaterPageSize
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
          } else if(type === 'readlater') {
            this.recentReadLater = response.data.data
            this.readLaterTotal = response.data.total
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
    },
    getDomain(url) {
      try {
        return new window.URL(url).hostname
      } catch {
        return ''
      }
    },
    // 添加分页处理方法
    handleReadLaterSizeChange(size) {
      this.readLaterPageSize = size
      this.fetchBookmarks('readlater')
    },
    
    handleReadLaterPageChange(page) {
      this.readLaterPage = page
      this.fetchBookmarks('readlater')
    },

    // 添加总结对话框
    async handleAddSummary(bookmark) {
      try {
        const { value: summary } = await ElMessageBox.prompt(this.$t('inputSummary'), this.$t('addSummaryTitle'), {
          confirmButtonText: this.$t('confirm'),
          cancelButtonText: this.$t('cancel'),
          inputType: 'textarea',
          inputValue: bookmark.summary || ''
        })
        
        if (summary !== null) {
          const response = await axios.post(getURL() + 'api/keeper/summary', {
            id: bookmark.id,
            summary: summary
          })
          
          if (response.data.code === 200) {
            ElMessage.success(this.$t('summaryAdded'))
            await this.fetchBookmarks('readlater')
          }
        }
      } catch (error) {
        if (error !== 'cancel') {
          parseBackendError(this, error)
        }
      }
    },

    // 移动到书签文件夹
    async handleMoveToBookmarks(bookmark) {
      try {
        const { value: folder } = await ElMessageBox.prompt(this.$t('inputFolderPath'), this.$t('moveToBookmarkTitle'), {
          confirmButtonText: this.$t('confirm'),
          cancelButtonText: this.$t('cancel'),
          inputValue: '/'
        })
        
        if (folder !== null) {
          const response = await axios.post(getURL() + 'api/keeper/move', {
            id: bookmark.id,
            folder: folder
          })
          
          if (response.data.code === 200) {
            ElMessage.success(this.$t('movedToBookmark'))
            await this.fetchBookmarks('readlater')
          }
        }
      } catch (error) {
        if (error !== 'cancel') {
          parseBackendError(this, error)
        }
      }
    },

    // 删除待读项
    async handleDelete(bookmark) {
      try {
        const confirmed = await ElMessageBox.confirm(
          this.$t('confirmDeleteReadLater'),
          this.$t('warningTitle'),
          {
            confirmButtonText: this.$t('confirm'),
            cancelButtonText: this.$t('cancel'),
            type: 'warning'
          }
        )
        
        if (confirmed) {
          const response = await axios.delete(getURL() + 'api/keeper/', {
            params: { id: bookmark.id }
          })
          
          if (response.data.code === 200) {
            ElMessage.success(this.$t('deleted'))
            // 从当前列表中移除该项
            this.recentReadLater = this.recentReadLater.filter(b => b.id !== bookmark.id)
            // 更新总数
            this.readLaterTotal -= 1
            // 如果当前页已空,且不是第一页,则跳转到上一页
            if (this.recentReadLater.length === 0 && this.readLaterPage > 1) {
              this.readLaterPage -= 1
              await this.fetchBookmarks('readlater')
            }
          }
        }
      } catch (error) {
        if (error !== 'cancel') {
          parseBackendError(this, error)
        }
      }
    }
  },

  async mounted() {
    await this.fetchBookmarks('random')
    await this.fetchBookmarks('readlater')
  },

  beforeUnmount() {
  }
}
</script>

<style>
/* BMManagerStyles.css 中添加 */
.bookmark-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.bookmark-summary {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.4;
}

.bookmark-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
