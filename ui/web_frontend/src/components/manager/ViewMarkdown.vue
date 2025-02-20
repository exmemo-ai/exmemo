<template>
    <el-container class="app-container">
        <el-header class="header" height="auto" style="padding: 0;">
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
                                <el-button size="small" type="primary" @click="addBookmark">{{ t('viewMarkdown.addBookmark') }}</el-button>
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
                            <el-dropdown 
                                trigger="click" 
                                @command="setViewMode"
                                style="margin-right: 5px;">
                                <el-button size="small" type="primary">
                                    <el-icon class="view-mode-icon">
                                        <component :is="viewModeIcon"/>
                                    </el-icon>
                                    <el-icon><ArrowDown /></el-icon>
                                </el-button>
                                <template #dropdown>
                                    <el-dropdown-menu>
                                        <el-dropdown-item 
                                            command="content"
                                            :icon="View">
                                            {{ t('viewMarkdown.contentOnly') }}
                                        </el-dropdown-item>
                                        <el-dropdown-item 
                                            command="content-note"
                                            :icon="Edit">
                                            {{ t('viewMarkdown.contentWithNote') }}
                                        </el-dropdown-item>
                                    </el-dropdown-menu>
                                </template>
                            </el-dropdown>
                        </div>
                    </div>
                </div>
            </el-container>
        </el-header>
        <div class="main-content" :class="viewMode">
            <div class="preview-container" ref="content" @mouseup="handleMouseUp" @touchend="handleMouseUp" @contextmenu.prevent>
                <MdPreview :id="previewId" :modelValue="markdownContent" ref="mdPreview" style="height: 100%;"/>
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
        
        <div v-if="showPlayer" class="player-footer">
            <TextSpeakerPlayer
                :text="selectedText"
                :lang="getLocale()"
                :getContentCallback="getContent"
                ref="speakerPlayer"
                @onSpeak="handleSpeak"
            />
        </div>
    </el-container>
</template>

<script setup>
import 'md-editor-v3/lib/preview.css';
import 'md-editor-v3/lib/style.css';
import axios from 'axios';
import logo from '@/assets/images/logo.png'
import { setDefaultAuthHeader,getURL,parseBackendError } from '@/components/support/conn'
import { getLocale } from '@/main.js' 
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { MdPreview } from 'md-editor-v3'
import { saveEntry, downloadFile } from './dataUtils';
import { HighlightManager } from '@/components/manager/HighlightManager'
import '@/assets/styles/markdown-view.css'
import TextSpeakerPlayer from '@/components/manager/TextPlayer.vue'
import { View, Edit, ArrowDown } from '@element-plus/icons-vue'
import ViewNote from '@/components/manager/ViewNote.vue'

const { t } = useI18n()
const appName = 'ExMemo'
const HEADER_HEIGHT = 80
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

const currentHighlight = ref(null)
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
    let table_name = 'data'
    setDefaultAuthHeader();
    try {
        const response = await axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/');
        form.value = { ...response.data };
        resetContent();
    } catch (error) {
        if (error.response && error.response.status === 401) {
            parseBackendError(null, error);
        } else {
            console.error(error)
            ElMessage.error(t('operationFailed'));
        }
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
            if (form.value.meta?.bookmark?.position) {
                window.scrollTo({
                    top: form.value.meta.bookmark.position,
                    behavior: 'smooth'
                });
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

const addBookmark = async () => {
    const scrollPosition = window.scrollY || window.pageYOffset

    if (!form.value.meta) {
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
    
    form.value.meta.bookmark = {
        position: scrollPosition,
        timestamp: new Date().toISOString()
    }

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
            ElMessage.success(t('viewMarkdown.addBookmarkSuccess'))
        }
    } catch (error) {
        console.error(t('viewMarkdown.addBookmarkFail'), error)
        ElMessage.error(t('viewMarkdown.addBookmarkFail'))
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
        const node = selection.anchorNode
        if (node && speakerPlayer.value) {
            speakerPlayer.value.stop()
            speakerPlayer.value.setContent(node)
            speakerPlayer.value.resume()
        }
        return
    }
    highlightSelection()
}

const getContent = () => {
    const selection = window.getSelection()
    const text = selection.toString().trim()
    const previewElement = document.getElementById(previewId)
    
    if (text && text.length > 0 && previewElement) {
        const range = selection.getRangeAt(0)
        return range.startContainer
    }
    
    if (previewElement) {
        const viewportTop = window.scrollY
        const offsetTop = viewportTop + HEADER_HEIGHT
        const walker = document.createTreeWalker(
            previewElement,
            NodeFilter.SHOW_TEXT,
            null
        )
        
        let node
        let bestNode = null
        let bestDistance = Infinity
        
        while (node = walker.nextNode()) {
            const range = document.createRange()
            range.selectNode(node)
            const rect = range.getBoundingClientRect()
            
            const absoluteTop = rect.top + window.scrollY
            const isVisible = getComputedStyle(node.parentElement).display !== 'none' && 
                            rect.height > 0 &&
                            node.textContent.trim().length > 0
            
            if (isVisible) {
                const distanceToOffset = Math.abs(absoluteTop - offsetTop)
                if (distanceToOffset < bestDistance && absoluteTop >= offsetTop) {
                    bestDistance = distanceToOffset
                    bestNode = node
                }
            }
        }
        
        return bestNode
    }
    return null
}

const handleSpeak = (text, index, node) => {
    if (currentHighlight.value) {
        currentHighlight.value.style.backgroundColor = ''
    }

    if (index === -1) {
        return
    }

    if (!node) {
        const previewElement = document.getElementById(previewId)
        if (previewElement) {
            const walker = document.createTreeWalker(
                previewElement,
                NodeFilter.SHOW_TEXT,
                null
            )
            let foundNode
            while (foundNode = walker.nextNode()) {
                if (foundNode.textContent.includes(text)) {
                    node = foundNode
                    break
                }
            }
        }
    }
    
    if (node?.parentElement) {
        node.parentElement.style.backgroundColor = '#fffacd'
        currentHighlight.value = node.parentElement
        
        const rect = node.parentElement.getBoundingClientRect()
        const isVisible = (
            rect.top >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)
        )
        
        if (!isVisible) {
            node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
    }
}

onBeforeUnmount(() => {
    if (currentHighlight.value) {
        currentHighlight.value.style.backgroundColor = ''
    }
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
        saveMeta()
    }
    window.removeEventListener('beforeunload', handleBeforeUnload)
})

onMounted(() => {
    fetchContent(route.query.idx)
    highlightManager.value = new HighlightManager(content.value)
    window.addEventListener('beforeunload', handleBeforeUnload)
})

const handleBeforeUnload = async (e) => {
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
        await saveMeta()
    }
    e.preventDefault()
    e.returnValue = ''
}

const viewMode = ref('content-note') // 'content' | 'content-note'

const setViewMode = (mode) => {
  viewMode.value = mode
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

const saveMeta = async () => {
    if (!highlightChanged.value) return

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

    try {
        const result = await saveEntry({
            parentObj: null,
            form: form.value,
            path: null,
            file: null,
            onProgress: null
        })
        
        if (result) {
            highlightChanged.value = false
            console.log('saveSuccess')
        }
    } catch (error) {
        console.error(t('viewMarkdown.saveHighlightFail'), error)
        ElMessage.error(t('viewMarkdown.saveHighlightFail'))
    }
}

const scheduleHighlightSave = () => {
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
    }
    highlightSaveTimer.value = setTimeout(async () => {
        await saveMeta()
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

<style>
</style>
