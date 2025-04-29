<template>
    <div class="app-container">
        <el-container style="flex: 0; width: 100%;">
            <app-navbar ref="navbar" :title="t('dataManagement')" :info="'DataManager2'"/>
        </el-container>
        <el-container style="flex: 1; width: 100%; overflow: hidden;">
            <el-aside class="file-tree-aside" :class="{ 'collapse-aside': isCollapse }" :style="{ width: computedAsideWidth }">
                <div class="toggle-button-collapse" @click="toggleCollapse">
                    <el-icon>
                        <Fold v-if="!isCollapse"/>
                        <Expand v-else/>
                    </el-icon>
                </div>
                <div class="tree-header">
                    <el-text class="tree-title">{{ t('tree.fileTree') }}</el-text>
                    <el-button class="icon-button" @click="refreshTree">
                        <el-icon>
                            <Refresh />
                        </el-icon>
                    </el-button>
                </div>
                <el-tree ref="treeRef" :data="treeData" :props="defaultProps" :load="loadNode" lazy draggable
                    :allow-drag="allowDrag" :allow-drop="allowDrop" @node-drop="handleDrop"
                    @node-click="handleNodeClick" :highlight-current="true" :expand-on-click-node="false"
                    @node-contextmenu="handleContextMenu">
                    <template #default="{ node, data }">
                        <span class="custom-tree-node">
                            <el-icon v-if="data.is_folder">
                                <Folder />
                            </el-icon>
                            <el-icon v-else>
                                <Document />
                            </el-icon>
                            <span>{{ node.label }}</span>
                        </span>
                    </template>
                </el-tree>
            </el-aside>

            <div class="resizer" @mousedown="onResizerMouseDown" @touchstart="onResizerMouseDown"></div>

            <el-main class="main-container list-options">
                <div class="header-buttons">
                    <div class="filter-section">
                        <div class="filter-item">
                            <div class="label-container">
                                <el-text>{{ t('data') }}</el-text>
                            </div>
                            <div class="select-container">
                                <el-select v-if="mounted && etype_options.length" v-model="etype_value"
                                    :placeholder="t('selectPlaceholder')" @change="handleEtypeChange">
                                    <el-option v-for="item in etype_options" :key="item.value" :label="item.label"
                                        :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </div>
                    </div>
                    <div class="action-buttons" v-if="currentNode && !currentNode.is_folder">
                        <template v-if="etype_value === 'file'">
                            <el-button size="small" @click="download" :title="t('download')">
                                <el-icon><Download /></el-icon>
                            </el-button>
                            <el-button size="small" @click="viewContent" :title="t('view')">
                                <el-icon><View /></el-icon>
                            </el-button>
                        </template>
                        <template v-else-if="etype_value === 'note'">
                            <el-button size="small" @click="viewContent" :title="t('view')">
                                <el-icon><View /></el-icon>
                            </el-button>
                            <el-button size="small" @click="editNote" :title="t('edit')">
                                <el-icon><Edit /></el-icon>
                            </el-button>
                        </template>
                        <template v-else-if="etype_value === 'web'">
                            <el-button size="small" @click="viewContent" :title="t('view')">
                                <el-icon><View /></el-icon>
                            </el-button>
                        </template>
                    </div>
                </div>
                <div class="description-container" v-if="markdownContent">
                    <MdPreview :editorId="previewId" :modelValue="markdownContent" :previewTheme="'default'"
                            :preview-lazy="true" ref="mdPreview" style="height: 100%; padding: 0px;" />
                </div>
            </el-main>
        </el-container>
        <AddDialog ref="addDialog" />
        
        <ContextMenu 
            :visible="contextMenuVisible"
            :menu-style="contextMenuStyle"
            :right-click-node="rightClickNode"
            :etype_value="etype_value"
            :tree-data="treeData"
            :tree-ref="treeRef"
            @update:visible="contextMenuVisible = $event"
            @refresh-tree="refreshTree"
            @refresh-item="refreshItem"
            @close-menu="closeContextMenu"
            @new-file="handleNewFileData"
            @task-started="startTask"
        />
    </div>
</template>

<script setup>
import axios from 'axios';
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, } from 'element-plus'
import { Folder, Document, Refresh, Download, View, Edit, Fold, Expand } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import AddDialog from '@/components/datatable/AddDialog.vue'
import AppNavbar from '@/components/support/AppNavbar.vue'
import ContextMenu from './ContextMenu.vue'
import { mapTreeData, updateNodeChildren, findNode } from './treeUtils'
import { loadTreeData, getFeatureOptions, renameData, refreshData } from './apiUtils'
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';
import { MdPreview } from 'md-editor-v3'
import { downloadFile } from '../datatable/dataUtils'

const { t, te } = useI18n();
const treeRef = ref(null);
const treeData = ref(null);
const currentNode = ref(null);
const mounted = ref(false);
const etype_value = ref(null);
const etype_options = ref([]);
const markdownContent = ref('');
const contextMenuVisible = ref(false);
const contextMenuStyle = ref({
    position: 'fixed',
    top: '0px',
    left: '0px'
});
const rightClickNode = ref(null);
const addDialog = ref(null);
const navbar = ref(null);

const defaultProps = {
    children: 'children',
    label: 'label',
    isLeaf: (data) => !data.is_folder,
};

const isMobile = computed(() => {
    return window.innerWidth <= 768;
});

const asideWidth = ref(isMobile.value ? 150 : 250);

const isDragging = ref(false);

const onResizerMouseDown = (e) => {
    isDragging.value = true;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleMouseUp);
};

const handleMouseMove = (e) => {
    if (!isDragging.value) return;
    const newWidth = e.clientX;
    if (newWidth >= 150 && newWidth <= 500) {
        asideWidth.value = newWidth;
    }
};

const handleTouchMove = (e) => {
    if (!isDragging.value) return;
    e.preventDefault(); // 防止页面滚动
    const touch = e.touches[0];
    const newWidth = touch.clientX;
    if (newWidth >= 150 && newWidth <= 500) {
        asideWidth.value = newWidth;
    }
};

const handleMouseUp = () => {
    isDragging.value = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.removeEventListener('touchmove', handleTouchMove);
    document.removeEventListener('touchend', handleMouseUp);
};

const loadNode = async (node, resolve) => {
    console.log('loadNode', etype_value.value, node.data?.title)
    /*
    if (node.level === 0) {
        const data = await loadTreeData();
        const mappedData = mapTreeData(data);
        resolve(mappedData);
        return;
    }*/ // later

    if (node.data && !node.data.need_load && node.data.children) {
        resolve(node.data.children);
        return;
    }

    const children = await loadTreeData(etype_value.value, node.data?.id || '');
    const mappedChildren = mapTreeData(children);
    
    updateNodeChildren(treeData.value, node.data?.id, mappedChildren);
    resolve(mappedChildren);
};

const initializeTree = async () => {
    if (treeRef.value) {
        const data = await loadTreeData(etype_value.value);
        treeData.value = mapTreeData(data);
    }
};

const getExpandedNodes = () => {
    const expandedNodes = [];
    const traverse = (node) => {
        if (node.expanded) {
            expandedNodes.push(node.data.id);
        }
        if (node.childNodes) {
            node.childNodes.forEach(child => traverse(child));
        }
    };

    treeRef.value.root.childNodes.forEach(node => traverse(node));
    return expandedNodes;
};

const expandNodes = async (expandedNodes) => {
    await nextTick();
    const expandNode = async (node) => {
        if (expandedNodes.includes(node.data.id)) {
            await node.expand();
            if (node.childNodes) {
                for (const child of node.childNodes) {
                    await expandNode(child);
                }
            }
        }
    };

    const rootNodes = treeRef.value.root.childNodes;
    for (const node of rootNodes) {
        await expandNode(node);
    }
};

const refreshTree = async () => {
    if (treeRef.value) {
        const expandedNodes = getExpandedNodes();
        await initializeTree();
        await expandNodes(expandedNodes);
    }
};

const refreshItem = async (addr, is_folder) => {
    if (!addr) return;
    const response_data = await refreshData(addr, etype_value.value, is_folder);
    if (response_data.status !== 'success') {
        ElMessage.error(response_data.info || t('tree.refreshFailed'));
        return;
    } else {
        if ("task_id" in response_data) {
            if (navbar.value) {
                navbar.value.startTaskCheck(response_data.task_id);
            }
            ElMessage.success(t('task.taskStarted'));
        } else {
            ElMessage.success(t('tree.refreshSuccess'));
        }
    }
};

const handleNodeClick = (data, node) => {
    currentNode.value = data;
    if (data.is_folder) {
        if (!node.expanded) {
            node.expand();
        } else {
            node.collapse();
        }
    } else {
        openItem(data.id);
    }
};

const parseOptions = (data) => {
    const options = [];
    data.forEach(item => {
        const hasTranslation = te(item);
        options.push({
            value: item,
            label: hasTranslation ? t(item) : item
        });
    });
    return options;
};

const getEtypeOptions = async () => {
    const data = await getFeatureOptions('etype');
    etype_options.value = parseOptions(data);
    
    if (etype_options.value.length === 0) {
        etype_options.value = [{ value: t('all'), label: t('all') }];
    }
    if (etype_options.value.some(item => item.value === 'note')) {
        etype_value.value = 'note';
    } else {
        etype_value.value = etype_options.value[0]?.value || t('all');
    }
};

const handleEtypeChange = async (value) => {
    etype_value.value = value;
    markdownContent.value = '';
    await refreshTree();
};

const openItem = async (idx) => {
    let func = 'api/entry/data/'
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + func + idx + '/', {
            params: {
            need_web_content: false
            }
        });
        const data = response.data;
        let description = ""
        if (data.title) description += `${t('title')}: ${data.title}\n`;
        if (data.etype) description += `${t('data')}: ${t(data.etype)}\n`;
        if (data.ctype) description += `${t('type')}: ${t(data.ctype)}\n`;
        if (data.status) description += `${t('status')}: ${t(data.status)}\n`;
        if (data.etype === 'web') {
            if (data.addr) description += `${t('webAddress')}: ${data.addr}\n`;
        } else {
            if (data.addr) description += `${t('file')}: ${data.addr}\n`;
        }
        if (data.created_time) description += `${t('createdAt')}: ${data.created_time}\n`;
        if (data.updated_time) description += `${t('lastUpdated')}: ${data.updated_time}\n`;
        description += '\n---\n';
        if (data.content) description += `\n${data.content}`;
        markdownContent.value = description
    } catch (error) {
        parseBackendError(error);
    }
};

const allowDrag = (node) => {
    if (etype_value.value === 'note' || etype_value.value === 'file') {
        return true;
    } else {
        return false;
    }
};

const allowDrop = (draggingNode, dropNode, type) => {
    return true;
};

const handleDrop = async (draggingNode, dropNode, type) => {
    try {
        const sourceAddr = draggingNode.data.addr;
        let targetAddr = dropNode.data.addr;
        const isFolder = draggingNode.data.is_folder;

        const sourceName = sourceAddr.split('/').pop();
        if (dropNode.data.is_folder) {
            targetAddr = `${targetAddr}/${sourceName}`.replace(/\/+/g, '/');
        } else {
            const targetDir = targetAddr.split('/').slice(0, -1).join('/');
            targetAddr = `${targetDir}/${sourceName}`.replace(/\/+/g, '/');
        }

        const response_data = await renameData(sourceAddr, targetAddr, etype_value.value, isFolder);
        if (response_data.status !== 'success') {
            ElMessage.error(response_data.info || t('tree.moveFailed'));
            return;
        }
        await refreshTree();
    } catch (error) {
        console.error('Move error:', error);
        parseBackendError(error);
    }
};

const handleContextMenu = (event, data, node) => {
    event.preventDefault();
    
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    
    const estimatedMenuHeight = 200;
    const estimatedMenuWidth = 150;
    
    let top = event.clientY;
    let left = event.clientX;
    
    if (top + estimatedMenuHeight > viewportHeight) {
        top = viewportHeight - estimatedMenuHeight - 5;
    }
    
    if (left + estimatedMenuWidth > viewportWidth) {
        left = viewportWidth - estimatedMenuWidth - 5;
    }
    
    top = Math.max(5, top);
    left = Math.max(5, left);
    
    contextMenuVisible.value = true;
    rightClickNode.value = { "node": node, "data": data };
    contextMenuStyle.value = {
        position: 'fixed',
        left: `${left}px`,
        top: `${top}px`,
        zIndex: 9999
    };

    nextTick(() => {
        document.addEventListener('click', closeContextMenu);
    });
};

const closeContextMenu = () => {
    contextMenuVisible.value = false;
    document.removeEventListener('click', closeContextMenu);
};

const handleNewFileSuccess = async (response_data) => {
    if (response_data.task_id) {
        if (navbar.value) {
            navbar.value.startTaskCheck(response_data.task_id);
        }
        ElMessage.success(t('task.taskStarted'));
    } else {
        await refreshTree();
        const exNode = await findNode(treeRef, rightClickNode.value.data.id);
        if (exNode) {
            exNode.expand();
        }
    }
};

const handleNewFileData = (data) => {
    addDialog.value.openDialog(handleNewFileSuccess, data);
};

const download = () => {
    if (!currentNode.value) return;
    const filename = currentNode.value.addr.split('/').pop();
    downloadFile(currentNode.value.id, filename);
};

const viewContent = () => {
    if (!currentNode.value) return;
    window.open(`${window.location.origin}/view_markdown?idx=${currentNode.value.id}`, '_blank');
};

const editNote = () => {
    if (!currentNode.value) return;
    window.open(`${window.location.origin}/edit_markdown?idx=${currentNode.value.id}`, '_blank');
};

const isCollapse = ref(false);
const computedAsideWidth = computed(() => {
    if (isCollapse.value) {
        return '40px';
    }
    return asideWidth.value + 'px';
});

const toggleCollapse = () => {
    isCollapse.value = !isCollapse.value;
};

const startTask = () => {
    console.log('startTask');
    if (navbar.value) {
        console.log('navbar', navbar.value);
        navbar.value.startTaskCheck();
    }
};

onMounted(async () => {
    mounted.value = true;
    await nextTick();
    await getEtypeOptions();
    await initializeTree();

    window.addEventListener('resize', () => {
        if (isMobile.value && asideWidth.value > 150) {
            asideWidth.value = 150;
        }
    });

    return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.removeEventListener('touchmove', handleTouchMove);
        document.removeEventListener('touchend', handleMouseUp);
        window.removeEventListener('resize');
    };
});

defineExpose({
    treeRef,
    treeData,
    defaultProps,
    currentNode,
    mounted,
    etype_value,
    etype_options,
    markdownContent,
    contextMenuVisible,
    contextMenuStyle,
    rightClickNode
});
</script>

<style scoped>

:deep(.md-editor-preview) {
    height: auto;
    overflow-y: auto !important;
    padding: 10px 20px;
    max-width: 960px;
    margin: 0 auto;
    font-size: v-bind('fontSize + "px"');
}

:deep(.md-editor-preview-wrapper) {
    padding: 0px;
}

.file-tree-aside {
    position: relative;
    transition: width 0.3s;
    border-right: 1px solid var(--el-border-color-light);
    background-color: var(--el-bg-color);
    height: 100%;
    overflow-y: auto;
    padding: 10px;
    max-width: 500px;
}

.resizer {
    width: 4px;
    height: 100%;
    background-color: transparent;
    cursor: col-resize;
    transition: background-color 0.3s;
    touch-action: none; /* 防止触摸事件的默认行为 */
}

.resizer:hover {
    background-color: var(--el-border-color-lighter);
}

.tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 10px 10px 10px;
    border-bottom: 1px solid var(--el-border-color-light);
    margin-bottom: 10px;
}

.tree-title {
    font-weight: bold;
    font-size: 16px;
}

.custom-tree-node {
    display: flex;
    align-items: center;
    gap: 4px;
}

:deep(.el-tree-node__content) {
    height: 32px;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
    background-color: var(--el-color-primary-light-9);
}

.header-buttons {
    display: flex;
    flex-wrap: nowrap;
    gap: 5px;
    margin: 5px;
    align-items: center;
}

.filter-section {
    display: flex;
    flex-grow: 1;
    align-items: center;
    gap: 10px;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
}

.label-container {
    flex-shrink: 0;
    white-space: nowrap;
}

.select-container {
    flex: 1;
    min-width: 120px;
    max-width: 200px;
}

:deep(.el-select) {
    width: 100%;
}

:deep(.el-dropdown-menu) {
    z-index: 9999;
}

.action-buttons {
    display: flex;
    gap: 10px;
    margin-left: 10px;
}

.action-buttons .el-button {
    margin: 0;
    padding: 0 5px;
}

:deep(.description-container) {
    padding: 10px;
}

.toggle-button-collapse {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 40px;
    background-color: var(--el-border-color-light);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 4px 0 0 4px;
    z-index: 10;
    transition: all 0.3s;
}

.toggle-button-collapse:hover {
    background-color: var(--el-border-color);
}

.collapse-aside {
    padding: 0;
    overflow: hidden;
}

.collapse-aside .tree-header,
.collapse-aside .el-tree {
    opacity: 0;
    visibility: hidden;
}

@media (max-width: 768px) {
    .toggle-button-collapse {
        width: 12px;
        height: 30px;
    }
    :deep(.description-container) {
        padding: 2px;
    }
    
    :deep(.md-editor-preview) {
        padding: 4px !important;
    }
    .tree-header {
        padding: 0 5px 5px 5px;
    }
    .file-tree-aside {
        padding: 5px;
        max-width: 500px;
    }
    .resizer {
        width: 12px;
    }    

    .filter-section {
        gap: 0px;
    }
    
    .filter-item {
        gap: 4px;
    }
    
    .select-container {
        min-width: 80px;
    }
    
    .label-container {
        font-size: 14px;
    }

    .header-buttons {
        margin: 2px;
    }    


    .action-buttons {
        gap: 2px;
        margin: 0px;
        padding: 0px;
    }    
}
</style>