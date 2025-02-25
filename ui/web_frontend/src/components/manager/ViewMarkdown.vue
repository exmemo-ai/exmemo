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
                                <el-button size="small" type="primary" @click="selectAll">{{ t('selectAll') }}</el-button>
                                <el-button size="small" type="primary" @click="copyContent">{{ t('copySelected') }}</el-button>
                                <el-button size="small" type="primary" v-if="form.etype === 'web'" @click="openWeb">{{ t('viewMarkdown.openWeb') }}</el-button>
                                <el-button size="small" type="primary" v-if="form.etype === 'file'" @click="download">{{ t('viewMarkdown.downloadFile') }}</el-button>
                                <el-button size="small" type="primary" @click="setPlayer">
                                    {{ showPlayer ? t('viewMarkdown.hideRead') : t('viewMarkdown.showRead') }}
                                </el-button>
                            </el-button-group>
                            <el-button-group class="highlight-buttons" style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="highlightText">
                                    {{ isHighlightMode ? t('viewMarkdown.stopHighlight') : t('viewMarkdown.showHighlight') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="clearHighlight" :disabled="!isHighlightMode">
                                    {{ t('viewMarkdown.clearHighlight') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="copyHighlight" :disabled="!isHighlightMode">
                                    {{ t('viewMarkdown.copyHighlight') }}
                                </el-button>
                            </el-button-group>
                            <el-button
                                size="small"
                                type="primary"
                                @click="toggleViewMode"
                                style="margin-right: 5px;">
                                <el-icon class="view-mode-icon">
                                    <component :is="viewModeIcon"/>
                                </el-icon>
                                {{ viewMode === 'content' ? t('viewMarkdown.contentWithNote') : t('viewMarkdown.contentOnly') }}
                            </el-button>
                        </div>
                    </div>
                </div>
            </el-container>
        </div>
        <div class="main-content" :class="viewMode">
            <div class="preview-container" ref="content" @mouseup="handleMouseUp" @touchend="handleMouseUp" @contextmenu.prevent>
                <MdPreview :id="previewId" :modelValue="markdownContent" ref="mdPreview" style="height: 100%; padding: 0px;"/>
            </div>
            <div v-show="viewMode === 'content-note'" class="editor-container">
                <div class="editor-toolbar">
                    <el-button-group>
                        <el-button size="small" type="primary" @click="selectedToNote">{{ t('viewMarkdown.insertSelected') }}</el-button>
                        <el-button size="small" type="primary" @click="highlightToNote">{{ t('viewMarkdown.insertHighlight') }}</el-button>
                        <el-button size="small" type="primary" @click="allToNote">{{ t('viewMarkdown.insertAll') }}</el-button>
                        <el-button size="small" type="primary" @click="saveAsNote">{{ t('viewMarkdown.saveAsNote') }}</el-button>
                    </el-button-group>
                </div>
                <ViewNote 
                    ref="viewNote"
                    :form="form"
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
import 'md-editor-v3/lib/preview.css';
import 'md-editor-v3/lib/style.css';
import logo from '@/assets/images/logo.png'
import { getLocale } from '@/main.js' 
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { MdPreview } from 'md-editor-v3'
import { saveEntry, downloadFile, fetchItem } from './dataUtils';
import { HighlightManager } from '@/components/manager/HighlightManager'
import '@/assets/styles/markdown-view.css'
import TextSpeakerPlayer from '@/components/manager/TextPlayer.vue'
import { View, Edit, ArrowDown } from '@element-plus/icons-vue'
import ViewNote from '@/components/manager/ViewNote.vue'
import { getSelectedNodeList, getVisibleNodeList, setHighlight } from './DOMUtils';

const { t } = useI18n()
const appName = 'ExMemo'
const markdownContent = ref(t('loading'))
const previewId = 'preview-content'
const route = useRoute()
const content = ref(null)
const form = ref({})
const highlightManager = ref(null)
const showPlayer = ref(true)
const speakerPlayer = ref(null)
const selectedText = ref('')
const mdPreview = ref(null)

const highlightChanged = ref(false)
const viewNote = ref(null)
const highlightSaveTimer = ref(null)

const clearHighlight = () => {
    highlightManager.value?.clearHighlight()
    highlightChanged.value = true
    scheduleHighlightSave()
}

const copyHighlight = () => {
    if (!highlightManager.value) return
    
    let text = highlightManager.value.getHighlightedText().join('\n')
    text = text + "\n"
    text = text + "\n" + t('title') + ": " + form.value.title
    text = text + "\n" + t('viewMarkdown.detail') + ": " + window.location.href
    text = text + "\n" + t('viewMarkdown.copiedFrom') + ": " + form.value.addr
    text = text + "\n" + t('viewMarkdown.copiedAt') + ": " + new Date().toLocaleString()
    text = text.trim()

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => ElMessage.success(t('copySuccess')))
            .catch(() => fallbackCopyTextToClipboard(text))
    } else {
        fallbackCopyTextToClipboard(text)
    }
}

const fallbackCopyTextToClipboard = (text) => {
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    try {
        const successful = document.execCommand('copy')
        if (successful) {
            ElMessage.success(t('copySuccess'))
        } else {
            ElMessage.error(t('copyFailed'))
        }
    } catch (err) {
        ElMessage.error(t('clipboardNotSupported'))
    }
    document.body.removeChild(textArea)
}

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
        await nextTick();
        viewNote.value?.loadNote();
        loadHighlight();
        setTimeout(() => {
            console.log('@@@', form.value.meta)
            if (form.value.meta?.bookmark?.position) {
                const mdPreviewContent = document.querySelector('.md-editor-preview');
                if (mdPreviewContent) {
                    mdPreviewContent.scrollTop = form.value.meta.bookmark.position;
                }
            }
        }, 100);
    } else {
        markdownContent.value = t('notSupport');
    }
    viewMode.value = 'content-note';
    console.log("viewMode", viewMode.value, form.value.etype);
}

const loadHighlight = () => {
    if (form.value.meta && highlightManager.value) {
        highlightManager.value.loadHighlight(form.value.meta)
    }
}

const openWeb = () => {
    window.open(form.value.addr, '_blank')
}

const download = () => {
    const file_path = form.value.addr;
    let filename = file_path.split('/').pop();
    downloadFile(form.value.idx, filename);
}

const selectAll = () => {
    const preview = document.querySelector('.preview-container');
    if (preview) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(preview);
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

const copyContent = () => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(markdownContent.value)
            .then(() => {
                ElMessage.success(t('copySuccess'));
            })
            .catch(() => {
                fallbackCopyTextToClipboard(markdownContent.value)
            });
    } else {
        fallbackCopyTextToClipboard(markdownContent.value)
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

const isHighlightMode = computed(() => highlightManager.value?.isHighlightMode || false)

const highlightText = () => {
    if (!highlightManager.value) return
    
    const newMode = highlightManager.value.toggleHighlightMode()
    ElMessage.success(newMode ? t('viewMarkdown.highlightModeOn') : t('viewMarkdown.highlightModeOff'))
    loadHighlight();
}

const highlightSelection = () => {
    highlightManager.value?.handleSelection()
    highlightChanged.value = true
    scheduleHighlightSave()
}

const handleMouseUp = (event) => {
    const isPlaying = speakerPlayer.value?.getStatus().isPlaying || false
    if (isPlaying) {
        const selection = window.getSelection()
        const startNode = selection.anchorNode
        if (startNode && speakerPlayer.value) {
            const previewElement = document.querySelector('.md-editor-preview');
            const nodeList = getVisibleNodeList(previewElement, startNode)
            speakerPlayer.value.stop()
            speakerPlayer.value.setContent(nodeList)
            speakerPlayer.value.resume()
        }
        return
    }
    highlightSelection()
}

const getContent = () => {
    const previewElement = document.querySelector('.md-editor-preview');
    const selectedNodeList = getSelectedNodeList(previewElement);    
    if (selectedNodeList.length > 0) {
        return selectedNodeList;
    }
    return getVisibleNodeList(previewElement);
}

const handleSpeak = (text, index, node) => {
    const previewElement = document.getElementById(previewId)
    setHighlight(text, index, node, previewElement)
}

const handleResize = () => {
    const visualHeight = window.innerHeight;
    console.log('visualHeight', visualHeight);
    document.documentElement.style.setProperty('--mainHeight', `${visualHeight}px`);
}

onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
    window.removeEventListener('resize', handleResize);
})

onMounted(() => {
    fetchContent(route.query.idx)
    highlightManager.value = new HighlightManager(content.value)
    window.addEventListener('beforeunload', handleBeforeUnload)
    window.addEventListener('resize', handleResize);
    handleResize();
})

const handleBeforeUnload = async (e) => {
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
    }
    await saveMeta(true)
    e.preventDefault()
    e.returnValue = ''
}

const viewMode = ref('content-note') // 'content' | 'content-note'

const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'content' ? 'content-note' : 'content'
}

const viewModeIcon = computed(() => {
  switch (viewMode.value) {
    case 'content':
      return View
    case 'content-note':
      return Edit
    default:
      return View
  }
})

const saveMeta = async (force) => {
    await nextTick();    
    const mdPreviewContent = document.querySelector('.md-editor-preview');
    const scrollPosition = mdPreviewContent ? mdPreviewContent.scrollTop : 0;
        
    if (force == false && !highlightChanged.value)  return

    if (!form.value.meta || form.value.meta === 'null') {
        form.value.meta = {}
    }
    
    if (typeof form.value.meta === 'string') {
        try {
            form.value.meta = JSON.parse(form.value.meta)
        } catch (error) {
            console.error('Failed to parse meta:', error)
            form.value.meta = {}
        }
    }

    if (highlightChanged.value && highlightManager.value?.hasHighlights()) {
        const serializableHighlights = highlightManager.value.getSerializableHighlights()
        form.value.meta.highlights = JSON.stringify(serializableHighlights)
    }

    form.value.meta.bookmark = {
        position: scrollPosition,
        timestamp: new Date().toISOString()
    }

    form.value.meta.note = viewNote.value.editContent

    try {
        const result = await saveEntry({
            parentObj: null,
            form: form.value,
            path: null,
            file: null,
            onProgress: null,
            showMessage: false
        })
        
        if (result) {
            highlightChanged.value = false
            console.log('saveSuccess')
        }
    } catch (error) {
        console.error(t('saveFail'), error)
        ElMessage.error(t('saveFail'))
    }
}

const scheduleHighlightSave = () => {
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
    }
    highlightSaveTimer.value = setTimeout(async () => {
        await saveMeta(false)
        highlightSaveTimer.value = null
    }, 10000) // 15s
}

const highlightToNote = () => {
    if (!highlightManager.value) return    
    let text = highlightManager.value.getHighlightedText().join('\n')
    text = text + "\n\n"
    viewNote.value.editContent = viewNote.value.editContent + text
};

const selectedToNote = () => {
    const selection = window.getSelection()
    let text = selection.toString()
    text = text + "\n\n"
    viewNote.value.editContent = viewNote.value.editContent + text
};

const allToNote = () => {
    viewNote.value.editContent = markdownContent.value
};

const saveAsNote = () => {
    viewNote.value.saveAsNote();
};

</script>

<style scoped>
/*为知为啥，只能写这里*/ 
:deep(.md-editor-preview) {
    height: 100% !important;
    overflow-y: auto !important;
    padding: 0px 10px;
}
:deep(.md-editor-preview-wrapper) {
    padding: 0px;
}
</style>