<template>
    <div class="app-container">
        <el-container style="flex: 0; width: 100%;">
            <app-navbar :title="t('dataManagement')" :info="'DataManager2'" />
        </el-container>
        <el-container style="flex: 1; width: 100%; overflow: hidden;">
            <el-aside width="250px" class="file-tree-aside">
                <div class="tree-header">
                    <el-text class="tree-title">{{ t('fileTree') }}</el-text>
                    <el-button class="icon-button" @click="refreshTree">
                        <el-icon><Refresh /></el-icon>
                    </el-button>
                </div>
                <el-tree
                    ref="treeRef"
                    :data="treeData"
                    :props="defaultProps"
                    :load="loadNode"
                    lazy
                    @node-click="handleNodeClick"
                    :highlight-current="true"
                    :expand-on-click-node="false"
                >
                    <template #default="{ node, data }">
                        <span class="custom-tree-node">
                            <el-icon v-if="data.is_folder"><Folder /></el-icon>
                            <el-icon v-else><Document /></el-icon>
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
                                <el-select v-if="mounted && etype_options.length" 
                                    v-model="etype_value"
                                    :placeholder="t('selectPlaceholder')"
                                    @change="handleEtypeChange">
                                    <el-option v-for="item in etype_options" :key="item.value" 
                                        :label="item.label" :value="item.value">
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
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios';
import EditDialog from '@/components/manager/EditDialog.vue';
import AddDialog from '@/components/manager/AddDialog.vue';
import AppNavbar from '@/components/support/AppNavbar.vue'
import { Search, Plus, Delete, Folder, Document, Refresh } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn'

export default {
    name: 'DataManager2',
    components: {
        EditDialog,
        AddDialog,
        AppNavbar,
        Search,
        Plus,
        Delete,
        Folder,
        Document,
        Refresh
    },
    setup() {
        const { t, te } = useI18n();
        const treeRef = ref(null);

        onMounted(() => {
            console.log('onMounted treeRef:', treeRef.value);
        });

        return { 
            t, 
            te, 
            treeRef
        };
    },
    data() {
        const { t } = useI18n();
        return {
            treeData: null,
            defaultProps: {
                children: 'children',
                label: 'label',
                isLeaf: (data) => !data.is_folder,
            },
            currentNode: null,
            mounted: false,
            etype_value: t('all'),
            etype_options: [],
            description: '',
        };
    },
    methods: {
        getInitialTreeData() {
            return [{
                label: 'Root',
                id: '',
                is_folder: true,
                need_load: true,
                children: []
            }];
        },

        mapTreeData(data) {
            return data.map(item => ({
                label: item.title,
                type: item.is_folder ? 'folder' : 'file',
                id: item.id,
                is_folder: item.is_folder,
                need_load: item.need_load ?? false,
                children: item.children || [],
            }));
        },

        async loadNode(node, resolve) {
            console.log('loadNode');
            if (node.data && !node.data.need_load && node.data.children) {
                resolve(this.mapTreeData(node.data.children));
                return;
            }

            console.log('requesting children for node', node);
            try {
                let path = node.level === 0 ? '' : node.data.id;
                setDefaultAuthHeader();
                const response = await axios.get(getURL() + 'api/entry/tool/', {
                    params: {
                        rtype: 'tree',
                        etype: this.etype_value === this.t('all') ? '' : this.etype_value,
                        path: path
                    }
                });

                const children = this.mapTreeData(response.data);
                resolve(children);
                
                if (node.level === 0) {
                    await this.$nextTick();
                }
            } catch (error) {
                parseBackendError(this, error);
                resolve([]);
            }
            console.log('after loadNode', node);
        },

        async initializeTree() {
            if (this.$refs.treeRef) {
                await this.$nextTick();
                this.treeData = this.getInitialTreeData();
                await this.$nextTick();
            }
        },

        async refreshTree() {
            console.log('refreshTree');
            if (this.$refs.treeRef) {
                this.treeData = this.getInitialTreeData();
                await this.$nextTick();
                const rootNode = this.$refs.treeRef.store.root.childNodes[0];
                if (rootNode) {
                    rootNode.expand();
                }
            }
        },

        handleNodeClick(data, node) {
            this.currentNode = data;
            if (data.is_folder) {
                if (!node.expanded) {
                    node.expand();
                } else {
                    node.collapse();
                }
            } else {
                this.openItem(data.id);
            }
        },

        parseOptions(data) {
            const options = [{ value: this.t('all'), label: this.t('all') }];
            data.forEach(item => {
                const hasTranslation = this.te(item);
                options.push({
                    value: item,
                    label: hasTranslation ? this.t(item) : item
                });
            });
            return options;
        },
        async getEtypeOptions() {
            await this.getOptions(null, 'etype');
        },

        async getOptions(obj, ctype) { // same as DataManager.vue
            let func = 'api/entry/tool/'
            try {
                const response = await axios.get(getURL() + func, {
                    params: { ctype: ctype, rtype: 'feature' }
                });
                console.log('getOptions success');

                if (ctype == 'all') {
                    if ('ctype' in response.data) {
                        this.ctype_options = this.parseOptions(response.data['ctype']);
                    }
                    if ('status' in response.data) {
                        this.status_options = this.parseOptions(response.data['status']);
                    }
                    if ('etype' in response.data) {
                        this.etype_options = this.parseOptions(response.data['etype']);
                    }
                } else {
                    const options = this.parseOptions(response.data);
                    await this.$nextTick();
                    if (ctype === 'ctype') {
                        this.ctype_options = options;
                    } else if (ctype === 'status') {
                        this.status_options = options;
                    } else if (ctype === 'etype') {
                        this.etype_options = options;
                    }
                }
            } catch (error) {
                console.log('getOptions error', error);
            }
        },

        async handleEtypeChange(value) {
            this.etype_value = value;
            await this.refreshTree();
        },

        async openItem(idx) {
            let func = 'api/entry/data/'
            try {
                const response = await axios.get(getURL() + func + idx + '/');
                const data = response.data;
                this.description = [
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
                parseBackendError(this, error);
            }
        }
    },
    async mounted() {
        this.mounted = true;
        await this.$nextTick();
        await this.getEtypeOptions();
        await this.initializeTree();
    }
}
</script>

<style scoped>
.file-tree-aside {
    border-right: 1px solid var(--el-border-color-light);
    background-color: var(--el-bg-color);
    height: 100%;
    overflow-y: auto;
    padding: 10px;
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
        width: 100% !important;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
        transform: translateX(-100%);
        transition: transform 0.3s;
    }

    .file-tree-aside.show {
        transform: translateX(0);
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
</style>
