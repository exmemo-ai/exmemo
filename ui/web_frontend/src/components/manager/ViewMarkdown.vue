<template>
    <el-container class="app-container">
        <el-header :class="{ 'scroll-header': !isPortrait, 'fixed-header': isPortrait }" height="auto">
            <el-container class="navbar-container nav-container">
                <div class="top-row-view">
                    <div class="title-container">
                        <img :src="logo" class="nav-avatar" />
                        <h3 class="title">{{ appName }}</h3>
                    </div>
                </div>
                <div>
                    <div class="user-controls" style="margin-bottom: 5px">
                        <div :class="{ 'mobile-buttons': isPortrait }" class="button-container-flex">
                            <el-button-group class="basic-buttons" style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="selectAll">{{ t('selectAll') }}</el-button>
                                <el-button size="small" type="primary" @click="copyContent">{{ t('copySelected') }}</el-button>
                                <el-button size="small" type="primary" @click="readContent">
                                    {{ isSpeaking ? t('stopSpeak') : t('viewMarkdown.readSelected') }}
                                </el-button>
                                <el-button size="small" type="primary" v-if="form.etype === 'web'" @click="openWeb">{{ t('viewMarkdown.openWeb') }}</el-button>
                                <el-button size="small" type="primary" v-if="form.etype === 'file'" @click="download">{{ t('viewMarkdown.downloadFile') }}</el-button>
                            </el-button-group>
                            <el-button-group class="highlight-buttons" style="margin-right: 5px;">
                                <el-button size="small" type="primary" @click="highlightText">
                                    {{ isHighlightMode ? t('viewMarkdown.stopHighlight') : t('viewMarkdown.startHighlight') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="clearHighlight" :disabled="!isHighlightMode">
                                    {{ t('viewMarkdown.clearHighlight') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="copyHighlight" :disabled="!isHighlightMode">
                                    {{ t('viewMarkdown.copyHighlight') }}
                                </el-button>
                                <el-button size="small" type="primary" @click="saveHighLight" :disabled="!isHighlightMode || savedRanges.value?.length === 0">
                                    {{ t('viewMarkdown.saveHighlight') }}
                                </el-button>
                            </el-button-group>
                        </div>
                    </div>
                </div>
            </el-container>
        </el-header>
        <div class="preview-container" ref="content" @mouseup="highlightSelection" @touchend="highlightSelection" @contextmenu.prevent>
            <MdPreview :id="previewId" :modelValue="markdownContent" />
        </div>
    </el-container>
</template>

<script setup>
import 'md-editor-v3/lib/preview.css'
import axios from 'axios';
import logo from '@/assets/images/logo.png'
import { setDefaultAuthHeader,getURL } from '@/components/support/conn'
import { getLocale } from '@/main.js' 
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { MdPreview } from 'md-editor-v3'
import { saveEntry, downloadFile } from './dataUtils';

const { t } = useI18n()
const isPortrait = ref(false)
const appName = 'ExMemo'
const markdownContent = ref(t('loading'))
const previewId = 'preview-content'
const route = useRoute()
const isSpeaking = ref(false)
const isHighlightMode = ref(false)
let speechUtterance = null
const content = ref(null)
const savedRanges = ref([])
const form = ref({})

const handleResize = () => {
    isPortrait.value = window.innerHeight > window.innerWidth
}

const clearHighlight = () => {
    const highlightedTexts = document.querySelectorAll('.custom-highlight')
    highlightedTexts.forEach(text => {
        const parent = text.parentNode
        parent.replaceChild(document.createTextNode(text.textContent), text)
    })
    savedRanges.value = []
}

const copyHighlight = () => {
    const highlightedTexts = document.querySelectorAll('.custom-highlight')
    let text = Array.from(highlightedTexts).map(text => text.textContent).join('\n')
    text = text + "\n"
    text = text + "\n" + t('title') + ": " + form.value.title
    text = text + "\n" + t('viewMarkdown.detail') + ": " + window.location.href
    text = text + "\n" + t('viewMarkdown.copiedFrom') + ": " + form.value.addr
    text = text + "\n" + t('viewMarkdown.copiedAt') + ": " + new Date().toLocaleString()
    text = text.trim()

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => {
                ElMessage.success(t('copySuccess'))
            })
            .catch(() => {
                fallbackCopyTextToClipboard(text)
            })
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
    axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/')
        .then(response => {
            //console.log('response:', response.data);
            form.value = { ...response.data };
            if ('content' in response.data && response.data.content !== null) {
                markdownContent.value = response.data.content;
            } else {
                markdownContent.value = t('notSupport');
            }
        });
}

const loadHighlight = () => {
    if (form.value.meta) {
        if (typeof form.value.meta === 'string') {
            try {
                form.value.meta = JSON.parse(form.value.meta);
            } catch (error) {
                console.error('Failed to parse meta:', error);
                form.value.meta = {};
            }
        }
        if (form.value.meta.highlights) {
            try {
                const highlights = form.value.meta.highlights;
                savedRanges.value = highlights;
                applyHighlights(highlights);
            } catch (error) {
                console.error('Failed to parse highlights:', error);
            }
        }
    }
}

const applyHighlights = (highlights) => {
    if (!highlights || !highlights.length) 
        return;

    clearHighlight();
    if (typeof highlights === 'string') {
        highlights = JSON.parse(highlights);
    }
    highlights.forEach(highlight => {
        findAndHighlightText(highlight.text);
    });
}

const findAndHighlightText = (text) => {
    const container = content.value;
    if (!container) return;

    const textNodes = getTextNodes(container);
    const searchText = text.trim();

    for (const node of textNodes) {
        const nodeText = node.textContent;
        const index = nodeText.indexOf(searchText);
        
        if (index >= 0) {
            const range = document.createRange();
            const mark = document.createElement('mark');
            mark.className = 'custom-highlight';
            
            range.setStart(node, index);
            range.setEnd(node, index + searchText.length);
            
            const selectedText = range.extractContents();
            mark.appendChild(selectedText);
            range.insertNode(mark);            
            break;
        }
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

const readContent = () => {
    if (isSpeaking.value) {
        window.speechSynthesis.cancel()
        isSpeaking.value = false
        return
    }

    try {
        const selection = window.getSelection()
        const text = selection.toString().trim()
        const contentToRead = text

        if (!contentToRead) {
            ElMessage.warning(t('viewMarkdown.noTextSelected'))
            return
        }

        speechUtterance = new SpeechSynthesisUtterance(contentToRead)
        speechUtterance.lang = getLocale()
        
        speechUtterance.onend = () => {
            isSpeaking.value = false
        }
        speechUtterance.onerror = () => {
            isSpeaking.value = false
            console.error('TTS error:', speechUtterance)
        }
        console.log('speak', speechUtterance)
        window.speechSynthesis.speak(speechUtterance)
        isSpeaking.value = true
    } catch (error) {
        console.error('TTS error:', error)
        ElMessage.error(t('speakError') + error)
        isSpeaking.value = false
    }
}

watch(isHighlightMode, (newValue) => {
    if (content.value) {
        content.value.setAttribute('data-highlight-mode', newValue)
        
        const highlights = content.value.getElementsByClassName('custom-highlight')
        Array.from(highlights).forEach(el => {
            el.style.backgroundColor = newValue ? 'yellow' : 'transparent'
        })
    }
})

const highlightText = () => {
    isHighlightMode.value = !isHighlightMode.value
    ElMessage.success(isHighlightMode.value ? t('viewMarkdown.highlightModeOn') : t('viewMarkdown.highlightModeOff'))
    if (isHighlightMode.value) {
        loadHighlight();
    }
}

const highlightSelection = () => {
    if (!isHighlightMode.value) return

    const selection = window.getSelection()
    if (!selection.rangeCount) return

    try {
        const range = selection.getRangeAt(0)
        const selectedText = range.toString()
        if (!selectedText.trim()) return

        savedRanges.value.push({
            text: selectedText,
            startOffset: range.startOffset,
            endOffset: range.endOffset,
            startContainer: range.startContainer.textContent,
            timestamp: new Date().getTime()
        })

        const markElement = range.commonAncestorContainer.parentElement
        if (markElement && markElement.classList.contains('custom-highlight')) {
            const textContent = markElement.textContent
            const textNode = document.createTextNode(textContent)
            markElement.parentNode.replaceChild(textNode, markElement)
            selection.removeAllRanges()
            return
        } else {
            const startContainer = range.startContainer;
            const endContainer = range.endContainer;

            if (startContainer === endContainer && startContainer.nodeType === Node.TEXT_NODE) {
                // Single text node selection
                const mark = document.createElement('mark');
                mark.className = 'custom-highlight';
                
                // Split text into three parts: before selection, selection, and after selection
                const beforeText = startContainer.textContent.substring(0, range.startOffset);
                const selectedText = startContainer.textContent.substring(range.startOffset, range.endOffset);
                const afterText = startContainer.textContent.substring(range.endOffset);
                
                // Create text nodes
                const beforeNode = document.createTextNode(beforeText);
                mark.appendChild(document.createTextNode(selectedText));
                const afterNode = document.createTextNode(afterText);
                
                // Replace the original node with three new nodes
                const parent = startContainer.parentNode;
                parent.insertBefore(beforeNode, startContainer);
                parent.insertBefore(mark, startContainer);
                parent.insertBefore(afterNode, startContainer);
                parent.removeChild(startContainer);
            } else {
                // Multiple nodes selection
                const textNodes = getTextNodes(range.commonAncestorContainer);
                const nodesToHighlight = textNodes.filter(node => range.intersectsNode(node));

                nodesToHighlight.forEach(node => {
                    const mark = document.createElement('mark');
                    mark.className = 'custom-highlight';
                    
                    if (node === startContainer) {
                        // First node - split from start
                        const newNode = node.splitText(range.startOffset);
                        mark.appendChild(document.createTextNode(newNode.textContent));
                        newNode.parentNode.replaceChild(mark, newNode);
                    } else if (node === endContainer) {
                        // Last node - split until end
                        const text = node.textContent.substring(0, range.endOffset);
                        node.textContent = node.textContent.substring(range.endOffset);
                        mark.appendChild(document.createTextNode(text));
                        node.parentNode.insertBefore(mark, node);
                    } else {
                        // Middle nodes - highlight completely
                        mark.appendChild(document.createTextNode(node.textContent));
                        node.parentNode.replaceChild(mark, node);
                    }
                });
            }
        }
        selection.removeAllRanges()
        console.log('highlight success. Saved ranges:', savedRanges.value)
    } catch (error) {
        console.error('highlight failed:', error)
    }
}

const getTextNodes = (node) => {
    let textNodes = []
    if (node.nodeType === Node.TEXT_NODE) {
        textNodes.push(node)
    } else {
        node.childNodes.forEach(child => {
            textNodes = textNodes.concat(getTextNodes(child))
        })
    }
    return textNodes
}

const saveHighLight = async () => {
    if (savedRanges.value.length === 0) {
        ElMessage.warning(t('noHighlightToSave'))
        return
    }
    
    const serializableHighlights = savedRanges.value.map(range => ({
        text: range.text,
        timestamp: range.timestamp,
        startOffset: range.startOffset,
        endOffset: range.endOffset
    }))
    
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
    form.value.meta.highlights = JSON.stringify(serializableHighlights);
    try {
        const result = await saveEntry({
            parentObj: null,
            form: form.value,
            file: null,
            onProgress: null
        })
        
        if (result) {
            console.log('saveHighlightSuccess')
        }
    } catch (error) {
        console.error(t('saveHighlightFail'), error)
        ElMessage.error(t('saveHighlightFail'))
    }
}

onMounted(() => {
    handleResize()
    window.addEventListener('resize', handleResize)
    fetchContent(route.query.idx)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    if (isSpeaking.value) {
        window.speechSynthesis.cancel()
    }
})
</script>

<style scoped>
.app-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.fixed-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: white;
    padding: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.scroll-header {
    position: relative;
    background-color: white;
    padding: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@media (orientation: portrait) {
    .preview-container {
        margin-top: 130px;
    }
}

.preview-container {
    padding: 0px;
    height: auto;    
    border: 1px solid #dcdfe6;
    background-color: white;
}

.preview-container :deep(mark.custom-highlight) {
    padding: 2px;
    transition: background-color 0.3s;
}

.preview-container[data-highlight-mode="true"] :deep(mark.custom-highlight) {
    background-color: yellow !important;
}

.preview-container[data-highlight-mode="false"] :deep(mark.custom-highlight) {
    background-color: transparent !important;
}

.scrollable-content {
    flex: 1;
    overflow-y: auto;
}

.editor-container {
    height: calc(100vh - 140px);
    border: 1px solid #dcdfe6;
    border-radius: 4px;
}

.editor-header, .preview-header {
    padding: 10px;
    background-color: #f5f7fa;
    border-bottom: 1px solid #dcdfe6;
}

.markdown-body {
    padding: 20px;
    height: calc(100% - 41px);
    overflow-y: auto;
}

.button-container {
    margin-top: 20px;
    text-align: right;
}

:deep(.el-textarea__inner) {
    height: calc(100% - 41px) !important;
    font-family: monospace;
}

.full-width {
    width: 100%;
}

.desktop-width {
    max-width: 100%;
    margin: 0 auto;
}

.button-group {
    margin-bottom: 10px;
    padding: 10px;
    background-color: #f5f7fa;
    border-radius: 4px;
}

.highlighted {
    background-color: yellow;
}

.top-row-view {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}
</style>
