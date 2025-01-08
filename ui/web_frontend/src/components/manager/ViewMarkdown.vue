<template>
    <div :class="{ 'full-width': isMobile, 'desktop-width': !isMobile }">
        <div style="display: flex; flex-direction: column;">
            <app-navbar :title="t('dataOperate')" :info="'DataOperate'" />
        </div>
        <el-main class="main-container">
            <div class="button-group">
                <el-button-group>
                    <el-button type="primary" @click="selectAll">{{ t('selectAll') }}</el-button>
                    <el-button type="primary" @click="copyContent">{{ t('copySelected') }}</el-button>
                    <el-button type="primary" @click="readContent">
                        {{ isSpeaking ? t('stopSpeak') : t('read') }}
                    </el-button>
                    <el-button type="primary" @click="highlightText">
                        {{ isHighlightMode ? t('stopHighlight') : t('startHighlight') }}
                    </el-button>
                    <!--
                    <el-button type="primary" @click="saveHighlight" :disabled="!isHighlightMode">
                        {{ t('save') }}
                    </el-button>
                    -->
                    <el-button type="primary" @click="clearHighlight" :disabled="!isHighlightMode">
                        {{ t('clearHighlight') }}
                    </el-button>
                    <el-button type="primary" @click="copyHighlight" :disabled="!isHighlightMode">
                        {{ t('copyHighlight') }}
                    </el-button>
                </el-button-group>
            </div>

            <el-row :gutter="20">
                <el-col :span="24">
                    <div class="preview-container" ref="content" @mouseup="highlightSelection">
                        <MdPreview :id="previewId" :modelValue="markdownContent" />
                        <!--<MdCatalog :editorId="previewId" :scrollElement="scrollElement" />-->
                    </div>
                </el-col>
            </el-row>
        </el-main>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import axios from 'axios';
import { getURL } from '@/components/support/conn'
import AppNavbar from '@/components/support/AppNavbar.vue'
import { getLocale } from '@/main.js' 
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const { t, locale } = useI18n()
const isMobile = ref(false)
const markdownContent = ref('## title\n\ncontent')
const previewId = 'preview-content'
const route = useRoute()
const isSpeaking = ref(false)
const isHighlightMode = ref(false)
let speechUtterance = null
const content = ref(null)

const handleResize = () => {
    isMobile.value = window.innerWidth < 768
}

const clearHighlight = () => {
    const highlightedTexts = document.querySelectorAll('.custom-highlight')
    highlightedTexts.forEach(text => {
        const parent = text.parentNode
        parent.replaceChild(document.createTextNode(text.textContent), text)
    })
}

const copyHighlight = () => {
    const highlightedTexts = document.querySelectorAll('.custom-highlight')
    const text = Array.from(highlightedTexts).map(text => text.textContent).join('\n')
    navigator.clipboard.writeText(text)
        .then(() => {
            ElMessage.success(t('copySuccess'))
        })
        .catch(() => {
            ElMessage.error(t('copyFailed'))
        })
}

const fetchContent = async (idx) => {
    let table_name = 'data'
            axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/')
                .then(response => {
                    console.log('@@@@', response);
                    if ('content' in response.data && response.data.content !== null) {
                        markdownContent.value = response.data.content;
                    } else {
                        markdownContent.value = t('notSupport');
                    }
                });
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
    navigator.clipboard.writeText(markdownContent.value)
        .then(() => {
            ElMessage.success(t('copySuccess'));
        })
        .catch(() => {
            ElMessage.error(t('copyFailed'));
        });
}

const readContent = () => {
    if (isSpeaking.value) {
        window.speechSynthesis.cancel()
        isSpeaking.value = false
        return
    }

    try {
        speechUtterance = new SpeechSynthesisUtterance(markdownContent.value)
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

// 监听高亮模式变化
watch(isHighlightMode, (newValue) => {
    if (content.value) {
        // 给预览容器添加自定义属性
        content.value.setAttribute('data-highlight-mode', newValue)
        
        // 强制更新所有高亮元素的样式
        const highlights = content.value.getElementsByClassName('custom-highlight')
        Array.from(highlights).forEach(el => {
            el.style.backgroundColor = newValue ? 'yellow' : 'transparent'
        })
    }
})

const highlightText = () => {
    isHighlightMode.value = !isHighlightMode.value
    ElMessage.success(isHighlightMode.value ? t('highlightModeOn') : t('highlightModeOff'))
}

const highlightSelection = () => {
    if (!isHighlightMode.value) return

    const selection = window.getSelection()
    if (!selection.rangeCount) return

    try {
        const range = selection.getRangeAt(0)
        const selectedText = range.toString()
        if (!selectedText.trim()) return

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
        console.log('highlight success')
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

onMounted(() => {
    handleResize()
    window.addEventListener('resize', handleResize)
    console.log('查询参数:', route.query.idx)
    fetchContent(route.query.idx)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    if (isSpeaking.value) {
        window.speechSynthesis.cancel()
    }
})
</script>

<style>
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

<style scoped>
.main-container {
    padding: 20px;
    height: calc(100vh - 60px);
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
    max-width: 1200px;
    margin: 0 auto;
}

.button-group {
    margin-bottom: 10px;
    padding: 10px;
    background-color: #f5f7fa;
    border-radius: 4px;
}

.preview-container {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 10px;
}

.highlighted {
    background-color: yellow;
}

@media (max-width: 767px) {
    .el-row {
        display: flex;
        flex-direction: column;
    }
    
    .el-col {
        width: 100% !important;
    }

    .editor-container {
        height: calc(100vh - 160px);
    }
}
</style>
