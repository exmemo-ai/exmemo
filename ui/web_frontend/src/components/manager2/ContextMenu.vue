<template>
    <div v-show="visible" class="context-menu" :style="menuStyle">
        <el-menu>
            <el-menu-item v-if="showNewFolder" @click="handleNewFolder">
                <el-icon><FolderAdd /></el-icon>
                <span>{{ t('newFolder') }}</span>
            </el-menu-item>
            <el-menu-item v-if="showNewFile" @click="handleNewFile">
                <el-icon><DocumentAdd /></el-icon>
                <span>{{ t('newFile') }}</span>
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
</template>

<script setup>
import { Delete, FolderAdd, DocumentAdd, Edit } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick, computed } from 'vue'
import { deleteData, renameData } from './apiUtils'
import { mapTreeItem, findAndAddNode, findNode, findData } from './treeUtils'

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
    'refresh-tree',
    'close-menu'
])

const showNewFolder = computed(() => ['note', 'file'].includes(props.etype_value))
const showNewFile = computed(() => ['note', 'file'].includes(props.etype_value))
const showRename = computed(() => ['note', 'file', 'chat', 'record'].includes(props.etype_value))
const showDelete = computed(() => true)

const handleNewFolder = async () => {
    if (!props.rightClickNode) return;

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
            ElMessage.error(t('folderAlreadyExists'));
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

        if (parentId === '') {
            if (!props.treeData) {
                props.treeData = [];
            }
            props.treeData.push(newFolder);
        } else {
            if (findAndAddNode(props.treeData, parentId, newFolder)) {
                props.treeData = [...props.treeData];
                await nextTick();
                const exNode = await findNode(props.treeRef, parentId);
                if (exNode) {
                    exNode.expand();
                }
            }
        }
        ElMessage.success(t('createFolderSuccess'));
    } catch (error) {
        if (error?.message !== 'cancel' && error !== 'cancel') {
            console.error('Create folder error:', error);
            ElMessage.error(t('createFolderFailed'));
        }
    } finally {
        emit('close-menu');
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
    emit('close-menu');
};

const handleRename = async () => {
    if (!props.rightClickNode) return;
    
    try {
        const { value: newName } = await ElMessageBox.prompt(
            t('enterNewName'),
            t('rename'),
            {
                confirmButtonText: t('ok'),
                cancelButtonText: t('cancel'),
                inputValue: props.rightClickNode.data.label,
                inputValidator: (value) => {
                    if (!value) return t('nameRequired');
                    if (value.includes('/')) return t('nameInvalid');
                    return true;
                }
            }
        );
        if (!newName || newName === props.rightClickNode.data.title) return;
        const newPath = props.rightClickNode.data.addr.replace(/[^/]+$/, newName);
        //console.log('Renaming to:', newName, ' at path:', newPath);
        const existingNode = await findData(props.treeData, newPath);
        if (existingNode) {
            ElMessage.error(t('nameAlreadyExists'));
            return;
        }
        await renameData(props.rightClickNode.data.addr, newPath, props.etype_value, props.rightClickNode.data.is_folder);
        emit('refresh-tree');
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Rename error:', error);
            ElMessage.error(t('renameFailed'));
        }
    } finally {
        emit('close-menu');
    }
};

const handleDelete = async () => {
    if (!props.rightClickNode) return;

    const isFolder = props.rightClickNode.data.is_folder;
    const path = props.rightClickNode.data.addr;
    
    try {
        if (isFolder) {
            const response = await axios.get(getURL() + 'api/entry/tool/', {
                params: {
                    rtype: 'tree',
                    etype: props.etype_value === t('all') ? '' : props.etype_value,
                    path: path,
                    level: -1
                }
            });

            const getAllFiles = (items) => {
                let files = [];
                items.forEach(item => {
                    if (!item.is_folder) {
                        files.push(item.id);
                    } else if (item.children) {
                        files = files.concat(getAllFiles(item.children));
                    }
                });
                return files;
            };

            const files = getAllFiles(response.data);
            if (files.length > 0) {
                await ElMessageBox.confirm(
                    t('deleteFolderConfirmation') + files.length,
                    t('promptTitle'),
                    {
                        confirmButtonText: t('confirm'),
                        cancelButtonText: t('cancel'),
                        type: 'warning'
                    }
                );
                for (const fileId of files) {
                    await deleteData(fileId);
                }
                ElMessage.success(t('deleteFolderSuccess'));
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
        emit('refresh-tree');
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Delete error:', error);
            ElMessage.error(t('deleteFailed'));
        }
    } finally {
        emit('close-menu');
    }
};

defineExpose({
    handleNewFolder,
    handleNewFile,
    handleRename,
    handleDelete
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
