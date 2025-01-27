<template>
    <el-container class="app-container">
        <el-header :class="{ 'scroll-header': !isPortrait, 'fixed-header': isPortrait }" height="auto" style="padding: 0;">
            <el-container class="nav-container">
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
                                <el-button size="small" type="primary" v-if="form.etype === 'web'" @click="openWeb">{{ t('viewMarkdown.openWeb') }}</el-button>
                                <el-button size="small" type="primary" v-if="form.etype === 'file'" @click="download">{{ t('viewMarkdown.downloadFile') }}</el-button>
                                <el-button size="small" type="primary" @click="setPlayer">
                                    {{ showPlayer ? t('viewMarkdown.hideRead') : t('viewMarkdown.showRead') }}
                                </el-button>
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
        <div class="preview-container" ref="content" @mouseup="handleMouseUp" @touchend="handleMouseUp" @contextmenu.prevent>
            <MdPreview :id="previewId" :modelValue="markdownContent" ref="mdPreview" />
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
import 'md-editor-v3/lib/preview.css'
import axios from 'axios';
import logo from '@/assets/images/logo.png'
import { setDefaultAuthHeader,getURL } from '@/components/support/conn'
import { getLocale } from '@/main.js' 
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ref, onMounted, onBeforeUnmount, computed, nextTick, markRaw } from 'vue'
import { MdPreview } from 'md-editor-v3'
import { saveEntry, downloadFile } from './dataUtils';
import { HighlightManager } from '@/components/manager/HighlightManager'
import '@/assets/styles/markdown-view.css'
import TextSpeakerPlayer from '@/components/manager/TextPlayer.vue'

const { t } = useI18n()
const isPortrait = ref(false)
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

const currentHighlight = ref(null)

const handleResize = () => {
    isPortrait.value = window.innerHeight > window.innerWidth
}

const clearHighlight = () => {
    highlightManager.value?.clearHighlight()
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
const savedRanges = computed(() => highlightManager.value?.savedRanges || [])

const highlightText = () => {
    if (!highlightManager.value) return
    
    const newMode = highlightManager.value.toggleHighlightMode()
    ElMessage.success(newMode ? t('viewMarkdown.highlightModeOn') : t('viewMarkdown.highlightModeOff'))
    if (newMode) {
        loadHighlight()
    }
}

const highlightSelection = () => {
    highlightManager.value?.handleSelection()
}

const saveHighLight = async () => {
    if (!highlightManager.value?.hasHighlights()) {
        ElMessage.warning(t('noHighlightToSave'))
        return
    }

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
    
    const serializableHighlights = highlightManager.value.getSerializableHighlights()
    form.value.meta.highlights = JSON.stringify(serializableHighlights)

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

const handleMouseUp = (event) => {
    highlightSelection()
}

const getContent = () => {
    const selection = window.getSelection()
    const text = selection.toString().trim()
    const previewElement = document.getElementById(previewId)
    
    if (text && text.length > 0 && previewElement) {
        const range = selection.getRangeAt(0)
        const walker = document.createTreeWalker(
            previewElement,
            NodeFilter.SHOW_TEXT,
            null
        )
        
        let node
        let found = false
        let content = ''
        while (node = walker.nextNode()) { // collect from select start
            if (node === range.startContainer || found) {
                if (!found) {
                    content += node.textContent.substring(range.startOffset)
                } else {
                    content += node.textContent
                }
                found = true
            }
        }
        return content
    }    

    // 当没有选中文本时，从当前可视区域开始读取
    if (previewElement) {
        const viewportTop = window.scrollY
        const viewportBottom = viewportTop + window.innerHeight
        const walker = document.createTreeWalker(
            previewElement,
            NodeFilter.SHOW_TEXT,
            null
        )
        
        let node
        let content = ''
        let foundVisible = false
        
        while (node = walker.nextNode()) {
            const range = document.createRange()
            range.selectNode(node)
            const rect = range.getBoundingClientRect()
            
            const absoluteTop = rect.top + window.scrollY
            const absoluteBottom = rect.bottom + window.scrollY
            
            if (!foundVisible) {
                const isVisible = (absoluteTop < viewportBottom) && 
                                (absoluteBottom > viewportTop) && 
                                rect.height > 0 &&
                                getComputedStyle(node.parentElement).display !== 'none'
                
                if (isVisible) {
                    foundVisible = true
                }
            }
            
            if (foundVisible) {
                content += node.textContent
            }
        }
        return content.trim()
    }
    return ''
}

const handleSpeak = (text, index) => {
    if (currentHighlight.value) {
        currentHighlight.value.style.backgroundColor = ''
    }

    if (index == -1) {
        return;
    }

    // 如果有完全重复的内容可能有问题，但是这里先不处理
    const previewElement = document.getElementById(previewId)
    if (previewElement) {
        const walker = document.createTreeWalker(
            previewElement,
            NodeFilter.SHOW_TEXT,
            null
        )

        let node
        while (node = walker.nextNode()) {
            const index = node.textContent.indexOf(text)
            if (index !== -1) {
                if (node.parentElement) {
                    node.parentElement.style.backgroundColor = '#fffacd'
                    currentHighlight.value = node.parentElement
                    node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                }
                break
            }
        }
    }
}

onBeforeUnmount(() => {
    if (currentHighlight.value) {
        currentHighlight.value.style.backgroundColor = ''
    }
})

onMounted(() => {
    handleResize()
    window.addEventListener('resize', handleResize)
    fetchContent(route.query.idx)
    highlightManager.value = new HighlightManager(content.value)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.preview-container {
    margin-bottom: 80px;
}

.player-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
    padding: 0px;
    z-index: 1000;
}
</style>
