<template>
  <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
    <div style="display: flex; flex-direction: column;">
      <app-navbar :title="$t('bookmarkManager')" :info="'BMManager'" />
    </div>
    <el-main class="main-container">
      <el-container style="display: flex; flex-direction: column;">
        <!-- 书签搜索部分 -->
        <div class="section">
          <el-input
            v-model="searchQuery"
            :placeholder="$t('searchBookmarks')"
            class="search-input">
            <template #append>
              <el-button @click="searchBookmarks">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div v-if="searchResults.length > 0" class="results-list">
            <el-card v-for="bookmark in searchResults" :key="bookmark.id" class="bookmark-card">
              <a :href="bookmark.url" target="_blank">{{ bookmark.title }}</a>
            </el-card>
          </div>
        </div>

        <!-- 快速导航部分 -->
        <div class="section">
          <h3>{{ $t('quickNavigation') }}</h3>
          <div class="bookmark-list">
            <el-card v-for="bookmark in randomBookmarks" :key="bookmark.id" class="bookmark-card">
              <a :href="bookmark.url" target="_blank">{{ bookmark.title }}</a>
            </el-card>
          </div>
        </div>

        <!-- 稍后阅读部分 -->
        <div class="section">
          <h3>{{ $t('readLater') }}</h3>
          <div class="bookmark-list">
            <el-card v-for="bookmark in recentReadLater" :key="bookmark.id" class="bookmark-card">
              <a :href="bookmark.url" target="_blank">{{ bookmark.title }}</a>
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
import axios from 'axios'
import { getURL } from '@/components/support/conn'

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
      recentReadLater: []
    }
  },
  methods: {
    async searchBookmarks() {
      if (this.searchQuery) {
        const formData = new FormData()
        formData.append('type', 'search')
        formData.append('param', this.searchQuery.toString())
        
        try {
          const response = await axios.post(getURL() + 'api/keeper/', formData, {
            timeout: 10000,
            withCredentials: true,
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          if (response.data.status === 'success') {
            this.searchResults = response.data.bookmarks
          }
        } catch (error) {
          console.error('Failed to search bookmarks:', error)
        }
      }
    },
    handleResize() {
      this.isMobile = window.innerWidth < 768;
    },
  },
  async mounted() {
    this.isMobile = window.innerWidth < 768;
    window.addEventListener('resize', this.handleResize);
    this.handleResize();
    try {
      // 获取随机书签
      const randomFormData = new FormData()
      randomFormData.append('type', 'random')
      randomFormData.append('param', '5')
      const randomResponse = await axios.post(getURL() + 'api/keeper/', randomFormData, {
        timeout: 10000,
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (randomResponse.data.status === 'success') {
        this.randomBookmarks = randomResponse.data.bookmarks
      }

      // 获取稍后阅读书签
      const readLaterFormData = new FormData()
      readLaterFormData.append('type', 'readlater')
      readLaterFormData.append('param', '5')
      const readLaterResponse = await axios.post(getURL() + 'api/keeper/', readLaterFormData, {
        timeout: 10000,
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (readLaterResponse.data.status === 'success') {
        this.recentReadLater = readLaterResponse.data.bookmarks
      }
    } catch (error) {
      console.error('Failed to load bookmarks:', error)
    }
  }
}
</script>

<style scoped>
.section {
  margin: 20px 0;
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
}

.search-input {
  max-width: 600px;
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
</style>
