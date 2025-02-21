<template>
    <MdEditor 
        v-model="editContent" 
        :preview="false"
        :toolbars="[]"
        :footers="[]"
        style="height: calc(100% - 40px);"
        @change="handleContentChange"
    />
    <AddDialog ref="addDialog" />
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { MdEditor } from 'md-editor-v3'
import { ElMessage, ElMessageBox } from 'element-plus'
import AddDialog from '@/components/manager/AddDialog.vue'
import axios from 'axios'
import { getURL, parseBackendError } from '@/components/support/conn'
import SettingService from '@/components/settings/settingService'
import { saveEntry } from './dataUtils';

const { t } = useI18n()
const editContent = ref('')
const addDialog = ref(null)

const props = defineProps({
    form: {
        type: Object,
        required: true
    }
})

const hasNoteChanged = ref(false)
const originalNote = ref('')
const saveTimer = ref(null)

const getDefaultPath = () => {
    let path = null;
    if (props.form.etype === 'note') {
        path = props.form.addr.split('/').slice(1, -1).join('/');
    } else if (props.form.etype === 'file') {
        path = t('viewMarkdown.fileNote');
    } else if (props.form.etype === 'web') {
        path = t('viewMarkdown.webNote');
    } else if (props.form.etype === 'chat') {
        path = t('.viewMarkdown.chatNote');
    } else {
        path = t('note');
    }
    let filename = props.form.title;
    if (filename) {
        filename = filename.replace(/\.md$/, '') + '_' + t('note') + '.md';
    }
    if (path) {
        path = path + '/' + filename;
    } else {
        path = filename;
    }
    return path
};

const getDefaultVault = () => {
    if (props.form.etype === 'note') {
        return props.form.addr.split('/')[0];
    } else {
        const settingService = SettingService.getInstance();
        const vault = settingService.getSetting('default_vault', t('default'));
        return vault;
    }
};

const updateFrontMatter = (content, newFields) => {
    if (content.startsWith('---')) {
        const secondDash = content.indexOf('---', 3);
        if (secondDash !== -1) {
            const frontMatter = content.substring(3, secondDash);
            const lines = frontMatter.split('\n')
                .filter(line => line.trim())
                .filter(line => !Object.keys(newFields).some(key => line.startsWith(`${key}:`)));
            
            const newFrontMatter = [
                ...lines,
                ...Object.entries(newFields).map(([key, value]) => `${key}: ${value}`)
            ].filter(line => line.trim()).join('\n');
            
            return '---\n' + newFrontMatter + '\n---\n\n' + 
                   content.substring(secondDash + 3).trim();
        }
    }
    
    const frontMatter = Object.entries(newFields)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');
    return `---\n${frontMatter}\n---\n\n${content.trim()}`;
};

const saveSuccess = (data) => {
    if (data && data.list && data.list.length > 0) {
        const addr = data.list[0];
        let func = 'api/entry/data/'
        let params = {
            keyword: addr, 
            etype: 'note',
            max_count: 1
        }
        axios.get(getURL() + func, { params: params })
            .then(response => {
                const results = response.data['results'];
                if (results && results.length > 0) {
                    showConfirm(results[0].idx);
                }
            })
            .catch(error => {
                parseBackendError(null, error);
            });
    }
};

const showConfirm = (idx) => {
    ElMessageBox.confirm(
        t('viewMarkdown.openNote'), 
        t('viewMarkdown.openNoteTitle'), 
        {
            confirmButtonText: t('confirm'),
            cancelButtonText: t('cancel'),
            type: 'info',
        }
    ).then(() => {
        window.open(`${window.location.origin}/view_markdown?idx=${idx}`, '_blank');
    }).catch(() => {
    });
};

const saveAsNote = async () => {
    if (editContent.value.trim().length === 0) {
        ElMessage.error(t('viewMarkdown.noteEmpty'));
        return;
    }
    
    const newFields = {
        origin_title: props.form.title,
        origin_addr: props.form.addr,
        origin_idx: props.form.idx
    };
    
    editContent.value = updateFrontMatter(editContent.value.trim(), newFields);
    
    const vault = getDefaultVault();
    const path = getDefaultPath();
    addDialog.value.openDialog(saveSuccess, {
        etype: 'note',
        content: editContent.value,
        vault: vault,
        path: path,
        atype: "subjective",
        ctype: props.form.ctype,
        status: "collect",
    });
};

const loadNote = () => {
    if (props.form.meta && props.form.meta.note) {
        editContent.value = props.form.meta.note
        originalNote.value = props.form.meta.note
    }
}

const handleContentChange = (value) => {
    hasNoteChanged.value = value !== originalNote.value
    scheduleSave()
}

const scheduleSave = () => {
    if (saveTimer.value) {
        clearTimeout(saveTimer.value)
    }
    saveTimer.value = setTimeout(async () => {
        await saveMeta()
        saveTimer.value = null
    }, 30000)
}

const saveMeta = async () => {
    if (!hasNoteChanged.value) return

    if (!props.form.meta || props.form.meta === 'null') {
        props.form.meta = {}
    }
    
    if (typeof props.form.meta === 'string') {
        try {
            props.form.meta = JSON.parse(props.form.meta)
        } catch (error) {
            console.error('Failed to parse meta:', error)
            props.form.meta = {}
        }
    }

    if (hasNoteChanged.value && editContent.value.trim().length > 0) {
        props.form.meta.note = editContent.value
    }

    try {
        const result = await saveEntry({
            parentObj: null,
            form: props.form,
            path: null,
            file: null,
            onProgress: null,
            showMessage: false
        })
        
        if (result) {
            hasNoteChanged.value = false
            originalNote.value = editContent.value
        }
    } catch (error) {
        console.error(t('saveFail'), error)
        ElMessage.error(t('saveFail'))
    }
}

onBeforeUnmount(() => {
    if (saveTimer.value) {
        clearTimeout(saveTimer.value)
    }
})

defineExpose({
    editContent,
    saveAsNote,
    loadNote
})
</script>

<style scoped>
</style>
