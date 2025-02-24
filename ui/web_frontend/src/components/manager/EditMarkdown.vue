<template>
    <div class="app-container">
        <div ref="navbar" class="header">
            <el-container class="nav-container">
                <div class="top-row-view">
                    <div class="title-container">
                        <img :src="logo" class="nav-avatar" />
                        <h3 class="title">{{ appName }}</h3>
                    </div>
                </div>
                <div>
                    <div class="user-controls" style="margin-bottom: 5px">
                        <div class="button-container-flex">
                            <el-button-group class="basic-buttons" style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="setPlayer">
                                    {{ showPlayer ? t('viewMarkdown.hideRead') : t('viewMarkdown.showRead') }}
                                </el-button>
                            </el-button-group>
                            <el-button-group style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="saveContent" :icon="Document">
                                    {{ t('save') }}
                                </el-button>
                            </el-button-group>
                            <el-button-group style="margin-right: 5px;" v-if="!isLandscape">
                                <el-button 
                                    size="small" 
                                    type="primary" 
                                    @click="toggleViewMode"
                                    :icon="viewModeIcon">
                                    {{ viewMode === 'edit' ? t('editMarkdown.previewMode') : t('editMarkdown.editMode') }}
                                </el-button>
                            </el-button-group>
                        </div>
                    </div>
                </div>
            </el-container>
        </div>
        <div class="main-content" :class="{ 'landscape': isLandscape }">
            <div :class="[
                'editor-container',
                { 'hidden': !isLandscape && viewMode === 'preview' }
            ]">
                <MdEditor
                    v-model="markdownContent"
                    :showCodeRowNumber="true"
                    @onChange="handleContentChange"
                    @on-save="saveContent"
                    :toolbarsExclude="['preview']"
                    :showToolbar="true"
                    :preview="isLandscape ? true: false"
                />
            </div>
            <div v-if="!isLandscape" 
                :class="['preview-container', { 'hidden': viewMode === 'edit' }]" 
                ref="content">
                <MdPreview 
                    :modelValue="markdownContent" 
                    :id="previewId"
                    ref="mdPreview" 
                    style="height: 100%; padding: 0px;"
                />
            </div>
        </div>
        
        <div v-if="showPlayer" class="player-footer" style="flex-shrink: 1">
            <TextSpeakerPlayer
                :text="selectedText"
                :lang="getLocale()"
                :getContentCallback="getContent"
                ref="speakerPlayer"
                @onSpeak="handleSpeak"
            />
        </div>
    </div>
</template>

<script setup>
import 'md-editor-v3/lib/style.css';
import logo from '@/assets/images/logo.png';
import { getLocale } from '@/main.js';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { MdEditor, MdPreview } from 'md-editor-v3';
import { saveEntry, fetchItem } from './dataUtils';
import TextSpeakerPlayer from '@/components/manager/TextPlayer.vue';
import { View, Edit, Document } from '@element-plus/icons-vue';
import { useWindowSize } from '@vueuse/core';

const { t } = useI18n();
const appName = 'ExMemo';
const HEADER_HEIGHT = 80;
const markdownContent = ref('');
const previewId = 'preview-content';
const route = useRoute();
const content = ref(null);
const form = ref({});
const showPlayer = ref(true);
const speakerPlayer = ref(null);
const selectedText = ref('');
const mdPreview = ref(null);
const viewMode = ref('edit');
const { width } = useWindowSize();
const isLandscape = computed(() => width.value >= 768);
const isContentModified = ref(false);

const fetchContent = async (idx) => {
    const result = await fetchItem(idx);
    if (result.success) {
        form.value = { ...result.data };
        resetContent();
    }
}

const resetContent = async () => {
    if ('content' in form.value && form.value.content !== null) {
        let content = form.value.content;
        if (form.value.etype === 'note') {
            content = content.replace(/^---\n[\s\S]*?\n---\n/, '');
        }
        markdownContent.value = content;
        isContentModified.value = false;
    } else {
        markdownContent.value = t('notSupport');
    }
}

const setPlayer = () => {
    try {
        if (showPlayer.value) {
            if (speakerPlayer.value) {
                speakerPlayer.value.stop();
            }
            showPlayer.value = false;
            return;
        }
        showPlayer.value = true;
    } catch (error) {
        console.error('TTS error:', error);
        ElMessage.error(t('speakError') + error);
    }
}

const viewModeIcon = computed(() => {
    return viewMode.value === 'edit' ? Edit : View;
})

const toggleViewMode = () => {
    viewMode.value = viewMode.value === 'edit' ? 'preview' : 'edit';
}

const handleContentChange = () => {
    isContentModified.value = true;
}

const saveContent = async () => {
    if (!isContentModified.value) {
        ElMessage.info(t('noChanges')); // 需要在i18n中添加对应的翻译
        return;
    }

    try {
        const blob = new Blob([markdownContent.value], { type: 'text/plain' });
        const file = new File([blob], 'temp.md', { type: 'text/plain' });
        const result = await saveEntry({
            onSuccess: null,
            form: form.value,
            path: form.value.addr,
            file: file,
            onProgress: null,
            showMessage: false
        });
        if (result) {
            ElMessage.success(t('saveSuccess'));
            isContentModified.value = false;
        }
    } catch (error) {
        console.error(t('saveFail'), error);
        ElMessage.error(t('saveFail'));
    }
}

const handleSpeak = (text, index, node) => {
    if (index === -1) {
        return;
    }

    if (!node) {
        const previewElement = document.getElementById(previewId);
        if (previewElement) {
            const walker = document.createTreeWalker(
                previewElement,
                NodeFilter.SHOW_TEXT,
                null
            );
            let foundNode;
            while (foundNode = walker.nextNode()) {
                if (foundNode.textContent.includes(text)) {
                    node = foundNode;
                    break;
                }
            }
        }
    }
    
    if (node?.parentElement) {
        node.parentElement.style.backgroundColor = '#fffacd';
        
        const rect = node.parentElement.getBoundingClientRect();
        const isVisible = (
            rect.top >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)
        );
        
        if (!isVisible) {
            node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

const getContent = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    const previewElement = isLandscape.value 
        ? document.querySelector('.md-editor-preview')  // 横屏模式下查找编辑器内的预览区
        : document.getElementById(previewId);           // 竖屏模式下查找独立预览区
    
    if (text && text.length > 0 && previewElement) {
        const range = selection.getRangeAt(0);
        return range.startContainer;
    }
    
    if (previewElement) {
        const viewportTop = window.scrollY;
        const offsetTop = viewportTop + HEADER_HEIGHT;
        const walker = document.createTreeWalker(
            isLandscape.value ? previewElement : previewElement.querySelector('.md-editor-preview'),
            NodeFilter.SHOW_TEXT,
            null
        );
        
        let node;
        let bestNode = null;
        let bestDistance = Infinity;
        
        while (node = walker.nextNode()) {
            const range = document.createRange();
            range.selectNode(node);
            const rect = range.getBoundingClientRect();
            
            const absoluteTop = rect.top + window.scrollY;
            const isVisible = getComputedStyle(node.parentElement).display !== 'none' && 
                            rect.height > 0 &&
                            node.textContent.trim().length > 0;
            
            if (isVisible) {
                const distanceToOffset = Math.abs(absoluteTop - offsetTop);
                if (distanceToOffset < bestDistance && absoluteTop >= offsetTop) {
                    bestDistance = distanceToOffset;
                    bestNode = node;
                }
            }
        }
        
        return bestNode;
    }
    return null;
}

onBeforeUnmount(() => {
    if (speakerPlayer.value) {
        speakerPlayer.value.stop();
    }
})

onMounted(() => {
    fetchContent(route.query.idx);
})
</script>

<style scoped>
.app-container {
    display: flex;
    flex-direction: column;
    height: var(--mainHeight);
}

.main-content {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.main-content.landscape {
    flex-direction: row;
}

.editor-container, .preview-container {
    height: 100%;
    transition: all 0.3s ease;
}

.main-content.landscape .editor-container {
    width: 100%;
}

.main-content.landscape :deep(.md-editor) {
    height: 100%;
}

.main-content.landscape :deep(.md-editor-container) {
    transition: width 0.3s ease;
}

.main-content.landscape :deep(.md-editor-preview) {
    border-left: 1px solid #ddd;
    display: block !important;
}

.hidden {
    display: none;
}

:deep(.md-editor-preview) {
    height: 100% !important;
    overflow-y: auto !important;
    padding: 0px 10px;
}

:deep(.md-editor-preview-wrapper) {
    padding: 0px;
}
</style>
