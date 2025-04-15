<template>
    <div class="app-container">
        <el-container style="flex: 0; width: 100%;">
            <app-navbar :title="t('dataManagement')" :info="'DataManager2'" />
        </el-container>
        <el-container style="flex: 1; width: 100%; overflow: hidden;">
            <el-aside class="file-tree-aside">
                <div class="tree-header">
                    <el-text class="tree-title">{{ t('fileTree') }}</el-text>
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
                </div>
                <div class="description-container" v-if="description">
                    <div style="padding: 10px;">
                        <pre>{{ description }}</pre>
                    </div>
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
            @close-menu="closeContextMenu"
            @new-file="handleNewFileData"
        />
    </div>
</template>

<script setup>
import axios from 'axios';
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, } from 'element-plus'
import { Folder, Document, Refresh } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import AddDialog from '@/components/manager/AddDialog.vue'
import AppNavbar from '@/components/support/AppNavbar.vue'
import ContextMenu from './ContextMenu.vue'
import { mapTreeData, updateNodeChildren, findNode } from './treeUtils'
import { loadTreeData, getFeatureOptions, renameData } from './apiUtils'
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';

const { t, te } = useI18n();
const treeRef = ref(null);
const treeData = ref(null);
const currentNode = ref(null);
const mounted = ref(false);
const etype_value = ref(null);
const etype_options = ref([]);
const description = ref('');
const contextMenuVisible = ref(false);
const contextMenuStyle = ref({
    position: 'fixed',
    top: '0px',
    left: '0px'
});
const rightClickNode = ref(null);
const addDialog = ref(null);

const defaultProps = {
    children: 'children',
    label: 'label',
    isLeaf: (data) => !data.is_folder,
};

const loadNode = async (node, resolve) => {
    console.log('loadNode', etype_value.value)
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
    await refreshTree();
};

const openItem = async (idx) => {
    let func = 'api/entry/data/'
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + func + idx + '/');
        const data = response.data;
        description.value = [
            `Title: ${data.title}`,
            `Type: ${data.etype}`,
            `Category: ${data.ctype}`,
            `Status: ${data.status}`,
            `Created: ${data.created_time}`,
            `Updated: ${data.updated_time}`,
            `User: ${data.user_id}`,
            `Path: ${data.path}`,
            `Content: \n${data.content}`
        ].join('\n');
    } catch (error) {
        parseBackendError(null, error);
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

        const response_data = renameData(sourceAddr, targetAddr, etype_value.value, isFolder);
        if (response_data.status !== 'success') {
            ElMessage.error(response_data.info || t('moveFailed'));
            return;
        }
        await refreshTree();
    } catch (error) {
        console.error('Move error:', error);
        parseBackendError(null, error);
    }
};

const handleContextMenu = (event, data, node) => {
    event.preventDefault();
    contextMenuVisible.value = true;
    rightClickNode.value = { "node": node, "data": data };
    contextMenuStyle.value = {
        position: 'fixed',
        left: `${event.clientX}px`,
        top: `${event.clientY}px`,
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

const handleNewFileData = (data) => {
    addDialog.value.openDialog(async () => {
        await refreshTree();
        const exNode = await findNode(treeRef, rightClickNode.value.data.id);
        if (exNode) {
            exNode.expand();
        }
    }, data);
};

onMounted(async () => {
    mounted.value = true;
    await nextTick();
    await getEtypeOptions();
    await initializeTree();
});

defineExpose({
    treeRef,
    treeData,
    defaultProps,
    currentNode,
    mounted,
    etype_value,
    etype_options,
    description,
    contextMenuVisible,
    contextMenuStyle,
    rightClickNode,
    loadNode,
    handleNodeClick,
    refreshTree,
    handleEtypeChange,
    handleContextMenu,
    closeContextMenu,
    handleNewFileData,
    allowDrag,
    allowDrop,
    handleDrop
});
</script>

<style scoped>
.file-tree-aside {
    border-right: 1px solid var(--el-border-color-light);
    background-color: var(--el-bg-color);
    height: 100%;
    overflow-y: auto;
    padding: 10px;
    min-width: 150px;
    max-width: 500px;
    resize: horizontal;
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
    margin: 0 5px 20px 5px;
    align-items: center;
}

.filter-section {
    display: flex;
    flex-grow: 1;
    align-items: center;
    gap: 5px;
}

.filter-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.label-container {
    flex-shrink: 0;
}

.select-container {
    flex-grow: 1;
    width: 200px;
}

:deep(.el-select) {
    width: 100%;
}

:deep(.el-dropdown-menu) {
    z-index: 9999;
}
</style>