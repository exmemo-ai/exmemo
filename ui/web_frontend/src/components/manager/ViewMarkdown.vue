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
                            <el-button size="small" type="primary" @click="selectAll">{{ t('selectAll')
                            }}</el-button>
                            <el-button size="small" type="primary" @click="copyContent">{{ t('copy')
                            }}</el-button>
                            <el-button size="small" type="primary" v-if="form.etype === 'web'" @click="openWeb">{{
                                t('viewMarkdown.openWeb') }}</el-button>
                            <el-button size="small" type="primary" v-if="form.etype === 'file'" @click="download">{{
                                t('viewMarkdown.downloadFile') }}</el-button>
                            <!--
                            <el-button size="small" type="primary" @click="setPlayer">
                                {{ showPlayer ? t('viewMarkdown.hideRead') : t('viewMarkdown.showRead') }}
                            </el-button>
                            -->
                        </el-button-group>

                        <el-dropdown trigger="click">
                            <el-button size="small" type="primary">
                                {{ t('viewMarkdown.highlight') }}
                                <el-icon class="el-icon--right">
                                    <arrow-down />
                                </el-icon>
                            </el-button>
                            <template #dropdown>
                                <el-dropdown-menu>
                                    <el-dropdown-item @click="highlightText" :class="{ 'is-active': isHighlightMode }">
                                        {{ isHighlightMode ? t('viewMarkdown.stopHighlight') :
                                        t('viewMarkdown.showHighlight') }}
                                    </el-dropdown-item>
                                    <el-dropdown-item @click="copyHighlight" :disabled="!isHighlightMode">
                                        {{ t('viewMarkdown.copyHighlight') }}
                                    </el-dropdown-item>
                                    <el-dropdown-item @click="clearHighlight" :disabled="!isHighlightMode">
                                        {{ t('viewMarkdown.clearHighlight') }}
                                    </el-dropdown-item>
                                </el-dropdown-menu>
                            </template>
                        </el-dropdown>

                        <el-checkbox v-model="showNote" size="small" style="margin-left: auto;">
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
                        <MdCatalog :editorId="previewId" :scrollElement="'.md-editor-preview'" class="md-catalog" />
                    </div>
                    <div class="content-container" ref="content" @mouseup="handleMouseUp" @touchend="handleMouseUp"
                        @contextmenu.prevent">
                        <MdPreview :editorId="previewId" :modelValue="markdownContent" :previewTheme="'default'"
                            :preview-lazy="true" ref="mdPreview" style="height: 100%; padding: 0px;" />
                    </div>
                </div>
            </div>
            <div v-show="viewMode === 'content-note'" class="editor-container">
                <div class="editor-toolbar">
                    <el-button-group>
                        <el-button size="small" type="primary" @click="selectedToNote">{{
                            t('viewMarkdown.insertSelected') }}</el-button>
                        <!--
                        <el-button size="small" type="primary" @click="highlightToNote">{{
                            t('viewMarkdown.insertHighlight') }}</el-button>
                            -->
                        <el-button size="small" type="primary" @click="allToNote">{{ t('viewMarkdown.insertAll')
                        }}</el-button>
                        <el-button size="small" type="primary" @click="saveAsNote">{{ t('viewMarkdown.saveAsNote')
                        }}</el-button>
                    </el-button-group>
                </div>
                <ViewNote ref="viewNote" :form="form" />
            </div>
        </div>

        <TextSpeakPlayer :text="selectedText" :lang="getLocale()" :getContentCallback="getContent" ref="txtPlayer"
            @onSpeak="handleSpeak" />
        <AIDialog v-model="aiDialogVisible" 
            :full-content="markdownContent" 
            :selected-content="getSelectedContent()"
            :screen-content="getScreenContent()"
            :etype="etype"
            @insert-note="handleInsertAIAnswer" />
    </div>
</template>

<script setup>
import 'md-editor-v3/lib/preview.css';
import 'md-editor-v3/lib/style.css';
import '@/assets/styles/markdown-view.css'
import '@/assets/styles/markdown-preview.css'
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
import { Expand, Fold, ArrowDown } from '@element-plus/icons-vue'
import ViewNote from '@/components/manager/ViewNote.vue'
import { getSelectedNodeList, getVisibleNodeList, setHighlight } from './DOMUtils';
import AIDialog from '@/components/ai/AIDialog.vue'
import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn'

const { t } = useI18n()
const appName = 'ExMemo'
const markdownContent = ref(t('loading'))
const previewId = 'preview-content-' + Date.now()
const route = useRoute()
const content = ref(null)
const form = ref({})
const highlightManager = ref(null)
const showPlayer = ref(true)
const txtPlayer = ref(null)
const selectedText = ref('')
const mdPreview = ref(null)
const etype = "view"

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
        loadHighlight();
        setTimeout(() => {
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
    viewMode.value = 'content';
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
            if (txtPlayer.value) {
                txtPlayer.value.stop();
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
})

const handleBeforeUnload = async (e) => {
    if (highlightSaveTimer.value) {
        clearTimeout(highlightSaveTimer.value)
    }
    await saveMeta(true)
    e.preventDefault()
    e.returnValue = ''
}

const viewMode = computed(() => showNote.value ? 'content-note' : 'content')
const showNote = ref(false)

const saveMeta = async (force) => {
    if (!form.value.idx) return
    await nextTick();
    const mdPreviewContent = document.querySelector('.md-editor-preview');
    const scrollPosition = mdPreviewContent ? mdPreviewContent.scrollTop : 0;

    if (force == false && !highlightChanged.value) return

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

    const visibleHeight = preview.clientHeight
    const previewRect = preview.getBoundingClientRect()
    const walker = document.createTreeWalker(
        preview,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: (node) => {
                if (node.textContent?.trim() === '') {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    )

    let visibleText = ''
    let node
    while (node = walker.nextNode()) {
        const range = document.createRange()
        range.selectNodeContents(node)
        const rect = range.getBoundingClientRect()
        const elementTop = rect.top - previewRect.top
        const elementBottom = rect.bottom - previewRect.top

        if (elementTop >= 0 && elementTop <= visibleHeight && elementBottom >= 0) {
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
</script>

<style scoped>
/*为知为啥，只能写这里*/
:deep(.md-editor-preview) {
    height: auto;
    overflow-y: auto !important;
    padding: 10px 20px;
    max-width: 960px;
    margin: 0 auto;
}

:deep(.md-editor-preview-wrapper) {
    padding: 0px;
}

.catalog-control {
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    cursor: pointer;
    background: #409EFF;
    color: white;
    padding: 8px 4px;
    border-radius: 0 4px 4px 0;
}

.catalog-control .is-active {
    transform: rotate(180deg);
}

.catalog-container {
    width: 250px;
    flex-shrink: 0;
    /* 防止目录被压缩 */
    background: #f5f7fa;
    border-right: 1px solid #e6e6e6;
    height: 100%;
    overflow-y: auto;
    position: relative;
    z-index: 2;
}

.md-catalog {
    height: 100%;
    padding: 10px;
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

.preview-container-out {
    flex: 2;
    overflow: hidden;
    height: 100%;
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.preview-container {
    flex: 1;
    overflow: hidden;
    position: relative;
    height: 100%;
    min-width: 0;
    background-color: white;
    display: flex;
}

.content-container {
    flex: 1;
    overflow: hidden;
    position: relative;
    height: 100%;
    min-width: 0;
}

:deep(.el-dropdown-menu__item.is-active) {
    color: #409EFF;
    font-weight: bold;
}

.button-container-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}

.progress-text {
    color: #909399;
    font-size: 14px;
    width: 50px;
    margin-left: 10px;
    padding: 0 10px;
}

.title-container {
    display: flex;
    align-items: center;
    flex-grow: 1;
}

.nav-right {
    display: flex;
    align-items: center;
    flex-shrink: 1;
}

.top-row-view {
    display: flex;
    flex-direction: row;
}

</style>