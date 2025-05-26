<template>
  <div class="bookmark-tree-container">
    <div class="common-header">
      <div class="header-content">
        <el-tree
          ref="bookmarkTreeRef"
          :data="treeData"
          :props="defaultProps"
          node-key="id"
          :expand-on-click-node="false"
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
                 :class="{ 
                   'drag-over': isDraggingOver === node.data.id,
                   'is-dragging': isDragging && node.data.id === draggedNodeId,
                   'can-drag': data.id !== 'bookmarkBar'
                 }"
                 :data-id="data.id">
              <template v-if="data.type === 'folder'">
                <el-icon><Folder /></el-icon>
                <span class="tree-folder-name">{{ formatLabel(data.title) }}</span>
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
        <el-button type="primary" class="refresh-button" @click="refreshTree">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- add drag -->
    <div v-if="dragTip.show" 
         class="tree-drag-tip" 
         :style="{ left: dragTip.x + 'px', top: dragTip.y + 'px' }">
      {{ dragTip.text }}
    </div>

    <!-- edit dialog -->
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
import { ref } from 'vue'
import { Folder, Edit, Delete, Refresh} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'

export default {
  name: 'BookmarkTree',
  components: { Folder, Edit, Delete, Refresh},
  
  setup() {
    const bookmarkTreeRef = ref(null)
    return {
      bookmarkTreeRef
    }
  },
  
  data() {
    return {
      treeData: [],
      expandedKeys: [],
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
      defaultFavicon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="%23909399" d="M17,3H7A2,2 0 0,0 5,5V21L12,18L19,21V5C19,3.89 18.1,3 17,3Z"/></svg>',
      isDragging: false, 
      isDraggingOver: null, 
      dragTip: {
        show: false,
        text: '',
        x: 0,
        y: 0
      },
      draggedNodeId: null,
      touchData: {
        isDragging: false,
        startX: 0,
        startY: 0,
        currentTarget: null,
        dragElement: null,
        dropTarget: null,
        lastX: 0,
        lastY: 0,
        sourceNode: null
      }
    }
  },

  methods: {
    _getBookmarkBarPath() {
      const isEnglish = this.$i18n.locale === 'en';
      return isEnglish ? '/chrome/bookmarks bar/' : '/chrome/书签栏/';
    },

    convertToTree(flatData) {
      
      const folderMap = new Map();
      const root = {
        id: 'bookmarkBar',
        title: this.$t('bookmarkBar'),
        children: [],
        type: 'folder',
      };

      const bookmarkBarPath = this._getBookmarkBarPath();
      folderMap.set(bookmarkBarPath, root);

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
        const fullPath = item.folder;
        let cleanPath = fullPath
          .replace(/^\/chrome\/书签栏\/|^chrome\/书签栏\//, '')
          .replace(/^\/bookmarks bar\/|^bookmarks bar\//, '');
        
        const titleWithoutSlash = item.title.replace(/\//g, '___SLASH___');
        if (cleanPath.endsWith(item.title)) {
          cleanPath = cleanPath.slice(0, -item.title.length);
        } else if (cleanPath.endsWith('/')) {
          cleanPath = cleanPath.slice(0, -1);
        }

        const pathParts = cleanPath
          .split('/')
          .filter(Boolean)
          .map(part => part.trim());

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

        let currentNode = root;
        let currentPath = this._getBookmarkBarPath();

        for (const folderName of pathParts) {
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

      const sortNodes = (nodes) => {
        nodes.sort((a, b) => {
          if (a.type !== b.type) {
            return a.type === 'folder' ? -1 : 1;
          }

          const timeA = new Date(a.created_at || 0).getTime();
          const timeB = new Date(b.created_at || 0).getTime();
          
          if (timeA === timeB) {
            return a.title.localeCompare(b.title);
          }
          
          return timeA - timeB;
        });

        nodes.forEach(node => {
          if (node.children) {
            sortNodes(node.children);
          }
        });
      };

      sortNodes(root.children);

      return [root];
    },

    async fetchBookmarks() {
      try {
        const response = await axios.get(getURL() + 'api/keeper/', {
          params: { type: 'tree' }
        });
        
        console.log('API Response:', response.data);
        
        if (response.data.code === 200) {
          const flatData = response.data.data;
          
          if (!Array.isArray(flatData)) {
            console.error('Invalid data format: expected array');
            return;
          }

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

          const rootNode = this.treeData[0];
          const expandKeys = ['bookmarkBar'];
          
          if (rootNode?.children?.length > 0) {
            const firstFolder = rootNode.children.find(node => node.type === 'folder');
            if (firstFolder) {
              expandKeys.push(firstFolder.id);
            }
          }
          
          this.expandedKeys = expandKeys;
          
          if (this.bookmarkTreeRef) {
            this.bookmarkTreeRef.value?.setExpandedKeys(expandKeys);
          }
        }
      } catch (error) {
        console.error('Error fetching bookmarks:', error);
        parseBackendError(error);
      }
    },
    refreshTree() {
      this.fetchBookmarks()
    },
    async submitEdit() {
      try {

        console.log('Submitting edit form:', this.editForm)

        const requestData = {
          id: this.editForm.id,
          title: this.editForm.title,
          url: this.editForm.url,
          folder: this.editForm.folder,
          type: 'tree'
        }
        
        console.log('Request data:', requestData)
        
        const response = await axios.put(getURL() + 'api/keeper/', requestData)

        if (response.data.code === 200) {
          this.updateBookmarkInTree(this.treeData[0], response.data.data)
          ElMessage.success(this.$t('updateSuccess'))
          this.editDialogVisible = false
          await this.refreshTree()
        }
      } catch (error) {
        parseBackendError(error)
      }
    },

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
          parseBackendError(error)
        }
      }
    },
    
    getFavicon(url) {
      if (!url) return this.defaultFavicon;
      try {
        const urlObj = new URL(url);
        if (urlObj.protocol === 'file:') {
          return this.defaultFavicon;
        }
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
      if (!label) return '';
      return label.length > 50 ? label.substring(0, 47) + '...' : label;
    },

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

    handleAllowDrag(node) {
      return node.data.id !== 'bookmarkBar'
    },

    handleAllowDrop(draggingNode, dropNode, type) {
      if (dropNode.data.id === 'bookmarkBar' && type !== 'inner') {
        return false
      }
      
      if (dropNode.data.type === 'bookmark' && type === 'inner') {
        return false
      }

      if (draggingNode.data.type === 'folder' && type === 'inner') {
        let parent = dropNode.parent;
        while (parent) {
          if (parent.data.id === draggingNode.data.id) {
            return false;
          }
          parent = parent.parent;
        }
      }

      return true
    },

    async handleDrop(draggingNode, dropNode, type) {
      this.isDragging = false;
      const bookmarkBarPath = this._getBookmarkBarPath().replace(/^\//, '');
      
      let newBaseFolder = '';
      if (type === 'inner') {
        newBaseFolder = dropNode.data.id === 'bookmarkBar' ? 
          bookmarkBarPath : 
          `${bookmarkBarPath}${dropNode.data.title}/`;
      } else {
        const parentNode = dropNode.parent;
        newBaseFolder = parentNode.data.id === 'bookmarkBar' ? 
          bookmarkBarPath : 
          `${bookmarkBarPath}${parentNode.data.title}/`;
      }

      try {
        if (draggingNode.data.type === 'folder') {
          const bookmarks = this.getAllBookmarksInFolder(draggingNode.data);
          const draggedFolderName = draggingNode.data.title;
          
          const updatePromises = bookmarks.map(bookmark => {
            const oldBasePath = `${bookmarkBarPath}`;
            let relativePath = bookmark.folder.replace(oldBasePath, '');
            
            const pathParts = relativePath.split('/');
            const bookmarkTitle = pathParts.pop(); 
            const lastFolderParts = pathParts
              .slice(pathParts.indexOf(draggedFolderName)) 
              .join('/');

            const newPath = `${newBaseFolder}${lastFolderParts}/${bookmarkTitle}`;
            
            return axios.put(getURL() + 'api/keeper/', {
              id: bookmark.id,
              title: bookmark.title,
              url: bookmark.url,
              folder: newPath.replace(/\/+/g, '/')
            });
          });

          await Promise.all(updatePromises);
        } else {
          // detal with bookmark
          await axios.put(getURL() + 'api/keeper/', {
            id: draggingNode.data.id,
            title: draggingNode.data.title,
            url: draggingNode.data.url,
            folder: `${newBaseFolder}${draggingNode.data.title}`.replace(/\/+/g, '/')
          });
        }

        ElMessage.success(this.$t('updateSuccess'));
        this.fetchBookmarks();
      } catch (error) {
        parseBackendError(error);
        this.fetchBookmarks();
      }
    },

    handleDragStart(node) {
      this.isDragging = true
      this.draggedNodeId = node.data.id
      this.isLongPress = false
      document.body.classList.add('is-dragging')
    },

    handleDragEnd() {
      this.isDragging = false
      this.draggedNodeId = null
      this.isDraggingOver = null
      this.dragTip.show = false
      document.body.classList.remove('is-dragging')
    },

    handleDragOver(draggingNode, dropNode, ev) {
      if (dropNode.data.type === 'folder') {
        this.isDraggingOver = dropNode.data.id;
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

    handleNodeClick(data, node, e) {
      if (this.isLongPress) {
        this.isLongPress = false
        return
      }

      if (this.isDragging) return
      
      if (data.type === 'bookmark') {
        window.open(data.url, '_blank')
      } else {
        node.expanded = !node.expanded
      }
    },

    handleEdit(data) {

      console.log('Editing bookmark:', data)
      this.editForm = {
        id: data.id,
        title: data.title,
        url: data.url || data.addr,
        folder: data.folder || data.path
      }

      console.log('Edit form data:', this.editForm)
      this.editDialogVisible = true
    },

    findTreeNode(id) {
      if (!id || !this.treeData || !this.treeData.length) {
        console.warn('Invalid input for findTreeNode:', { id, treeData: this.treeData })
        return null
      }

      const traverse = (nodes, parent = null) => {
        for (const node of nodes) {
          if (node.id === id) {
            return {
              data: node,
              parent: parent,
              children: node.children || [],
              level: parent ? parent.level + 1 : 0
            }
          }
          if (node.children && node.children.length > 0) {
            const found = traverse(node.children, {
              data: node,
              children: node.children,
              level: parent ? parent.level + 1 : 0
            })
            if (found) return found
          }
        }
        return null
      }

      const result = traverse(this.treeData)
      console.log('findTreeNode result:', { id, result })
      return result
    },

    initTouchEvents() {
      const treeEl = this.$refs.bookmarkTreeRef?.$el
      if (treeEl) {
        treeEl.addEventListener('touchstart', this.onTouchStart, { passive: false })
        treeEl.addEventListener('touchmove', this.onTouchMove, { passive: false })
        treeEl.addEventListener('touchend', this.onTouchEnd)
      }
    },
    removeTouchEvents() {
      const treeEl = this.$refs.bookmarkTreeRef?.$el
      if (treeEl) {
        treeEl.removeEventListener('touchstart', this.onTouchStart)
        treeEl.removeEventListener('touchmove', this.onTouchMove)
        treeEl.removeEventListener('touchend', this.onTouchEnd)
      }
    },
    onTouchStart(e) {
      if (e.touches.length !== 1) return
      
      const touch = e.touches[0]
      const target = e.target.closest('.tree-node')
      if (!target || target.dataset.id === 'bookmarkBar') return
      
      const nodeId = target.dataset.id
      const foundNode = this.findTreeNode(nodeId)
      
      if (!foundNode) {
        console.error('Node not found:', nodeId)
        return
      }
      
      console.log('Found node:', foundNode)
      
      this.touchData = {
        isDragging: true,
        startX: touch.clientX,
        startY: touch.clientY,
        currentTarget: target,
        sourceNode: foundNode,
        dragElement: this.createDragPreview(target),
        dropTarget: null,
        lastX: touch.clientX,
        lastY: touch.clientY
      }

      target.classList.add('is-dragging')
      document.body.classList.add('is-dragging')
      e.preventDefault()
    },

    
    onTouchMove(e) {
      if (!this.touchData.isDragging) return
      e.preventDefault()

      const touch = e.touches[0]
      const { dragElement, startX, startY } = this.touchData

      const deltaX = touch.clientX - startX
      const deltaY = touch.clientY - startY
      dragElement.style.transform = `translate3d(${deltaX}px, ${deltaY}px, 0)`

      const elementsAtPoint = document.elementsFromPoint(touch.clientX, touch.clientY)
      const dropTarget = elementsAtPoint.find(el => 
        el.classList.contains('tree-node') && 
        el !== this.touchData.currentTarget
      )

      if (dropTarget) {
        if (this.touchData.dropTarget) {
          this.touchData.dropTarget.classList.remove('drag-over')
        }
        dropTarget.classList.add('drag-over')
        this.touchData.dropTarget = dropTarget
      }

      this.touchData.lastX = touch.clientX
      this.touchData.lastY = touch.clientY
    },

    onTouchEnd() {
      if (!this.touchData.isDragging) return

      const { currentTarget, dropTarget, sourceNode, dragElement } = this.touchData

      if (dropTarget) {
        const targetId = dropTarget.dataset.id
        const targetNode = this.findTreeNode(targetId)

        if (targetNode && sourceNode && sourceNode.data) { 

          const dropType = this.determineDropType(dropTarget, targetNode.data, this.touchData.lastY)
          
          if (this.handleAllowDrop(sourceNode, targetNode, dropType)) {
            this.handleDrop(sourceNode, targetNode, dropType)
          }
        }

        dropTarget.classList.remove('drag-over')
      }

      if (dragElement) {
        dragElement.remove()
      }
      currentTarget.classList.remove('is-dragging')
      document.body.classList.remove('is-dragging')

      // 重置触摸数据
      this.touchData = {
        isDragging: false,
        startX: 0,
        startY: 0,
        currentTarget: null,
        dragElement: null,
        dropTarget: null,
        lastX: 0,
        lastY: 0,
        sourceNode: null
      }
    },

    createDragPreview(target) {
      const clone = target.cloneNode(true)
      const rect = target.getBoundingClientRect()
      
      Object.assign(clone.style, {
        position: 'fixed',
        left: rect.left + 'px',
        top: rect.top + 'px',
        width: rect.width + 'px',
        backgroundColor: 'var(--el-color-primary-light-9)',
        opacity: '0.8',
        zIndex: '9999',
        pointerEvents: 'none',
        transition: 'transform 0.1s'
      })

      document.body.appendChild(clone)
      return clone
    },

    determineDropType(dropTarget, targetData, y) {
      const rect = dropTarget.getBoundingClientRect()
      const relativeY = y - rect.top
      const threshold = rect.height * 0.3

      if (targetData.type === 'folder' && targetData.id !== 'bookmarkBar') {
        return 'inner'
      }
      
      if (relativeY < threshold) {
        return 'before'
      } else if (relativeY > rect.height - threshold) {
        return 'after'
      }

      return 'inner'
    },
  },

  mounted() {
    this.fetchBookmarks()
    this.initTouchEvents()
  },

  beforeUnmount() {
    this.removeTouchEvents()
  }
}
</script>

<style scoped>
.common-header {
  justify-content: space-between;
}

.tree-node {
  display: flex;
  gap: 8px;
  width: 70%;
}


.tree-node:hover .bookmark-actions {
    opacity: 1;
  }

.bookmark-actions {
  opacity: 0;
  margin-left: 8px;
}

.tree-folder-name {
  font-weight: 500;
}


.el-tree-node__content {
  height: auto !important;
}


.el-tree :deep(.is-dragging) {
  opacity: 0.5;
}

.el-tree :deep(.el-tree-node__drop-inner) {
  border: 2px dashed #409EFF;
}


.tree-node.drag-over {
  background-color: var(--el-color-primary-light-8);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}


.tree-node.drag-over .tree-folder-name {
  color: var(--el-color-primary);
}


.tree-drag-tip {
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

.header-content {
  display: flex;
  align-items: flex-start;
  width: 100%;
  position: relative;
}

.refresh-button {
  position: absolute;
  right: 0;
  top: 0;
  z-index: 1;
}


@media screen and (max-width: 768px) {
  .bookmark-tree-container {
    padding: 0;
    max-width: 100%;
    margin: 0;
  }
  
  .common-header {
    padding: 8px;
    margin-bottom: 8px;
    align-items: center;
    justify-content: space-between;
  }

  :deep(.el-tree) {
    padding: 0 8px;
  }

  .tree-node {
    padding: 12px 8px;
    width: 100%;
    font-size: 14px;
  }

  .tree-node.can-drag::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 1;
    pointer-events: none;
  }

  :global(body.is-dragging) {
    overflow: hidden;
    touch-action: none;
  }


  :deep(.el-button) {
    padding: 4px;
    font-size: 12px;
  }

  :deep(.el-button + .el-button) {
    margin-left: 4px;
  }
  
  .favicon {
    width: 14px;
    height: 14px;
  }

  .bookmark-actions {
    gap: 4px;
  }

  .tree-node {
    touch-action: none;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
  }

  .tree-node.is-dragging {
    opacity: 0.3;
  }

  .tree-node.drag-over {
    border: 2px dashed var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    margin: 4px 0;
  }
}

.tree-node.can-drag {
  touch-action: none;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
}

.tree-node.is-dragging {
  opacity: 0.8;
  background: var(--el-color-primary-light-9);
  transform: scale(1.02);
  z-index: 10;
}

.tree-node.drag-over {
  border: 2px dashed var(--el-color-primary);
  background: var(--el-color-primary-light-8);
}
</style>