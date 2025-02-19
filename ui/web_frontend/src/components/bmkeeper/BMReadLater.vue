<template>
  <div class="section">
    <div class="web-source">{{ $t('webSource') }}</div>
    <div class="bookmark-list">
      <el-card v-for="bookmark in mergedBookmarks" :key="bookmark.groupId" class="bookmark-card">
        <div class="link-container">
          <div class="bookmark-left">
            <img :src="getFavicon(bookmark.url)" class="favicon" @error="handleFaviconError" :data-url="bookmark.url">
            <div class="bookmark-content">
              <a :href="bookmark.url" target="_blank" class="bookmark-title">
                {{ bookmark.title }}
                <span v-if="bookmark.count > 1" class="duplicate-count">({{ bookmark.count }})</span>
              </a>
              <div class="meta-content">
                <div v-if="bookmark.tags" class="tags-container">
                  <el-tag
                    v-for="tag in bookmark.tags.split(',')"
                    :key="tag"
                    size="small"
                    class="bookmark-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <p v-if="bookmark.summary" class="bookmark-summary">{{ bookmark.summary }}</p>
              </div>
            </div>
          </div>
          <div class="bookmark-actions">
            <el-tooltip :content="$t('editBookmark')" placement="top">
              <el-button size="small" @click="handleEdit(bookmark)">
                <el-icon><Edit /></el-icon>
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

    <!-- add edit dialog-->
    <el-dialog
      v-model="editDialogVisible"
      :title="$t('editBookmark')"
      width="500px"
      class="bm-dialog bookmark-edit-dialog"
      append-to-body
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item :label="$t('bookmarkTitle')">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item :label="$t('tags')" class="tags-form-item">
          <div class="tag-input-container">
            <div class="tag-list">
              <el-tag
                v-for="tag in editForm.tags"
                :key="tag"
                closable
                size="small"
                @close="removeTag(tag)"
              >
                {{ tag }}
              </el-tag>
            </div>
            <el-input
              v-model="tagInput"
              size="small"
              :placeholder="$t('enterTags')"
              @keyup.enter="handleTagInputConfirm"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">{{ $t('cancel') }}</el-button>
          <el-button type="primary" @click="submitEdit">{{ $t('confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- add files dialog -->
    <el-dialog
      v-if="showFolderDialog"
      v-model="showFolderDialog"
      :title="$t('selectFolder')"
      width="500px"
      class="bm-dialog folder-select-dialog"
    >
      <el-input
        v-model="folderSearchInput"
        :placeholder="$t('searchFolder')"
        @input="handleFolderSearch"
      />
      <div class="folder-list">
        <el-scrollbar height="300px">
          <div
            v-for="folder in filteredFolders"
            :key="folder"
            class="folder-item"
            @click="handleFolderSelect(folder)"
          >
            <!-- 显示处理后的文件夹路径 -->
            {{ formatFolderDisplay(folder) }}
          </div>
        </el-scrollbar>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { FolderAdd, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'ReadLaterManager',
  components: { FolderAdd, Delete, Edit },
  data() {
    return {
      recentReadLater: [],
      readLaterPage: 1,
      readLaterPageSize: 10,
      readLaterTotal: 0,
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
      editDialogVisible: false,
      editForm: {
        id: null,
        relatedIds: [],
        title: '',
        tags: [],
      },
      tagInput: '',
      showFolderDialog: false,
      folderSearchInput: '',
      allFolders: [],
      filteredFolders: [],
    }
  },
  computed: {
    mergedBookmarks() {
      const bookmarkMap = new Map();
      
      this.recentReadLater.forEach(bookmark => {
        const key = bookmark.url;
        const existing = bookmarkMap.get(key);
        
        if (!existing || new Date(bookmark.updated_time) > new Date(existing.updated_time)) {
          bookmarkMap.set(key, {
            ...bookmark,
            groupId: key,
            count: existing ? existing.count + 1 : 1,
            relatedIds: existing ? [...existing.relatedIds, bookmark.id] : [bookmark.id],
            tags: bookmark.tags || '',
            summary: bookmark.raw || ''
          });
        } else {
          existing.count++;
          existing.relatedIds.push(bookmark.id);
        }
      });
      
      return Array.from(bookmarkMap.values());
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

    async handleMoveToBookmarks(bookmark) {
      this.currentBookmark = bookmark;
      await this.getFolders();
      this.showFolderDialog = true;
    },

    async getFolders() {
      try {
        const response = await axios.get(getURL() + 'api/keeper/folders');
        if (response.data.code === 200) {
          this.allFolders = ['/', ...response.data.data];
          this.filteredFolders = this.allFolders;
        }
      } catch (error) {
        parseBackendError(this, error);
      }
    },

    formatFolderDisplay(folder) {
      if (folder === '/') return folder;
      return folder;
    },
    
    handleFolderSearch(value) {
      if (!value) {
        this.filteredFolders = this.allFolders;
      } else {
        this.filteredFolders = this.allFolders.filter(folder => 
          this.formatFolderDisplay(folder).toLowerCase().includes(value.toLowerCase())
        );
      }
    },

    async handleFolderSelect(folder) {
      try {
        const movePromises = this.currentBookmark.relatedIds.map(id =>
          axios.post(getURL() + 'api/keeper/move/', {
            id: id,
            folder: folder
          })
        );
        
        await Promise.all(movePromises);
        ElMessage.success(this.$t('movedToBookmark'));
        this.showFolderDialog = false;
        await this.fetchBookmarks('readlater');
      } catch (error) {
        parseBackendError(this, error);
      }
    },

    async handleDelete(bookmark) {
      try {
        const confirmed = await ElMessageBox.confirm(
          bookmark.count > 1 
            ? this.$t('confirmDeleteMultipleReadLater', { count: bookmark.count })
            : this.$t('confirmDeleteReadLater'),
          this.$t('warningTitle'),
          {
            confirmButtonText: this.$t('confirm'),
            cancelButtonText: this.$t('cancel'),
            type: 'warning'
          }
        )
        
        if (confirmed) {
          const deletePromises = bookmark.relatedIds.map(id => 
            axios.delete(getURL() + 'api/keeper/', { params: { id } })
          );
          
          await Promise.all(deletePromises);
          ElMessage.success(this.$t('deleted'));
          this.readLaterTotal -= bookmark.count;
          
          if (this.recentReadLater.length === 0 && this.readLaterPage > 1) {
            this.readLaterPage -= 1;
          }
          await this.fetchBookmarks('readlater');
        }
      } catch (error) {
        if (error !== 'cancel') {
          parseBackendError(this, error)
        }
      }
    },

    handleEdit(bookmark) {
      this.editForm = {
        id: bookmark.id,
        title: bookmark.title,
        tags: bookmark.tags ? bookmark.tags.split(',') : []
      }
      this.editDialogVisible = true
    },

    async submitEdit() {
      try {
        const response = await axios.put(getURL() + 'api/keeper/', {
          type: 'readlater', 
          id: this.editForm.id,
          title: this.editForm.title,
          tags: this.editForm.tags.join(',')
        })

        if (response.data.code === 200) {
          ElMessage.success(this.$t('updateSuccess'))
          this.editDialogVisible = false
          
          const updatedBookmark = response.data.data
          this.recentReadLater = this.recentReadLater.map(bm => {
            if (bm.id === updatedBookmark.id) {
              return {
                ...bm,
                ...updatedBookmark,
                updated_time: updatedBookmark.updated_time
              }
            }
            return bm
          })
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    handleReadLaterSizeChange(size) {
      this.readLaterPageSize = size
      this.fetchBookmarks('readlater')
    },
    
    handleReadLaterPageChange(page) {
      this.readLaterPage = page
      this.fetchBookmarks('readlater')
    },

    handleTagInputConfirm() {
      const value = this.tagInput.trim()
      if (value && !this.editForm.tags.includes(value)) {
        this.editForm.tags.push(value)
      }
      this.tagInput = ''
    },
    
    removeTag(tag) {
      this.editForm.tags = this.editForm.tags.filter(t => t !== tag)
    },
  },

  async mounted() {
    await this.fetchBookmarks('readlater')
  }
}
</script>

<style scoped>
.duplicate-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: 4px;
}

.bookmark-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.bookmark-card {
  transition: all 0.3s ease;
}

.bookmark-card:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.link-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.bookmark-left {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.bookmark-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bookmark-title {
  font-size: 15px;
  color: var(--el-text-color-primary);
  text-decoration: none;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bookmark-title:hover {
  color: var(--el-color-primary);
}

.meta-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bookmark-tag {
  font-size: 11px;
  padding: 0 6px;
  height: 20px;
  line-height: 18px;
  background-color: var(--el-color-info-light-9);
  color: var(--el-text-color-secondary);
  border: none;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.title-and-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.bookmark-summary {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin: 0;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tag-input-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-list :deep(.el-tag) {
  margin-right: 4px;
  margin-bottom: 4px;
}

.tag-input-container :deep(.el-input) {
  width: 100%;
}

.web-source {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 16px;
}

.bookmark-actions {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
}

/* add moble */
@media (max-width: 768px) {
  .link-container {
    flex-direction: column;
    gap: 12px;
  }

  .bookmark-title {
    white-space: normal;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    line-height: 1.4;
    max-height: 2.8em;
    word-break: break-word;
  }

  .bookmark-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
    padding-top: 8px;
    border-top: 1px solid var(--el-border-color-lighter);
  }

  .bookmark-actions .el-button {
    flex: 0;
    padding: 6px; 
    min-width: auto; 
    max-width: none; 
  }

  .bookmark-actions .el-button :deep(.el-icon) {
    font-size: 14px;
  }
}
</style>