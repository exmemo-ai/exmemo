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
                                    {{ viewMode === 'edit' ? t('viewMarkdown.previewMode') : t('viewMarkdown.editMode') }}
                                </el-button>
                            </el-button-group>
                            <el-button-group style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="handlePolish">
                                    {{ t('aiDialog.commonQuestions.polish') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="handleSummarize">
                                    {{ t('aiDialog.commonQuestions.summary') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="handleGenerate">
                                    {{ t('aiDialog.commonQuestions.generate') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="handleStyle">
                                    {{ t('aiDialog.commonQuestions.style') }}
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
                    ref="mdEditor"
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
                ref="content"
                @mouseup="handleMouseUp" 
                @touchend="handleMouseUp"
                @contextmenu.prevent>
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
        <AIDialog
            v-model="aiDialogVisible"
            :full-content="markdownContent"
            :selected-content="getSelectedContent()"
            :screen-content="getScreenContent()"
            :common-questions="predefinedQuestions"
            :default-reference-type="defaultReferenceType"
            @insertNote="handleInsertAIAnswer"
        />
    </div>
</template>

<script setup>
import 'md-editor-v3/lib/style.css';
import logo from '@/assets/images/logo.png';
import { getLocale } from '@/main.js';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue';
import { MdEditor, MdPreview } from 'md-editor-v3';
import { saveEntry, fetchItem } from './dataUtils';
import TextSpeakerPlayer from '@/components/manager/TextPlayer.vue';
import { View, Edit, Document } from '@element-plus/icons-vue';
import { useWindowSize } from '@vueuse/core';
import { getSelectedNodeList, getVisibleNodeList, setHighlight } from './DOMUtils';
import AIDialog from './AIDialog.vue';
import { getPolishQuestions, getSummaryQuestions, getGenerateQuestions, getStyleQuestions } from './predefinedQuestions';

const { t } = useI18n();
const appName = 'ExMemo';
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
const mdEditor = ref(null);
const aiDialogVisible = ref(false);
const predefinedQuestions = ref([]);
const defaultReferenceType = ref('');

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
        ElMessage.info(t('noChanges'));
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
    const previewElement = isLandscape.value 
        ? document.querySelector('.md-editor-preview')
        : document.getElementById(previewId);
    setHighlight(text, index, node, previewElement);
}

const getContent = () => {
    const previewElement = isLandscape.value 
        ? document.querySelector('.md-editor-preview')  
        : document.getElementById(previewId);   
    const selectedNodeList = getSelectedNodeList(previewElement);
    if (selectedNodeList.length > 0) {
        return selectedNodeList;
    }
    return getVisibleNodeList(previewElement);
}

const handleMouseUp = (event) => {
    const isPlaying = speakerPlayer.value?.getStatus().isPlaying || false
    if (isPlaying) {
        const selection = window.getSelection()
        const startNode = selection.anchorNode
        if (startNode && speakerPlayer.value) {
            const previewElement = isLandscape.value 
                ? document.querySelector('.md-editor-preview')
                : document.getElementById(previewId);
            const nodeList = getVisibleNodeList(previewElement, startNode)
            speakerPlayer.value.stop()
            speakerPlayer.value.setContent(nodeList)
            speakerPlayer.value.resume()
        }
    }
}

const handleSummarize = () => {
    predefinedQuestions.value = getSummaryQuestions(t);
    defaultReferenceType.value = 'all';
    nextTick(() => {
        aiDialogVisible.value = true;
    });
}

const handlePolish = () => {
    predefinedQuestions.value = getPolishQuestions(t);
    defaultReferenceType.value = getSelectedContent()?.trim() ? 'selection' : 'screen';
    nextTick(() => {
        aiDialogVisible.value = true;
    });
}

const handleGenerate = () => {
    predefinedQuestions.value = getGenerateQuestions(t);
    defaultReferenceType.value = 'all';
    nextTick(() => {
        aiDialogVisible.value = true;
    });
}

const handleStyle = () => {
    predefinedQuestions.value = getStyleQuestions(t);
    defaultReferenceType.value = 'all';
    nextTick(() => {
        aiDialogVisible.value = true;
    });
}

const getSelectedContent = () => {
    const selection = window.getSelection();
    return selection.toString();
}

const getScreenContent = () => {
    const previewElement = isLandscape.value 
        ? document.querySelector('.md-editor-preview')
        : document.getElementById(previewId);
    if (!previewElement) return '';
    
    const visibleHeight = previewElement.clientHeight;
    const previewRect = previewElement.getBoundingClientRect();
    const walker = document.createTreeWalker(
        previewElement,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: (node) => {
                if (node.textContent?.trim() === '') {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );
    
    let visibleText = '';
    let node;
    while (node = walker.nextNode()) {
        const range = document.createRange();
        range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        const elementTop = rect.top - previewRect.top;
        const elementBottom = rect.bottom - previewRect.top;
        
        if (elementTop >= 0 && elementTop <= visibleHeight && elementBottom >= 0) {
            visibleText += node.textContent.trim() + '\n';
        }
    }
    
    return visibleText.trim();
}

const handleInsertAIAnswer = (text) => {
    if (!text) return;
    if (mdEditor.value) {
        mdEditor.value?.insert(() => {
            return {
                targetValue: text + '\n\n',
                select: true,
                deviationStart: 0,
                deviationEnd: 0
            };
        });
        isContentModified.value = true;
    }
    ElMessage.success(t('viewMarkdown.insertSuccess'));
}

onBeforeUnmount(() => {
    if (speakerPlayer.value) {
        speakerPlayer.value.stop();
    }
})

onMounted(() => {
    fetchContent(route.query.idx);
    nextTick(() => {
        if (mdEditor.value?.$el) {
            const previewElement = mdEditor.value.$el.querySelector('.md-editor-preview');
            if (previewElement) {
                previewElement.addEventListener('mouseup', handleMouseUp);
                previewElement.addEventListener('touchend', handleMouseUp);
                previewElement.addEventListener('contextmenu', (e) => e.preventDefault());
            }
        }
    });
});
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
