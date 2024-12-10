<template>
  <div class="section">
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
</template>

<script>
import { DocumentAdd, FolderAdd, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'ReadLaterManager',
  components: { DocumentAdd, FolderAdd, Delete },
  data() {
    return {
      recentReadLater: [],
      readLaterPage: 1,
      readLaterPageSize: 10,
      readLaterTotal: 0,
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set()
    }
  },
  methods: {
    async fetchBookmarks(type, count = this.readLaterPageSize) {
      try {
        let func = 'api/keeper/'
        const params = { 
          type: type,
          param: count.toString(),
          page: this.readLaterPage,
          page_size: this.readLaterPageSize
        }
        
        const response = await axios.get(getURL() + func, { params })
        console.log(`${type} bookmarks:`, response.data)
        if(response.data.code === 200) {
          this.recentReadLater = response.data.data
          this.readLaterTotal = response.data.total
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
            this.recentReadLater = this.recentReadLater.filter(b => b.id !== bookmark.id)
            this.readLaterTotal -= 1
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
    },

    handleReadLaterSizeChange(size) {
      this.readLaterPageSize = size
      this.fetchBookmarks('readlater')
    },
    
    handleReadLaterPageChange(page) {
      this.readLaterPage = page
      this.fetchBookmarks('readlater')
    }
  },

  async mounted() {
    await this.fetchBookmarks('readlater')
  }
}
</script>