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
import { ElMessage } from 'element-plus'
import AddDialog from '@/components/datatable/AddDialog.vue'
import { getDefaultPath, getDefaultVault } from '@/components/datatable/dataUtils';

const emit = defineEmits(['noteChange'])

const { t } = useI18n()
const editContent = ref('')
const addDialog = ref(null)

const props = defineProps({
    form: {
        type: Object,
        required: true
    }
})

const originalNote = ref('')

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
    
    const vault = getDefaultVault(props.form.etype, props.form.addr);
    const path = getDefaultPath(props.form.etype, props.form.addr, props.form.title);
    addDialog.value.openDialog(null, {
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
    if (value !== originalNote.value) {
        emit('noteChange')
    }
}

defineExpose({
    editContent,
    saveAsNote,
    loadNote
})
</script>

<style scoped>
</style>
