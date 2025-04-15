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
        <EditDialog ref="editDialog" />
        <AddDialog ref="addDialog" />

        <div v-show="contextMenuVisible" class="context-menu" :style="contextMenuStyle">
            <el-menu>
                <el-menu-item @click="handleNewFolder">
                    <el-icon>
                        <FolderAdd />
                    </el-icon>
                    <span>{{ t('newFolder') }}</span>
                </el-menu-item>
                <el-menu-item @click="handleNewFile">
                    <el-icon>
                        <DocumentAdd />
                    </el-icon>
                    <span>{{ t('newFile') }}</span>
                </el-menu-item>
                <el-divider />
                <el-menu-item @click="handleRename">
                    <el-icon>
                        <Edit />
                    </el-icon>
                    <span>{{ t('rename') }}</span>
                </el-menu-item>
                <el-menu-item @click="handleDelete">
                    <el-icon>
                        <Delete />
                    </el-icon>
                    <span>{{ t('delete') }}</span>
                </el-menu-item>
            </el-menu>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus'
import EditDialog from '@/components/manager/EditDialog.vue';
import AddDialog from '@/components/manager/AddDialog.vue';
import AppNavbar from '@/components/support/AppNavbar.vue'
import { Delete, Folder, Document, Refresh, FolderAdd, DocumentAdd, Edit } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn'

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

const defaultProps = {
    children: 'children',
    label: 'label',
    isLeaf: (data) => !data.is_folder,
};

const loadTreeData = async (path = '') => {
    if (!mounted.value || !etype_value.value) {
        return [];
    }
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + 'api/entry/tool/', {
            params: {
                rtype: 'tree',
                etype: etype_value.value === t('all') ? '' : etype_value.value,
                path: path
            }
        });
        return response.data;
    } catch (error) {
        console.error('Load tree data error:', error);
        parseBackendError(error);
        return [];
    }
};

const mapTreeItem = (item) => ({
    label: item.title,
    type: item.is_folder ? 'folder' : 'file',
    id: item.id,
    addr: item.addr,
    is_folder: item.is_folder,
    need_load: item.need_load ?? false,
    children: item.is_folder && item.children ? mapTreeData(item.children) : undefined,
});

const mapTreeData = (data) => {
    if (!Array.isArray(data)) return [];
    
    const folders = data.filter(item => item.is_folder);
    const files = data.filter(item => !item.is_folder);

    const sortByTitle = (a, b) => a.title.localeCompare(b.title);
    folders.sort(sortByTitle);
    files.sort(sortByTitle);

    return [...folders, ...files].map(mapTreeItem);
};

const loadNode = async (node, resolve) => {
    console.log('loadNode')
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

    const children = await loadTreeData(node.data?.id || '');
    const mappedChildren = mapTreeData(children);
    
    updateNodeChildren(treeData.value, node.data?.id, mappedChildren);
    resolve(mappedChildren);
};

const updateNodeChildren = (nodes, nodeId, mappedChildren) => {
    if (!nodes) return false;
    for (let n of nodes) {
        if (n.id === nodeId) {
            n.children = mappedChildren;
            n.need_load = false;
            return true;
        }
        if (n.children && updateNodeChildren(n.children)) {
            return true;
        }
    }
    return false;
};

const initializeTree = async () => {
    if (treeRef.value) {
        const data = await loadTreeData();
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
    await getOptions(null, 'etype');
    if (etype_options.value.length === 0) {
        etype_options.value = [{ value: t('all'), label: t('all') }];
    }
    if (etype_options.value.some(item => item.value === 'note')) {
        etype_value.value = 'note';
    } else {
        etype_value.value = etype_options.value[0]?.value || t('all');
    }
};

const getOptions = async (obj, ctype) => {
    let func = 'api/entry/tool/'
    try {
        const response = await axios.get(getURL() + func, {
            params: { ctype: ctype, rtype: 'feature' }
        });

        if (ctype == 'all') {
            if ('ctype' in response.data) {
                ctype_options.value = parseOptions(response.data['ctype']);
            }
            if ('status' in response.data) {
                status_options.value = parseOptions(response.data['status']);
            }
            if ('etype' in response.data) {
                etype_options.value = parseOptions(response.data['etype']);
            }
        } else {
            const options = parseOptions(response.data);
            await nextTick();
            if (ctype === 'ctype') {
                ctype_options.value = options;
            } else if (ctype === 'status') {
                status_options.value = options;
            } else if (ctype === 'etype') {
                etype_options.value = options;
            }
        }
    } catch (error) {
        console.log('getOptions error', error);
    }
};

const handleEtypeChange = async (value) => {
    etype_value.value = value;
    await refreshTree();
};

const openItem = async (idx) => {
    let func = 'api/entry/data/'
    try {
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
        const sourceId = draggingNode.data.addr;
        const targetId = dropNode.data.addr;

        setDefaultAuthHeader();

        let func = 'api/entry/tool/'
        const response = await axios.get(getURL() + func, {
            params: {
                rtype: 'move',
                source: sourceId,
                source_type: draggingNode.data.type,
                target: targetId,
                target_type: dropNode.data.type,
                etype: etype_value.value,
            }
        });

        if (response.data.status !== 'success') {
            ElMessage.error(response.data.info || 'Move failed');
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

const findAndAddNode = (trees, targetId, newNode) => {
    for (let node of trees) {
        if (node.id === targetId) {
            if (node.id === targetId) {
                if (!node.children) {
                    node.children = [];
                }
                node.children.push(newNode);
            }
            return true;
        }
        if (node.children) {
            if (findAndAddNode(node.children, targetId, newNode)) {
                return true;
            }
        }
    }
    return false;
};

const findNode = (nodeId) => {
    const traverse = (node) => {
        if (!node) return null;
        if (node.data?.id === nodeId) return node;
        return node.childNodes?.find(child => traverse(child)) || null;  
    };

    return treeRef.value.root.childNodes.reduce((found, node) => 
        found || traverse(node), null);
};

const findData = (nodeId) => {
    const traverse = (nodes) => {
        if (!nodes || !Array.isArray(nodes)) return false;
        for (const node of nodes) {
            if (node.id === nodeId) return true;
            if (node.children && traverse(node.children)) return true;
        }
        return false;
    };
    return traverse(treeData.value);
};

const handleNewFolder = async () => {
    if (!rightClickNode.value) return;

    try {
        const { value: folderName } = await ElMessageBox.prompt(t('enterFolderName'), {
            confirmButtonText: t('ok'),
            cancelButtonText: t('cancel'),
            inputValidator: (value) => {
                if (!value) return t('folderNameRequired');
                if (value.includes('/')) return t('folderNameInvalid');
                return true;
            }
        });

        if (!folderName) return;

        const id = `${rightClickNode.value.data.addr}/${folderName}`;
        const folderData = {
            title: folderName,
            is_folder: true,
            id: id,
            addr: id,
            need_load: false,
            children: []
        };

        const existingNode = await findData(id);
        if (existingNode) {
            ElMessage.error(t('folderAlreadyExists'));
            return;
        }

        const newFolder = mapTreeItem(folderData);

        if (rightClickNode.value.data.id === '') {
            if (!treeData.value) {
                treeData.value = [];
            }
            treeData.value.push(newFolder);
        } else {
            if (findAndAddNode(treeData.value, rightClickNode.value.data.id, newFolder)) {
                treeData.value = [...treeData.value];
                await nextTick();
                const exNode = await findNode(rightClickNode.value.data.id);
                if (exNode) {
                    exNode.expand();
                }
            }
        }
        ElMessage.success(t('createFolderSuccess'));
    } catch (error) {
        if (error.message !== 'cancel') {
            console.error('Create folder error:', error);
            ElMessage.error(t('createFolderFailed'));
        }
    } finally {
        closeContextMenu();
    }
};

const handleNewFile = () => {
    console.log('新建文件', rightClickNode.value);
};

const handleRename = () => {
    console.log('重命名', rightClickNode.value);
};

const handleDelete = () => {
    console.log('删除', rightClickNode.value);
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
    handleNewFolder,
    handleNewFile,
    handleRename,
    handleDelete,
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
    align-items: center;
    gap: 5px;
    flex-grow: 1;
}

.label-container {
    display: flex;
    align-items: center;
    flex-shrink: 1;
}

.select-container {
    flex-grow: 1;
    width: 200px;
}

@media (max-width: 767px) {
    .file-tree-aside {
        width: 250px !important;
        /* 移动端默认宽度 */
        min-width: auto;
        max-width: 100%;
        resize: none;
    }

    .filter-section {
        width: 100%;
    }

    .select-container {
        width: 100%;
    }

    :deep(.el-select) {
        width: 100%;
    }
}

:deep(.el-dropdown-menu) {
    z-index: 9999;
}

.context-menu {
    position: fixed;
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-light);
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    z-index: 3000;
}

.context-menu :deep(.el-menu) {
    border: none;
    padding: 4px 0;
}

.context-menu :deep(.el-menu-item) {
    height: 36px;
    line-height: 36px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px;
}

.context-menu :deep(.el-divider--horizontal) {
    margin: 4px 0;
}
</style>
