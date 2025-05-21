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
                        <el-button size="small" type="primary" circle @click="handleAI">
                            {{ t('viewMarkdown.ai') }}
                        </el-button>
                    </div>
                </div>
            </el-container>
        </div>
        <div class="main-content" :class="{ 'landscape': isLandscape }">
            <div class="editor-container">
                <MdEditor
                    ref="mdEditor"
                    v-model="markdownContent"
                    :showCodeRowNumber="true"
                    @onChange="handleContentChange"
                    @on-save="saveContent"
                    :toolbars="customToolbars"
                    preview-theme="github"
                    :showToolbar="true"
                    :preview="isLandscape ? true: false"
                    :scroll-auto="true"
                    :footers="['markdownTotal']"
                >
                    <template #defToolbars>
                        <NormalToolbar :title="t('saveAs')" @onClick="saveAs">
                            <template #trigger>
                                <el-icon><SaveAsIcon /></el-icon>
                            </template>
                        </NormalToolbar>
                        <NormalToolbar :title="t('img.insertImage')" @onClick="uploadImage">
                            <template #trigger>
                                <el-icon><Picture /></el-icon>
                            </template>
                        </NormalToolbar>
                    </template>
                </MdEditor>
            </div>
        </div>
        
        <div style="flex-shrink: 1">
            <TextSpeakPlayer
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
            :etype="etype"
            :default-reference-type="defaultReferenceType"
            @insert-note="handleInsertAIAnswer"
        />
        <AddDialog ref="addDialog" />
        <ImageProcessDialog ref="imageProcessRef" />
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
import { MdEditor, NormalToolbar, config } from 'md-editor-v3';
import { saveEntry, fetchItem, getDefaultPath, getDefaultVault } from '@/components/datatable/dataUtils';
import TextSpeakPlayer from '@/components/viewer/TextPlayer.vue';
import SaveAsIcon from '@/components/icons/SaveAsIcon.vue'
import { Picture } from '@element-plus/icons-vue';
import { useWindowSize } from '@vueuse/core';
import { getSelectedNodeList, getVisibleNodeList, setHighlight } from './DOMUtils';
import AIDialog from '@/components/ai/AIDialog.vue';
import AddDialog from '@/components/datatable/AddDialog.vue'
import { getMarkdownItConfig, uploadPendingImages, cleanupTempImages, addTempImage, resizeImageIfNeeded, handleSingleImage } from './imageUtils';
import ImageProcessDialog from '@/components/viewer/ImageProcessDialog.vue';

const { t } = useI18n();
const appName = 'ExMemo';
const markdownContent = ref('');
const route = useRoute();
const form = ref({});
const speakerPlayer = ref(null);
const selectedText = ref('');
const { width } = useWindowSize();
const isLandscape = computed(() => width.value >= 768);
const isContentModified = ref(false);
const mdEditor = ref(null);
const aiDialogVisible = ref(false);
const defaultReferenceType = ref('');
const addDialog = ref(null)
const etype = "editor"
const imageProcessRef = ref(null);

const currentFileName = computed(() => {
    if (form.value && form.value.title) {
        return form.value.addr.split('/').pop();
    }
    return '';
});

const customToolbars = computed(() => {
    const mobileToolbars = [
        'bold',
        'italic',
        'strikethrough',
        'title',
        'quote',
        'unorderedList',
        'orderedList',
        'task',
        1,
        '=',
        'previewOnly',
        'save',
        0,
    ];

    const desktopToolbars = [
        'bold',
        'italic',
        'strikethrough',
        '-',
        'title',
        'quote',
        'unorderedList',
        'orderedList',
        'task',
        '-',
        'codeRow',
        'code',
        'link',
        'table',
        'mermaid',
        'formula',
        1,
        '=',
        'revoke',
        'next',
        'catalog',
        'preview',
        'previewOnly',
        'htmlPreview',
        'save',
        0,
    ];

    return isLandscape.value ? desktopToolbars : mobileToolbars;
});

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
        //if (form.value.etype === 'note') {
        //    content = content.replace(/^---\n[\s\S]*?\n---\n/, '');
        //}
        markdownContent.value = content;
        isContentModified.value = false;
    } else {
        markdownContent.value = t('notSupport');
    }
}

const handleContentChange = () => {
    isContentModified.value = true;
}

const getCurrentPathInfo = () => {
    let vault = '';
    let path = '';
    if (!form.value.addr) {
        vault = getDefaultVault('note', null);
        path = getDefaultPath('note', null, null);
    } else {
        const parts = form.value.addr.split('/');
        vault = parts[0];
        path = parts.slice(1).join('/');
    }
    return { vault, path };
}

const saveAs = async () => {
    const { vault, path } = getCurrentPathInfo();
    const modifiedPath = path.replace(/(\.[^.]*)$/, '_copy$1');
    addDialog.value.openDialog(null, {
        etype: 'note',
        content: markdownContent.value,
        vault: vault,
        path: modifiedPath,
        atype: form.value.atype,
        ctype: form.value.ctype,
        status: form.value.status,
        title: t('saveAs')
    });
}

const saveContent = async () => {
    if (!form.value.idx) {
        await saveAs();
        return;
    }
    if (!isContentModified.value) {
        ElMessage.info(t('noChanges'));
        return;
    }

    try {
        const { vault } = getCurrentPathInfo();
        let finalContent = await uploadPendingImages(markdownContent.value, vault);
        const blob = new Blob([finalContent], { type: 'text/plain' });
        const file = new File([blob], 'temp.md', { type: 'text/plain' });
        const result = await saveEntry({
            form: form.value,
            path: form.value.addr,
            file: file,
            showMessage: false
        });
        if (result) {
            ElMessage.success(t('saveSuccess'));
            isContentModified.value = false;
            markdownContent.value = finalContent;
            cleanupTempImages(finalContent);
        }
    } catch (error) {
        console.error(t('saveFail'), error);
        ElMessage.error(t('saveFail'));
    }
}

const handleSpeak = (text, index, node) => {
    const previewElement = document.querySelector('.md-editor-preview')
    setHighlight(text, index, node, previewElement, scroll=false);
}

const getContent = () => {
    const previewElement = document.querySelector('.md-editor-preview')
    const selectedNodeList = getSelectedNodeList(previewElement);
    if (selectedNodeList.length > 0) {
        return selectedNodeList;
    }
    if (!previewElement || !previewElement.offsetParent) {
        ElMessage.warning(t('viewMarkdown.pleasePreview'));
        return [];
    }
    return getVisibleNodeList(previewElement);
}

const handleMouseUp = (event) => {
    const isPlaying = speakerPlayer.value?.getStatus().isPlaying || false
    if (isPlaying) {
        const selection = window.getSelection()
        const startNode = selection.anchorNode
        if (startNode && speakerPlayer.value) {
            const previewElement = document.querySelector('.md-editor-preview')
            const nodeList = getVisibleNodeList(previewElement, startNode)
            speakerPlayer.value.stop()
            speakerPlayer.value.setContent(nodeList)
            speakerPlayer.value.resume()
        }
    }
}

const handleAI = async () => {
    defaultReferenceType.value = 'all';
    nextTick(() => {
        aiDialogVisible.value = true;
    });
}

const htmlToMarkdown = (html) => {
    try {
        const div = document.createElement('div');
        div.innerHTML = html; 
        
        const processNode = (node) => {
            if (node.nodeType === 3) {
                return node.textContent;
            }
            
            let text = '';
            for (const child of node.childNodes) {
                text += processNode(child);
            }
            
            switch (node.nodeName.toLowerCase()) {
                case 'p':
                    return text + '\n\n';
                case 'br':
                    return '\n';
                case 'h1':
                    return `# ${text}\n\n`;
                case 'h2':
                    return `## ${text}\n\n`;
                case 'h3':
                    return `### ${text}\n\n`;
                case 'b':
                case 'strong':
                    return `**${text}**`;
                case 'i':
                case 'em':
                    return `*${text}*`;
                case 'pre':
                    return `\`\`\`\n${text}\n\`\`\`\n\n`;
                case 'code':
                    return `\`${text}\``;
                case 'ul':
                    return text + '\n';
                case 'ol':
                    return text + '\n';
                case 'li':
                    return `- ${text}\n`;
                case 'a':
                    const href = node.getAttribute('href');
                    return href ? `[${text}](${href})` : text;
                default:
                    return text;
            }
        };
        
        let markdown = processNode(div);        
        markdown = markdown.replace(/\n\s*\n\s*\n/g, '\n\n');
        return markdown.trim();
    } catch (error) {
        console.error('HTML to Markdown conversion failed:', error);
        return '';
    }
}

const setContentFromCB = async () => {
    if (!navigator?.clipboard) {
        ElMessage.warning(t('paste.notSupport'));
        return;
    }

    if (navigator.permissions) {
        const result = await navigator.permissions.query({ name: 'clipboard-read' });
        if (result.state === 'denied') {
            ElMessage.warning(t('paste.permissionDenied'));
            return;
        }
    }

    const clipboardData = await navigator.clipboard.read();
    let allContent = '';
    
    for (const item of clipboardData) {
        if (item.types.includes('text/html')) {
            const blob = await item.getType('text/html');
            const html = await blob.text();
            const markdown = htmlToMarkdown(html);
            if (markdown) {
                allContent += markdown + '\n\n';
            }
        } else if (item.types.includes('text/plain')) {
            const blob = await item.getType('text/plain');
            const text = await blob.text();
            if (text.length > 0) {
                allContent += text + '\n\n';
            }
        }
    }

    if (allContent) {
        ElMessage.info(t('paste.openClipboardContent'));
        form.value = {};
        markdownContent.value = allContent.trim();
        isContentModified.value = true;
    }
}

const handleExtractStyle = async () => {
    try {
        const clipboardData = await navigator.clipboard.read();
        for (const item of clipboardData) {
            if (item.types.includes('text/html')) {
                const blob = await item.getType('text/html');
                const html = await blob.text();
                
                // 创建一个临时的 DOM 元素来解析 HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;

                console.log(html)
                
                // 提取所有内联样式
                const elementsWithStyle = tempDiv.querySelectorAll('[style]');
                let styles = [];
                
                elementsWithStyle.forEach(element => {
                    styles.push(element.getAttribute('style'));
                });
                
                // 去重并格式化样式
                const uniqueStyles = [...new Set(styles)];
                const formattedStyles = uniqueStyles
                    .map(style => `样式: ${style}`)
                    .join('\n');
                
                // 插入到编辑器
                if (mdEditor.value && formattedStyles) {
                    mdEditor.value.insert(() => {
                        return {
                            targetValue: '\n提取的样式：\n```css\n' + formattedStyles + '\n```\n',
                            select: true,
                            deviationStart: 0,
                            deviationEnd: 0
                        };
                    });
                    isContentModified.value = true;
                    ElMessage.success('样式提取成功');
                } else {
                    ElMessage.info('未发现样式');
                }
                return;
            }
        }
        ElMessage.warning('剪贴板中没有富文本内容');
    } catch (error) {
        console.error('读取剪贴板失败:', error);
        ElMessage.error('读取剪贴板失败: ' + error.message);
    }
};

const getSelectedContent = () => {
    const selection = window.getSelection();
    return selection.toString();
}

const getScreenContent = () => {
    const previewElement = document.querySelector('.md-editor-preview')
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

const handleResize = () => {
    const visualHeight = window.innerHeight;
    console.log('visualHeight', visualHeight);
    document.documentElement.style.setProperty('--mainHeight', `${visualHeight}px`);
}

const handleImageChange = async (files, callback) => {
    if (files.length === 0) {
        callback([]);
        return;
    } else if (files.length > 1) {
        for (const file of files) {
            if (file instanceof Blob) {
                const resizedFile = await resizeImageIfNeeded(file);
                const imageId = addTempImage(resizedFile);
                if (imageId) {
                    callback([imageId]);
                    isContentModified.value = true;
                }
            }
        }
        return;
    }
    callback([]);

    const file = files[0];
    const result = await handleSingleImage(file, imageProcessRef.value, addTempImage);
    
    if (result.type === 'image') {
        callback([result.imageId]);
        isContentModified.value = true;
    } else if (result.type === 'text') {
        if (result.text.length > 0 && mdEditor.value) {
            mdEditor.value?.insert(() => {
                return {
                    targetValue: result.text + '\n\n',
                    select: true,
                    deviationStart: 0,
                    deviationEnd: 0
                };
            });
            isContentModified.value = true;
        }
    } else if (result.error) {
        const errorMessages = {
            'processing_failed': t('image.processingFailed'),
            'invalid_format': t('image.invalidFileFormat'),
            'unknown_error': t('uploadFail'),
            'failed_to_add_temp_image': t('uploadFail')
        };
        ElMessage.error(errorMessages[result.error] || t('uploadFail'));
    }
};

const uploadImage = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    
    input.onchange = (event) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            handleImageChange(Array.from(files), (urls) => {
                if (urls && urls.length > 0) {
                    mdEditor.value?.insert(() => {
                        return {
                            targetValue: `![image](${urls[0]})\n`,
                            select: false,
                            deviationStart: 0,
                            deviationEnd: 0
                        };
                    });
                }
            });
        }
    };
    input.click();
};

config({
    markdownItConfig: getMarkdownItConfig
});


onBeforeUnmount(() => {
    if (speakerPlayer.value) {
        speakerPlayer.value.stop();
    }
    window.removeEventListener('resize', handleResize);    
})

onMounted(() => {
    if (route.query.idx) {
        fetchContent(route.query.idx)
    } else {
        setContentFromCB()
    }
    window.addEventListener('resize', handleResize);
    handleResize();
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

.main-content {
    flex: 1;
    overflow: hidden;
    width: 100%;
    height: 100%;
}

.editor-container {
    width: 100%;
    height: 100%;
    transition: all 0.3s ease;
}

:deep(.md-editor) {
    height: 100%;
}

:deep(.md-editor-container) {
    transition: width 0.3s ease;
}

:deep(.md-editor-preview) {
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

.title-container {
    display: flex;
    align-items: center;
    flex-grow: 1;
    min-width: 0;
}

.nav-right {
    display: flex;
    align-items: center;
    flex-shrink: 1;
}

.top-row-view {
    display: flex;
    flex-direction: row;
    width: 100%;
}

.filename-container {
    margin-left: 10px;
    color: #666;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
