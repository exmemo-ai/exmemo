<template>
    <div v-show="visible" class="context-menu" :style="menuStyle">
        <el-menu>
            <el-menu-item v-if="showNewFolder" @click="handleNewFolder">
                <el-icon><FolderAdd /></el-icon>
                <span>{{ t('tree.newFolder') }}</span>
            </el-menu-item>
            <el-menu-item v-if="showNewFile" @click="handleNewFile">
                <el-icon><DocumentAdd /></el-icon>
                <span>{{ t('tree.newFile') }}</span>
            </el-menu-item>
            <el-menu-item v-if="showImport" @click="handleImport">
                <el-icon><Upload /></el-icon>
                <span>{{ t('tree.importNote') }}</span>
            </el-menu-item>
            <el-menu-item v-if="showRefresh" @click="handleRefresh">
                <el-icon><RefreshRight /></el-icon>
                <span>{{ t('tree.refresh') }}</span>
            </el-menu-item>
            <el-divider v-if="showNewFolder || showNewFile" />
            <el-menu-item v-if="showRename" @click="handleRename">
                <el-icon><Edit /></el-icon>
                <span>{{ t('rename') }}</span>
            </el-menu-item>
            <el-menu-item v-if="showDelete" @click="handleDelete">
                <el-icon><Delete /></el-icon>
                <span>{{ t('delete') }}</span>
            </el-menu-item>
        </el-menu>
    </div>
    <ImportDialog ref="importDialogRef" />
</template>

<script setup>
import { Upload, Delete, FolderAdd, DocumentAdd, Edit, RefreshRight } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick, computed, ref } from 'vue'
import { deleteData, deleteDir, renameData, loadTreeData, importNotes } from './apiUtils'
import { mapTreeItem, findAndAddNode, findNode, findData } from './treeUtils'
import { saveEntry } from '@/components/datatable/dataUtils';
import ImportDialog from './ImportDialog.vue'

const { t } = useI18n()

const props = defineProps({
    visible: Boolean,
    menuStyle: Object,
    rightClickNode: Object,
    etype_value: String,
    treeData: Array,
    treeRef: Object
})

const emit = defineEmits([
    'update:visible',
    'refresh',
    'item-refresh',
    'close',
    'new-file',
    'task-start',
    'update:tree-data',
])

const showNewFolder = computed(() => ['note', 'file'].includes(props.etype_value))
const showNewFile = computed(() => ['note', 'file'].includes(props.etype_value))
const showRename = computed(() => ['note', 'file', 'chat', 'record'].includes(props.etype_value))
const showDelete = computed(() => true)
const showImport = computed(() => props.etype_value === 'file')
const showRefresh = computed(() => ['web', 'file', 'note'].includes(props.etype_value))

const importDialogRef = ref(null)

const handleNewFolder = async () => {
    if (!props.rightClickNode) return;

    try {
        const { value: folderName } = await ElMessageBox.prompt(t('tree.enterFolderName'), {
            confirmButtonText: t('confirm'),
            cancelButtonText: t('cancel'),
            inputValidator: (value) => {
                if (!value) return t('tree.folderNameRequired');
                if (value.includes('/')) return t('tree.folderNameInvalid');
                return true;
            }
        });

        if (!folderName) return;

        let parentPath;
        let parentId;
        if (!props.rightClickNode.data.is_folder) {
            const pathParts = props.rightClickNode.data.addr.split('/');
            pathParts.pop();
            parentPath = pathParts.join('/');
            parentId = parentPath || '';
        } else {
            parentPath = props.rightClickNode.data.addr;
            parentId = props.rightClickNode.data.id;
        }

        const id = `${parentPath}/${folderName}`.replace(/^\//, '');
        const existingNode = await findData(props.treeData, id);
        if (existingNode) {
            ElMessage.error(t('tree.folderAlreadyExists'));
            return;
        }

        const folderData = {
            title: folderName,
            is_folder: true,
            id: id,
            addr: id,
            need_load: false,
            children: []
        };
        const newFolder = mapTreeItem(folderData);        
        const newTreeData = JSON.parse(JSON.stringify(props.treeData || []));
        
        if (parentId === '') {
            newTreeData.push(newFolder);
            emit('update:tree-data', newTreeData);
        } else {
            if (findAndAddNode(newTreeData, parentId, newFolder)) {
                emit('update:tree-data', newTreeData);
                await nextTick();
                const exNode = await findNode(props.treeRef, parentId);
                if (exNode) {
                    exNode.expand();
                }
            }
        }
        ElMessage.success(t('tree.createFolderSuccess'));
    } catch (error) {
        if (error?.message !== 'cancel' && error !== 'cancel') {
            console.error('Create folder error:', error);
            ElMessage.error(t('tree.createFolderFailed'));
        }
    } finally {
        emit('close');
    }
};

const handleNewFile = async () => {
    if (!props.rightClickNode) return;

    let parentPath;
    if (!props.rightClickNode.data.is_folder) {
        const pathParts = props.rightClickNode.data.addr.split('/');
        pathParts.pop();
        parentPath = pathParts.join('/');
    } else {
        parentPath = props.rightClickNode.data.addr;
    }

    const data = { etype: props.etype_value };
    if (props.etype_value === 'note' && parentPath) {
        const pathParts = parentPath.split('/');
        data['vault'] = pathParts[0];
        if (pathParts.length > 1) {
            data['path'] = pathParts.slice(1).join('/');
        } else {
            data['path'] = '';
        }
    } else {
        data['path'] = parentPath || '';
    };
    if (data['path'].length > 0 && !data['path'].endsWith('/')) {
        data['path'] += '/';
    }
    emit('new-file', data);
    emit('close');
};

const handleRename = async () => {
    if (!props.rightClickNode) return;
    
    try {
        const { value: newName } = await ElMessageBox.prompt(
            t('tree.enterNewName'),
            t('rename'),
            {
                confirmButtonText: t('confirm'),
                cancelButtonText: t('cancel'),
                inputValue: props.rightClickNode.data.label,
                inputValidator: (value) => {
                    if (!value) return t('tree.nameRequired');
                    if (value.includes('/')) return t('tree.nameInvalid');
                    return true;
                }
            }
        );
        if (!newName || newName === props.rightClickNode.data.title) return;
        const newPath = props.rightClickNode.data.addr.replace(/[^/]+$/, newName);
        const existingNode = await findData(props.treeData, newPath);
        if (existingNode) {
            ElMessage.error(t('tree.nameAlreadyExists'));
            return;
        }

        if (props.etype_value === 'chat' || props.etype_value === 'record') {
            const ret = await saveEntry({
                form: {
                    idx: props.rightClickNode.data.id,
                    etype: props.etype_value,
                    title: newPath
                }, showMessage:false
            });
            if (ret && ret.status === 'success') {
                emit('refresh');
            } else {
                ElMessage.error(t('tree.renameFailed'));
            }
            console.log('Rename success', ret);
        } else {
            const response_data = await renameData(props.rightClickNode.data.addr, newPath, props.etype_value, props.rightClickNode.data.is_folder);
            if (response_data.task_id) {
                emit('task-start');
            } else {
                if (response_data.status === 'success') {
                    emit('refresh');
                } else {
                    ElMessage.error(t('tree.renameFailed'));
                }
            }
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Rename error:', error);
            ElMessage.error(t('tree.renameFailed'));
        }
    } finally {
        emit('close');
    }
};

const handleDelete = async () => {
    if (!props.rightClickNode) return;

    const isFolder = props.rightClickNode.data.is_folder;
    const path = props.rightClickNode.data.addr;
    
    try {
        if (isFolder) {
            const response_data = await loadTreeData(props.etype_value, path, -1);
            const files = getAllFiles(response_data);
            if (files.length > 0) {
                await ElMessageBox.confirm(
                    t('tree.deleteFolderConfirmation', { count: files.length }),
                    t('promptTitle'),
                    {
                        confirmButtonText: t('confirm'),
                        cancelButtonText: t('cancel'),
                        type: 'warning'
                    }
                );
                const response_data = await deleteDir(path, props.etype_value);
                if (response_data.task_id) {
                    emit('task-start');
                } else if (response_data.status === 'success') {
                    ElMessage.success(t('tree.deleteFolderSuccess'));
                } else {
                    ElMessage.error(t('deleteFail'))
                }
            }
        } else {
            await ElMessageBox.confirm(
                t('deleteConfirmation'),
                t('promptTitle'),
                {
                    confirmButtonText: t('confirm'),
                    cancelButtonText: t('cancel'),
                    type: 'warning'
                }
            );
            await deleteData(props.rightClickNode.data.id);
            ElMessage.success(t('deleteSuccess'));
        }
        emit('refresh');
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Delete error:', error);
            ElMessage.error(t('deleteFail'));
        }
    } finally {
        emit('close');
    }
};

const getAllFiles = (items) => {
    let files = [];
    items.forEach(item => {
        if (!item.is_folder) {
            files.push(item.addr);
        } else if (item.children) {
            files = files.concat(getAllFiles(item.children));
        }
    });
    return files;
};

const handleImport = async () => {
    if (!props.rightClickNode) return;
    
    try {
        const path = props.rightClickNode.data.addr;
        let count = 0;
        if (props.rightClickNode.data.is_folder) {
            const response_data = await loadTreeData(props.etype_value, path, -1);
            let files = getAllFiles(response_data);
            if (files.length === 0) {
                ElMessage.error(t('tree.noFilesToImport'));
                return;
            }
            const supportedExtensions = ['pdf', 'docx', 'doc', 'md', 
                    'txt', 'epub', 'mobi', 'html'];
            files = files.filter(file => {
                const ext = file.split('.').pop().toLowerCase();
                return supportedExtensions.includes(ext);
            });
            if (files.length === 0) {
                ElMessage.error(t('tree.noFilesToImport'));
                return;
            }
            count = files.length;
        }

        const result = await importDialogRef.value?.show(props.rightClickNode.data.is_folder, 
                            'note', count);

        if (result) {
            let target = result.vault
            if (result.path) {
                target += '/' + result.path
            }
            if (target.length > 0 && !target.endsWith('/')) {
                target += '/'
            }
            const response_data = await importNotes(
                props.rightClickNode.data.addr, 
                target,
                props.rightClickNode.data.is_folder,
                result.overwrite
            )
            if (response_data.task_id) {
                emit('task-start');
            } else if (response_data.status === 'success') {
                ElMessage.success(t('tree.importSuccess'))
                //emit('refresh')
            } else {
                ElMessage.error(t('tree.importFailed'))
            }
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Import error:', error)
            ElMessage.error(t('tree.importFailed'))
        }
    } finally {
        emit('close')
    }
};

const handleRefresh = async () => {
    if (!props.rightClickNode) return;
    emit('item-refresh', props.rightClickNode.data.id, props.rightClickNode.data.is_folder);
    emit('close');
};

defineExpose({
    handleNewFolder,
    handleNewFile,
    handleRename,
    handleDelete,
    handleImport,
    handleRefresh
});
</script>

<style scoped>
.context-menu {
    position: fixed;
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-light);
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    z-index: 3000;
}

.context-menu :deep(.el-menu) {
    padding: 4px 0;
}

.context-menu :deep(.el-menu-item) {
    padding: 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    height: 36px;
    line-height: 36px;
}

.context-menu :deep(.el-divider--horizontal) {
    margin: 4px 0;
}
</style>
