<template>
    <div class="app-container">
        <div ref="navbar" class="header">
            <el-container class="nav-container">
                <div class="top-row-view">
                    <div class="title-container">
                        <img :src="logo" class="nav-avatar" />
                        <h3 class="title">{{ appName }}</h3>
                        <div class="title-filename-container" v-if="currentFileName">
                            {{ currentFileName }}
                        </div>
                    </div>
                    <div class="nav-right">
                        <el-button size="small" type="primary" circle @click="showAIDialog">
                            {{ t('viewMarkdown.ai') }}
                        </el-button>
                    </div>
                </div>
            </el-container>
        </div>
        <div class="main-content" :class="viewMode">
            <div class="preview-container-out">
                <div class="editor-toolbar">
                    <div class="button-container-flex">
                        <el-button-group class="basic-buttons" style="margin-right: 5px;">
                            <el-button size="small" @click="selectAll" :title="t('selectAll')">
                                <el-icon><Select /></el-icon>
                            </el-button>
                            <el-button size="small" @click="copyContent" :title="t('copy')">
                                <el-icon><DocumentCopy /></el-icon>
                            </el-button>
                            <el-button size="small" v-if="form.etype === 'web'" @click="openWeb" :title="t('viewMarkdown.openWeb')">
                                <el-icon><Link /></el-icon>
                            </el-button>
                            <el-button size="small" v-if="form.etype === 'file'" @click="download" :title="t('viewMarkdown.downloadFile')">
                                <el-icon><Download /></el-icon>
                            </el-button>
                            <el-button v-if="!form.idx" size="small" @click="handleSave" :title="t('collect')">
                                <el-icon><Star /></el-icon>
                            </el-button>
                        </el-button-group>

                        <el-dropdown trigger="click">
                            <el-button size="small">
                                {{ t('viewMarkdown.highlight') }}
                                <el-icon class="el-icon--right">
                                    <arrow-down />
                                </el-icon>
                            </el-button>
                            <template #dropdown>
                                <el-dropdown-menu>
                                    <el-dropdown-item @click="copyHighlight">
                                        {{ t('viewMarkdown.copyHighlight') }}
                                    </el-dropdown-item>
                                    <el-dropdown-item @click="clearHighlight">
                                        {{ t('viewMarkdown.clearHighlight') }}
                                    </el-dropdown-item>
                                </el-dropdown-menu>
                            </template>
                        </el-dropdown>

                        <div style="margin-left: auto; margin-right: 5px;">
                            <el-button size="small" class="zoomButton" circle @click="decreaseFontSize">
                                <el-icon>
                                    <FontSmallIcon />
                                </el-icon>
                            </el-button>
                            <el-button size="small" class="zoomButton" circle @click="increaseFontSize">
                                <el-icon>
                                    <FontLargeIcon />
                                </el-icon>
                            </el-button>
                        </div>
                        <el-checkbox v-model="showNote" size="small">
                            {{ t('note') }}
                        </el-checkbox>
                        <div class="progress-text">{{ readingProgress }}%</div>
                    </div>
                </div>
                <div class="preview-container">
                    <div class="catalog-control" @click="toggleCatalog">
                        <el-icon :class="{ 'is-active': showCatalog }">
                            <Expand v-if="!showCatalog" />
                            <Fold v-else />
                        </el-icon>
                    </div>

                    <div v-show="showCatalog" class="catalog-container">
                        <MdCatalog :editorId="previewId" :scrollElement="'.md-editor-preview-wrapper'"
                            class="md-catalog" />
                    </div>
                    <div class="content-container" ref="content" @mouseup="handleMouseUp" @touchend="handleMouseUp"
                        @contextmenu.prevent">
                        <MdPreview :editorId="previewId" :modelValue="markdownContent" :previewTheme="'default'"
                            :preview-lazy="true" ref="mdPreview" style="height: 100%; padding: 0px;" />

                        <div v-show="contextMenuVisible" class="context-menu"
                            :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }">
                            <div class="context-menu-item">
                                <div class="context-menu-buttons">
                                    <div class="context-menu-button" :title="t('viewMarkdown.addToNote')"
                                        @click="handleAddToNote">
                                        <el-icon>
                                            <DocumentAdd />
                                        </el-icon>
                                    </div>
                                    <div class="context-menu-button" title="AI" @click="handleAskAI">
                                        <el-icon>
                                            <ChatDotSquare />
                                        </el-icon>
                                    </div>
                                    <div class="context-menu-button" :title="t('copy')" @click="handleCopySelection">
                                        <el-icon>
                                            <DocumentCopy />
                                        </el-icon>
                                    </div>
                                    <div class="context-menu-button" :title="t('translate')" @click="handleTranslate">
                                        <el-icon>
                                            <TranslateIcon />
                                        </el-icon>
                                    </div>
                                </div>
                            </div>
                            <div class="context-menu-item">
                                <div class="context-menu-buttons">
                                    <div v-for="(color, index) in ['pink', 'blue', 'yellow', 'green', 'purple']"
                                        :key="color" :class="['highlight-color-button', color]"
                                        @click.stop="highlightSelection(index)"></div>
                                    <div class="context-menu-button" @click.stop="handleHighlightAction"
                                        :title="hasHighlight ? t('viewMarkdown.clearHighlight') : ''">
                                        <el-icon v-if="hasHighlight">
                                            <Delete />
                                        </el-icon>
                                        <el-icon v-else>
                                            <Close />
                                        </el-icon>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="showTranslatePopup"
                            :style="{ top: `${translatePosition.y}px`, left: `${translatePosition.x}px`, maxHeight: '200px', height: 'auto', overflow: 'auto' }"
                            class="popup">
                            <div style="display: flex; flex-direction: column; margin: 5px;">
                                <div style="flex-grow: 0; text-align: left; white-space: pre-line;">
                                    {{ translatedText }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-show="viewMode === 'content-note'" class="editor-container">
                <div class="editor-toolbar">
                    <el-button-group>
                        <el-button size="small" @click="selectedToNote" :title="t('viewMarkdown.insertSelected')">
                            <el-icon><DocumentAdd /></el-icon>
                        </el-button>
                        <el-button size="small" @click="allToNote" :title="t('viewMarkdown.insertAll')">
                            <el-icon><Files /></el-icon>
                        </el-button>
                        <el-button size="small" @click="saveAsNote" :title="t('viewMarkdown.saveAsNote')">
                            <el-icon><SaveAsIcon /></el-icon>
                        </el-button>
                        <el-button size="small" v-if="isPaper" @click="parsePaper" :title="t('paperAnalysis')">
                            <el-icon><Search /></el-icon>
                        </el-button>
                    </el-button-group>
                </div>
                <ViewNote ref="viewNote" :form="form" @note-change="handleNoteChange" />
            </div>
        </div>

        <TextSpeakPlayer :text="selectedText" :lang="getLocale()" :getContentCallback="getContent" ref="txtPlayer"
            @onSpeak="handleSpeak" />
        <AIDialog v-model="aiDialogVisible" :full-content="markdownContent" :selected-content="getSelectedContent()"
            :screen-content="getScreenContent()" :etype="etype" @insert-note="handleInsertAIAnswer" />
    </div>
</template>

<script setup>
import 'md-editor-v3/lib/preview.css';
import 'md-editor-v3/lib/style.css';
import '@/assets/styles/markdown-view.css'
import logo from '@/assets/images/logo.png'
import { getLocale } from '@/main.js'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { MdPreview, MdCatalog } from 'md-editor-v3'
import { saveEntry, downloadFile, fetchItem } from './dataUtils';
import { HighlightManager } from '@/components/manager/HighlightManager'
import TextSpeakPlayer from '@/components/manager/TextPlayer.vue'
import { Expand, Fold, ArrowDown, Close, DocumentAdd, ChatDotSquare, DocumentCopy, Delete, Select, Link, Download, Star, Document, Files, Search } from '@element-plus/icons-vue'
import FontSmallIcon from '@/components/icons/FontSmallIcon.vue'
import FontLargeIcon from '@/components/icons/FontLargeIcon.vue'
import TranslateIcon from '@/components/icons/TranslateIcon.vue'
import SaveAsIcon from '@/components/icons/SaveAsIcon.vue'
import ViewNote from '@/components/manager/ViewNote.vue'
import { getSelectedNodeList, getVisibleNodeList, setHighlight } from './DOMUtils';
import AIDialog from '@/components/ai/AIDialog.vue'
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn'
import { translateFunc } from '@/components/translate/TransFunction'

const { t } = useI18n()
const appName = 'ExMemo'
const markdownContent = ref(t('loading'))
const previewId = 'preview-content-' + Date.now()
const route = useRoute()
const content = ref(null)
const form = ref({})
const highlightManager = ref(null)
const txtPlayer = ref(null)
const selectedText = ref('')
const mdPreview = ref(null)
const etype = "view"

const metaChanged = ref(false)
const viewNote = ref(null)
const saveTimer = ref(null)

const fontSize = ref(16)

const clearHighlight = () => {
    highlightManager.value?.clearHighlight()
    metaChanged.value = true
    scheduleSave(5)
}

const copyHighlight = () => {
    if (!highlightManager.value) return

    let text = highlightManager.value.getHighlightedText().join('\n\n')
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

const fetchWeb = async (url) => {
    const formData = new FormData();
    formData.append('content', url);
    formData.append('rtype', 'markdown');
    try {
        const res = await axios.post(getURL() + 'api/web/', formData);
        if (res.data.status === 'success') {
            ElMessage.info(t('paste.openClipboardContent'));
            form.value = {
                content: res.data.content,
                title: res.data.title,
                addr: url,
                etype: 'web'
            };
            resetContent();
        }
    } catch (err) {
        parseBackendError(null, err);
        markdownContent.value = t('fetchFailed');
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
        setTimeout(() => {
            if (form.value.meta?.bookmark?.position) {
                const mdPreviewContent = document.querySelector('.md-editor-preview-wrapper');
                if (mdPreviewContent) {
                    const scrollHeight = mdPreviewContent.scrollHeight - mdPreviewContent.clientHeight;
                    mdPreviewContent.scrollTop = form.value.meta.bookmark.position * scrollHeight / 100;
                }
            }
            loadHighlight();
        }, 100);
    } else {
        markdownContent.value = t('notSupport');
    }
    viewMode.value = 'content';
    console.log("viewMode", viewMode.value, form.value.etype);
    await nextTick()
    if (form.value.meta?.fontSize) {
        fontSize.value = form.value.meta.fontSize
        updatePreviewFontSize()
    }
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

const highlightSelection = (index) => {
    if (highlightManager.value?.addHighlight(index)) {
        metaChanged.value = true
        scheduleSave(5)
    }
    contextMenuVisible.value = false
}

const handleMouseUp = (event) => {
    if (event.target.classList.contains('context-menu-button')) {
        return
    }

    const isPlaying = txtPlayer.value?.getStatus().isPlaying || false
    if (isPlaying) {
        const selection = window.getSelection()
        const startNode = selection.anchorNode
        if (startNode && txtPlayer.value) {
            const previewElement = document.querySelector('.md-editor-preview');
            const nodeList = getVisibleNodeList(previewElement, startNode)
            txtPlayer.value.stop()
            txtPlayer.value.setContent(nodeList)
            txtPlayer.value.resume()
        }
        return
    }
    handleSelectArea(event)
    event.preventDefault()
    event.stopPropagation()
}

const handleSelectArea = (event) => {
    const selection = window.getSelection()
    if (!selection || selection.toString().trim() === '') {
        contextMenuVisible.value = false
        return
    }

    const range = selection.getRangeAt(0)
    const commonAncestor = range.commonAncestorContainer
    const highlightElement = commonAncestor.nodeType === 3
        ? commonAncestor.parentElement?.closest('.custom-highlight')
        : commonAncestor.querySelector('.custom-highlight')
    hasHighlight.value = !!highlightElement

    const menuWidth = 160
    const menuHeight = 88
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let x = event.clientX
    let y = event.clientY
    if (x + menuWidth > viewportWidth) {
        x = viewportWidth - menuWidth - 10
    }
    if (y + menuHeight > viewportHeight) {
        y = y - menuHeight
    }
    x = Math.max(10, x)
    y = Math.max(10, y)

    contextMenuPosition.value = { x, y }
    nextTick(() => {
        contextMenuVisible.value = true
    })
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
    document.documentElement.style.setProperty('--mainHeight', `${visualHeight}px`);
}

onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
    window.removeEventListener('resize', handleResize);
})

const previewScrollElement = ref(null)

onMounted(() => {
    if (route.query.idx) {
        fetchContent(route.query.idx)
    } else if (route.query.url) {
        fetchWeb(route.query.url)
    } else {
        markdownContent.value = t('notSupport')
    }
    highlightManager.value = new HighlightManager(content.value)
    window.addEventListener('beforeunload', handleBeforeUnload)
    window.addEventListener('resize', handleResize);
    handleResize();
    nextTick(() => {
        previewScrollElement.value = document.querySelector('.md-editor-preview')
    })
    document.addEventListener('click', (e) => {
        const menu = document.querySelector('.context-menu')
        if (menu && !menu.contains(e.target) &&
            (Math.abs(e.clientX - contextMenuPosition.value.x) > 10 ||
                Math.abs(e.clientY - contextMenuPosition.value.y) > 10)) {
            contextMenuVisible.value = false
        }
        if (showTranslatePopup.value &&
            new Date().getTime() - translateTimer.value > 1000) {
            showTranslatePopup.value = false
        }
    })
})

const handleBeforeUnload = async (e) => {
    if (saveTimer.value) {
        clearTimeout(saveTimer.value)
    }
    await saveMeta(true)
    e.preventDefault()
    e.returnValue = ''
}

const viewMode = computed(() => showNote.value ? 'content-note' : 'content')
const showNote = ref(false)

const saveMeta = async (force) => {
    console.log('real saveMeta')
    if (!form.value.idx) return
    await nextTick();
    const mdPreviewContent = document.querySelector('.md-editor-preview-wrapper');
    let scrollPosition = 0;
    if (mdPreviewContent) {
        const scrollHeight = mdPreviewContent.scrollHeight - mdPreviewContent.clientHeight;
        scrollPosition = Math.round((mdPreviewContent.scrollTop / scrollHeight) * 1000) / 10;
    }

    if (force == false && !metaChanged.value) return

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

    if (metaChanged.value && highlightManager.value?.hasHighlights()) {
        const serializableHighlights = highlightManager.value.getSerializableHighlights()
        form.value.meta.highlights = JSON.stringify(serializableHighlights)
    }

    form.value.meta.bookmark = {
        position: scrollPosition,
        timestamp: new Date().toISOString()
    }

    form.value.meta.note = viewNote.value.editContent
    form.value.meta.fontSize = fontSize.value

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
            metaChanged.value = false
            console.log('saveSuccess')
        }
    } catch (error) {
        console.error(t('saveFail'), error)
        ElMessage.error(t('saveFail'))
    }
}

const scheduleSave = (timeout) => {
    console.log('scheduleSave, wait', timeout)
    if (saveTimer.value) {
        clearTimeout(saveTimer.value)
    }
    saveTimer.value = setTimeout(async () => {
        await saveMeta(false)
        saveTimer.value = null
    }, timeout * 1000)
}

const selectedToNote = () => {
    const selection = window.getSelection()
    let text = selection.toString()
    text = text.trim()
    text = text.split('\n').map(line => '> ' + line).join('\n')
    text = t('viewMarkdown.estreat') + ": " + readingProgress.value + "%" + "\n" + text + "\n\n"
    let content = viewNote.value.editContent.trim()
    if (content.length > 0) {
        content = content + "\n\n" + text
    } else {
        content = text
    }
    viewNote.value.editContent = content
};

const allToNote = () => {
    viewNote.value.editContent = markdownContent.value
};

const saveAsNote = () => {
    viewNote.value.saveAsNote();
};

const aiDialogVisible = ref(false)

const showAIDialog = () => {
    aiDialogVisible.value = true
}

const getSelectedContent = () => {
    const selection = window.getSelection()
    return selection.toString()
}

const getScreenContent = () => {
    const preview = document.querySelector('.md-editor-preview')
    if (!preview) return ''

    const previewWrapper = preview.closest('.md-editor-preview-wrapper')
    if (!previewWrapper) return ''

    const walker = document.createTreeWalker(
        preview,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: (node) => {
                if (node.textContent?.trim() === '') {
                    return NodeFilter.FILTER_REJECT
                }
                return NodeFilter.FILTER_ACCEPT
            }
        }
    )

    let visibleText = ''
    let node
    while (node = walker.nextNode()) {
        const range = document.createRange()
        range.selectNodeContents(node)
        const rect = range.getBoundingClientRect()
        const elementTop = rect.top
        const elementBottom = rect.bottom
        const wrapperRect = previewWrapper.getBoundingClientRect()

        if (elementBottom > wrapperRect.top && elementTop < wrapperRect.bottom) {
            visibleText += node.textContent.trim() + '\n'
        }
    }
    return visibleText.trim()
}

const handleInsertAIAnswer = (text) => {
    if (!text) return
    text = text + "\n\n"
    viewNote.value.editContent = viewNote.value.editContent + text
    ElMessage.success(t('viewMarkdown.insertSuccess'))
}

const showCatalog = ref(false)

const toggleCatalog = () => {
    showCatalog.value = !showCatalog.value
}

const readingProgress = ref(0)

const updateReadingProgress = () => {
    const mdPreviewContent = document.querySelector('.md-editor-preview-wrapper')
    if (!mdPreviewContent) return

    const scrollPosition = mdPreviewContent.scrollTop
    const scrollHeight = mdPreviewContent.scrollHeight - mdPreviewContent.clientHeight
    const progress = Math.round((scrollPosition / scrollHeight) * 1000) / 10
    readingProgress.value = Math.min(100, Math.max(0, progress))
    metaChanged.value = true
    scheduleSave(10) // save bookmark
}

onMounted(() => {
    const mdPreviewContent = document.querySelector('.md-editor-preview-wrapper')
    if (mdPreviewContent) {
        mdPreviewContent.addEventListener('scroll', updateReadingProgress)
    }
})

onBeforeUnmount(() => {
    const mdPreviewContent = document.querySelector('.md-editor-preview-wrapper')
    if (mdPreviewContent) {
        mdPreviewContent.removeEventListener('scroll', updateReadingProgress)
    }
})

const currentFileName = computed(() => {
    if (form.value && form.value.title) {
        return form.value.title.split('/').pop();
    }
    return '';
});

const handleNoteChange = async () => {
    metaChanged.value = true
    scheduleSave(30)
}

const increaseFontSize = () => {
    fontSize.value = Math.min(fontSize.value + 2, 32)
    updatePreviewFontSize()
}

const decreaseFontSize = () => {
    fontSize.value = Math.max(fontSize.value - 2, 12)
    updatePreviewFontSize()
}

const updatePreviewFontSize = () => {
    const preview = document.querySelector('.md-editor-preview')
    if (preview) {
        preview.style.fontSize = `${fontSize.value}px`
    }
    metaChanged.value = true
    scheduleSave(10)
}

const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })

const handleAddToNote = () => {
    selectedToNote()
    contextMenuVisible.value = false
    showNote.value = true
}

const hasHighlight = ref(false)

const handleHighlightAction = () => {
    if (hasHighlight.value) {
        if (highlightManager.value?.removeHighlight()) {
            metaChanged.value = true
            scheduleSave(5)
        }
    }
    contextMenuVisible.value = false
}

const handleAskAI = () => {
    contextMenuVisible.value = false
    aiDialogVisible.value = true
}

const handleTranslate = () => {
    contextMenuVisible.value = false
    const selection = window.getSelection()
    const text = selection.toString().trim()
    if (!text) return

    const rect = selection.getRangeAt(0).getBoundingClientRect()
    translatePosition.value = {
        x: rect.left,
        y: rect.bottom + window.scrollY
    }

    if (text.indexOf(' ') === -1 && text.length < 20 && /^[a-zA-Z]+$/.test(text)) {
        let sentence = getSentence(selection.anchorNode)
        let word = getWord(selection.anchorNode)
        console.log('sentence', sentence)
        console.log('word', word)
        translateFunc(null, 'word', word, sentence, translateCallback)
    } else {
        translateFunc(null, 'sentence', null, text, translateCallback)
    }
}

const getWord = (element) => {
    const text = element.textContent
    const selection = window.getSelection()
    const range = selection.getRangeAt(0)

    let start = range.startOffset
    let end = range.endOffset

    while (start > 0 && !/\s/.test(text[start - 1])) {
        start--
    }
    while (end < text.length && !/\s/.test(text[end])) {
        end++
    }
    return text.substring(start, end).trim()
}

const getSentence = (element) => {
    let paragraph = getParagraph(element)
    if (paragraph.length > 0) {
        let sentences = paragraph.match(/[^\.!\?]+[\.!\?]+/g)
        const text = element.textContent
        let ret = paragraph
        //console.log('sentence', sentences)
        if (sentences && sentences.length > 0) {
            for (let i = 0; i < sentences.length; i++) {
                if (text.indexOf(sentences[i]) !== -1) {
                    ret = sentences[i]
                    break
                }
            }
        }
        //console.log('ret', ret)
        return ret
    } else {
        return ''
    }
}

const getParagraph = (element) => {
    while (element && element.nodeType === 3) {
        element = element.parentNode
    }
    const container = element.closest('p, div, li')
    if (!container) {
        return element.textContent?.trim() || ''
    }
    return container.textContent?.trim() || ''
}

const translateCallback = (info) => {
    translatedText.value = info
    showTranslatePopup.value = true
    translateTimer.value = new Date().getTime()
}

const handleCopySelection = () => {
    contextMenuVisible.value = false
    const selection = window.getSelection()
    const text = selection.toString().trim()
    if (!text) return

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => ElMessage.success(t('copySuccess')))
            .catch(() => fallbackCopyTextToClipboard(text))
    } else {
        fallbackCopyTextToClipboard(text)
    }
}

const handleSave = async () => {
    if (!form.value.content) {
        ElMessage.warning(t('noContent'))
        return
    }

    try {
        const result = await saveEntry({
            parentObj: null,
            form: form.value,
            path: null,
            file: null
        })

        if (result && result.status === 'success') {
            getNewIdx()
        }
    } catch (error) {
        console.error(t('saveFail'), error)
        ElMessage.error(t('saveFail'))
    }
}

const getNewIdx = () => {
    const addr = form.value.addr;
    let func = 'api/entry/data/'
    let params = {
        keyword: addr,
        etype: 'web',
        max_count: 1
    }
    axios.get(getURL() + func, { params: params })
        .then(response => {
            const results = response.data['results'];
            if (results && results.length > 0) {
                form.value.idx = results[0].idx
            }
        })
        .catch(error => {
            console.error('Failed to get idx:', error)
        })
}

const showTranslatePopup = ref(false)
const translatePosition = ref({ x: 0, y: 0 })
const translatedText = ref('')
const translateTimer = ref(null)

const isPaper = computed(() => {
    if (!form.value || !form.value.addr) return false
    return form.value.etype === 'web' && (
        form.value.addr.includes('arxiv.org')
    )
})

const parsePaper = async () => {
    const formData = new FormData();
    formData.append('content', form.value.addr);
    formData.append('rtype', 'search')
    axios.post(getURL() + 'api/paper/', formData).then((res) => {
        if (res.data.status == 'success') {
            let note = viewNote.value.editContent;
            if (note.length > 0) {
                note = note + "\n\n";
            }
            note = note + res.data.info;
            viewNote.value.editContent = note;
            this.$message({
                message: this.$t('searchSuccess'),
                type: 'success'
            });
        }
    }).catch((err) => {
        parseBackendError(this, err);
    });
}
</script>

<style scoped>
/*为知为啥，只能写这里*/
:deep(.md-editor-preview) {
    height: auto;
    overflow-y: auto !important;
    padding: 10px 20px;
    max-width: 960px;
    margin: 0 auto;
    font-size: v-bind('fontSize + "px"');
}

:deep(.md-editor-preview-wrapper) {
    padding: 0px;
}

:deep(.md-editor-catalog) {
    border: none !important;
    height: 100% !important;
}

:deep(.md-editor-catalog-title) {
    padding: 10px !important;
    border-bottom: 1px solid #e6e6e6;
}

:deep(.md-editor-catalog-list) {
    padding: 10px !important;
}

:deep(.el-dropdown-menu__item.is-active) {
    color: #409EFF;
    font-weight: bold;
}

.popup {
    margin: 2px;
    position: fixed;
    width: 200px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    font-size: 12px;
    z-index: 9999;
    padding: 8px;
}

.el-button {
    padding: 8px 12px;
}

.el-button-group .el-button {
    padding: 8px 12px;
}
</style>