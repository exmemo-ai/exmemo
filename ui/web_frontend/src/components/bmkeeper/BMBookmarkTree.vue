<template>
  <div class="bookmark-tree-container">
    <div class="tree-header">
      <div class="header-left">
        <h3>{{ $t('bookmarkTree') }}</h3>
        <!--
        <el-button-group>
          <el-button @click="expandAll">
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <el-button @click="collapseAll">
            <el-icon><ArrowUp /></el-icon>
          </el-button>
        </el-button-group>
        -->
      </div>
      <el-button type="primary" @click="refreshTree">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <el-tree
      ref="bookmarkTreeRef"
      :data="treeData"
      :props="defaultProps"
      node-key="id"
      :expand-on-click-node="true"
      :default-expanded-keys="['bookmarkBar']"
      v-model:expanded-keys="expandedKeys"
      :indent="16"
      draggable
      :allow-drop="handleAllowDrop"
      :allow-drag="handleAllowDrag"
      @node-drop="handleDrop"
      @node-drag-start="handleDragStart"
      @node-drag-end="handleDragEnd"
      @node-click="handleNodeClick"
      @node-drag-over="handleDragOver"
      @node-drag-leave="handleDragLeave">
      <template #default="{ node, data }">
        <div class="tree-node" 
             :class="{ 'drag-over': isDraggingOver === node.data.id }"
             :style="{ paddingLeft: node.level * 16 + 'px' }">
          <template v-if="data.type === 'folder'">
            <el-icon><Folder /></el-icon>
            <span class="folder-name">
              {{ formatLabel(data.title) }}
            </span>
            <span class="bookmark-count">({{ data.children?.length || 0 }})</span>
          </template>
          <template v-else>
            <img :src="getFavicon(data.url)" class="favicon" @error="handleFaviconError">
            <a :href="data.url" 
               target="_blank" 
               class="bookmark-link"
               :title="`${data.title}\n${data.url}`"
               @click.stop>
              {{ formatLabel(data.title) }}
            </a>
            <div class="bookmark-actions">
              <el-tooltip :content="$t('editBookmark')" placement="top">
                <el-button size="small" @click.stop="handleEdit(data)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('deleteBookmark')" placement="top">
                <el-button size="small" type="danger" @click.stop="handleDelete(node, data)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </div>
      </template>
    </el-tree>

    <!-- 添加拖拽提示 -->
    <div v-if="dragTip.show" 
         class="drag-tip" 
         :style="{ left: dragTip.x + 'px', top: dragTip.y + 'px' }">
      {{ dragTip.text }}
    </div>

    <!-- 编辑书签对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="$t('editBookmark')"
      width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item :label="$t('title')">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item :label="$t('url')">
          <el-input v-model="editForm.url" />
        </el-form-item>
        <el-form-item :label="$t('folder')">
          <el-input v-model="editForm.folder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('cancel') }}</el-button>
        <el-button type="primary" @click="submitEdit">{{ $t('confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Folder, Edit, Delete, Refresh/*, ArrowDown, ArrowUp*/ } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'BookmarkTree',
  components: { Folder, Edit, Delete, Refresh/*, ArrowDown, ArrowUp*/ },
  
  setup() {
    const bookmarkTreeRef = ref(null)
    return {
      bookmarkTreeRef
    }
  },
  
  data() {
    return {
      treeData: [],
      expandedKeys: [], // 初始化为空数组，稍后会在 fetchBookmarks 中设置
      defaultProps: {
        children: 'children',
        label: 'title'
      },
      editDialogVisible: false,
      editForm: {
        id: null,
        title: '',
        url: '',
        folder: ''
      },
      faviconCache: new Map(),
      faviconQueue: [],
      faviconLoading: new Set(),
      defaultFavicon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="%23909399" d="M17,3H7A2,2 0 0,0 5,5V21L12,18L19,21V5C19,3.89 18.1,3 17,3Z"/></svg>',
      isDragging: false, // 添加拖拽状态标记
      isDraggingOver: null, // 添加当前悬停节点的ID
      dragTip: {
        show: false,
        text: '',
        x: 0,
        y: 0
      }
    }
  },

  methods: {
    _getBookmarkBarPath() {
      const isEnglish = this.$i18n.locale === 'en';
      return isEnglish ? '/chrome/bookmarks bar/' : '/chrome/书签栏/';
    },

    convertToTree(flatData) {
      // console.log('Original flat data:', flatData);
      
      const folderMap = new Map();
      const root = {
        id: 'bookmarkBar',
        title: this.$t('bookmarkBar'),
        children: [],
        type: 'folder',
      };

      const bookmarkBarPath = this._getBookmarkBarPath();
      folderMap.set(bookmarkBarPath, root);

      // 修改过滤和排序逻辑
      const sortedData = flatData
        .filter(item => {
          const isValid = item.folder && (
            item.folder.includes('书签栏') || 
            item.folder.includes('bookmarks bar')
          );
          return isValid;
        })
        .sort((a, b) => {
          const aPath = a.folder.split('/').filter(Boolean);
          const bPath = b.folder.split('/').filter(Boolean);
          return aPath.length - bPath.length;
        });

      sortedData.forEach(item => {
        // 1. 清理路径,移除前缀
        const fullPath = item.folder;
        let cleanPath = fullPath
          .replace(/^\/chrome\/书签栏\/|^chrome\/书签栏\//, '')
          .replace(/^\/bookmarks bar\/|^bookmarks bar\//, '');
        
        // 2. 处理标题中的斜杠问题 - 检查标题是否出现在路径末尾
        const titleWithoutSlash = item.title.replace(/\//g, '___SLASH___');
        if (cleanPath.endsWith(item.title)) {
          cleanPath = cleanPath.slice(0, -item.title.length);
        } else if (cleanPath.endsWith('/')) {
          cleanPath = cleanPath.slice(0, -1);
        }

        // 3. 分割路径,过滤空字符串
        const pathParts = cleanPath
          .split('/')
          .filter(Boolean)
          .map(part => part.trim());

        // 4. 如果没有文件夹路径,直接添加到根节点
        if (pathParts.length === 0) {
          const bookmarkNode = {
            id: item.id,
            title: item.title, 
            url: item.url,
            type: 'bookmark',
            folder: item.folder,
            created_at: item.created_at
          };
          root.children.push(bookmarkNode);
          return;
        }

        // 5. 递归构建文件夹结构
        let currentNode = root;
        let currentPath = this._getBookmarkBarPath();

        for (const folderName of pathParts) {
          // 跳过与标题相同的文件夹名称,避免重复分类
          if (folderName === item.title) continue;
          
          currentPath += folderName + '/';
          let folderNode = folderMap.get(currentPath);
          
          if (!folderNode) {
            folderNode = {
              id: currentPath,
              title: folderName,
              children: [],
              type: 'folder',
              created_at: item.created_at
            };
            folderMap.set(currentPath, folderNode);
            currentNode.children.push(folderNode);
          }
          currentNode = folderNode;
        }

        // 6. 添加书签节点,恢复标题中的斜杠
        const bookmarkNode = {
          id: item.id,
          title: item.title,
          url: item.url,
          type: 'bookmark', 
          folder: item.folder,
          created_at: item.created_at
        };
        currentNode.children.push(bookmarkNode);
      });

      // 修改排序函数
      const sortNodes = (nodes) => {
        nodes.sort((a, b) => {
          // 文件夹依然优先
          if (a.type !== b.type) {
            return a.type === 'folder' ? -1 : 1;
          }
          
          // 无论是文件夹还是书签，都按创建时间排序
          const timeA = new Date(a.created_at || 0).getTime();
          const timeB = new Date(b.created_at || 0).getTime();
          
          if (timeA === timeB) {
            // 时间相同时按名称排序
            return a.title.localeCompare(b.title);
          }
          
          return timeA - timeB;
        });

        // 递归排序子节点
        nodes.forEach(node => {
          if (node.children) {
            sortNodes(node.children);
          }
        });
      };

      sortNodes(root.children);

      return [root];
    },

    // 获取书签数据
    async fetchBookmarks() {
      try {
        const response = await axios.get(getURL() + 'api/keeper/', {
          params: { type: 'tree' }
        });
        
        console.log('API Response:', response.data);
        
        if (response.data.code === 200) {
          const flatData = response.data.data;
          
          // 验证数据格式
          if (!Array.isArray(flatData)) {
            console.error('Invalid data format: expected array');
            return;
          }
          
          // 验证数据字段
          const isValidData = flatData.every(item => 
            item.id && 
            item.title && 
            typeof item.folder === 'string'
          );
          
          if (!isValidData) {
            console.error('Invalid data structure:', flatData);
            return;
          }

          this.treeData = this.convertToTree(flatData);

          // 立即设置展开状态，不使用 nextTick
          const rootNode = this.treeData[0];
          const expandKeys = ['bookmarkBar'];
          
          if (rootNode?.children?.length > 0) {
            const firstFolder = rootNode.children.find(node => node.type === 'folder');
            if (firstFolder) {
              expandKeys.push(firstFolder.id);
            }
          }
          
          // 直接设置展开状态
          this.expandedKeys = expandKeys;
          
          // 确保展开状态生效
          if (this.bookmarkTreeRef) {
            this.bookmarkTreeRef.value?.setExpandedKeys(expandKeys);
          }
        }
      } catch (error) {
        console.error('Error fetching bookmarks:', error);
        parseBackendError(this, error);
      }
    },
    refreshTree() {
      this.fetchBookmarks()
    },
    async submitEdit() {
      try {
        const response = await axios.put(getURL() + 'api/keeper/', {
          id: this.editForm.id,
          title: this.editForm.title
        })

        if (response.data.code === 200) {
          // 更新本地数据而不是重新获取
          this.updateBookmarkInTree(this.treeData[0], response.data.data)
          ElMessage.success(this.$t('updateSuccess'))
          this.editDialogVisible = false
        }
      } catch (error) {
        parseBackendError(this, error)
      }
    },

    // 添加新方法: 在树中更新书签
    updateBookmarkInTree(node, updatedBookmark) {
      if (node.id === updatedBookmark.id) {
        Object.assign(node, {
          ...node,
          title: updatedBookmark.title,
          url: updatedBookmark.url,
          folder: updatedBookmark.folder
        })
        return true
      }
      
      if (node.children) {
        for (const child of node.children) {
          if (this.updateBookmarkInTree(child, updatedBookmark)) {
            return true
          }
        }
      }
      return false
    },

    async handleDelete(node, data) {
      try {
        await ElMessageBox.confirm(
          this.$t('confirmDelete'),
          this.$t('warning'),
          { type: 'warning' }
        )

        const response = await axios.delete(getURL() + 'api/keeper/', {
          params: { id: data.id }
        })

        if (response.data.code === 200) {
          ElMessage.success(this.$t('deleteSuccess'))
          this.fetchBookmarks()
        }
      } catch (error) {
        if (error !== 'cancel') {
          parseBackendError(this, error)
        }
      }
    },
    
    getFavicon(url) {
      if (!url) return this.defaultFavicon;
      try {
        const urlObj = new URL(url);
        return `${urlObj.protocol}//${urlObj.hostname}/favicon.ico`;
      } catch (e) {
        return this.defaultFavicon;
      }
    },

    handleFaviconError(event) {
      event.target.src = this.defaultFavicon;
      event.target.onerror = null;
    },

    formatLabel(label) {
      // 添加空值检查
      if (!label) return '';
      return label.length > 50 ? label.substring(0, 47) + '...' : label;
    },

    /*
    expandAll() {
      const allKeys = [];
      const collectKeys = (nodes) => {
        nodes.forEach(node => {
          if (node.type === 'folder') {
            allKeys.push(node.id);
            if (node.children?.length) {
              collectKeys(node.children);
            }
          }
        });
      };
      
      collectKeys(this.treeData);
      this.expandedKeys = allKeys;
    },

    collapseAll() {
      this.expandedKeys = ['bookmarkBar'];
    },
    */

    getAllFolderKeys(nodes) {
      const keys = new Set(['bookmarkBar']);
      const addFolderKeys = (items) => {
        items.forEach(node => {
          if (node.type === 'folder') {
            keys.add(node.id);
            if (node.children && node.children.length > 0) {
              addFolderKeys(node.children);
            }
          }
        });
      };
      addFolderKeys(nodes);
      return Array.from(keys);
    },

    // 判断是否允许拖拽
    handleAllowDrag(node) {
      // 允许拖拽书签和文件夹，但根节点不能拖动
      return node.data.id !== 'bookmarkBar'
    },

    // 判断是否允许放置
    handleAllowDrop(draggingNode, dropNode, type) {
      // 不允许拖到根节点之前或之后
      if (dropNode.data.id === 'bookmarkBar' && type !== 'inner') {
        return false
      }
      
      // 书签节点不能作为父节点
      if (dropNode.data.type === 'bookmark' && type === 'inner') {
        return false
      }

      // 检查是否形成循环引用
      if (draggingNode.data.type === 'folder' && type === 'inner') {
        let parent = dropNode.parent;
        while (parent) {
          if (parent.data.id === draggingNode.data.id) {
            return false; // 避免循环引用
          }
          parent = parent.parent;
        }
      }

      return true
    },

    // 处理拖拽完成事件
    async handleDrop(draggingNode, dropNode, type) {
      this.isDragging = false;
      const bookmarkBarPath = this._getBookmarkBarPath();
      
      // 构建新的文件夹路径
      let newFolder = '';
      if (type === 'inner') {
        newFolder = dropNode.data.id === 'bookmarkBar' ? 
          bookmarkBarPath : 
          `${bookmarkBarPath}${dropNode.data.title}/`;
      } else {
        const parentNode = dropNode.parent;
        newFolder = parentNode.data.id === 'bookmarkBar' ? 
          bookmarkBarPath : 
          `${bookmarkBarPath}${parentNode.data.title}/`;
      }

      try {
        if (draggingNode.data.type === 'folder') {
          // 处理文件夹移动
          const bookmarks = this.getAllBookmarksInFolder(draggingNode.data);
          const updatePromises = bookmarks.map(bookmark => {
            // 计算每个书签的新路径
            const oldPath = bookmark.folder;
            const oldFolderPath = `${bookmarkBarPath}${draggingNode.data.title}/`;
            const newPath = oldPath.replace(oldFolderPath, newFolder);
            
            return axios.put(getURL() + 'api/keeper/', {
              id: bookmark.id,
              title: bookmark.title,
              url: bookmark.url,
              folder: newPath
            });
          });

          await Promise.all(updatePromises);
        } else {
          // 处理单个书签移动
          await axios.put(getURL() + 'api/keeper/', {
            id: draggingNode.data.id,
            title: draggingNode.data.title,
            url: draggingNode.data.url,
            folder: newFolder
          });
        }

        ElMessage.success(this.$t('updateSuccess'));
        this.fetchBookmarks();
      } catch (error) {
        parseBackendError(this, error);
        this.fetchBookmarks();
      }
    },

    handleDragStart() {
      this.isDragging = true;
    },

    handleDragEnd() {
      this.isDragging = false;
      this.isDraggingOver = null;
      this.dragTip.show = false;
    },

    handleDragOver(draggingNode, dropNode, ev) {
      if (dropNode.data.type === 'folder') {
        this.isDraggingOver = dropNode.data.id;
        // 更新提示文本和位置
        this.dragTip = {
          show: true,
          text: this.$t('dragToFolder', {
            title: draggingNode.data.title,
            target: dropNode.data.title
          }),
          x: ev.clientX + 15,
          y: ev.clientY + 15
        };
      }
    },

    handleDragLeave(draggingNode, dropNode) {
      if (this.isDraggingOver === dropNode.data.id) {
        this.isDraggingOver = null;
        this.dragTip.show = false;
      }
    },
    
    // 获取文件夹下所有书签
    getAllBookmarksInFolder(folderNode) {
      const bookmarks = [];
      const traverse = (node) => {
        if (node.type === 'bookmark') {
          bookmarks.push(node);
        } else if (node.children) {
          node.children.forEach(traverse);
        }
      };
      traverse(folderNode);
      return bookmarks;
    },

    // 计算新的文件夹路径
    calculateNewPath(oldPath, oldFolderId, newFolderId) {
      return oldPath.replace(oldFolderId, newFolderId);
    },

    handleNodeClick(data, node) {
      // 如果正在拖拽中，不触发点击事件
      if (this.isDragging) return;
      
      if (data.type === 'bookmark') {
        window.open(data.url, '_blank')
      }
    },

    handleEdit(data) {
      this.editForm = { ...data }
      this.editDialogVisible = true
    },
  },

  mounted() {
    this.fetchBookmarks()
  }
}
</script>

<style scoped>
.bookmark-tree-container {
  padding: 20px;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 28px;
}

.favicon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.bookmark-link {
  color: #606266;
  text-decoration: none;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: calc(100% - 100px);
}

.bookmark-link:hover {
  color: #409EFF;
}

/* 移除之前的 .bookmark-link 相关样式 */

.bookmark-count {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.bookmark-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.tree-node:hover .bookmark-actions {
  opacity: 1;
}

.folder-name {
  font-weight: 500;
}

.el-tree-node__content {
  height: auto !important;
  padding: 4px 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.el-tree :deep(.is-dragging) {
  opacity: 0.5;
}

.el-tree :deep(.el-tree-node__drop-prev),
.el-tree :deep(.el-tree-node__drop-next),
.el-tree :deep(.el-tree-node__drop-inner) {
  border: 2px dashed #409EFF;
  margin: 4px 0;
}

.tree-node.drag-over {
  background-color: var(--el-color-primary-light-8);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.tree-node.drag-over .folder-name {
  color: var(--el-color-primary);
}

.drag-tip {
  position: fixed;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  white-space: nowrap;
}
</style>