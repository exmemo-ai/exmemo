import { saveEntry } from '../datatable/dataUtils';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'

const encodeSpecialChars = (str) => {
    return str.replace(/[ !@#$%^&*()+=[\]{};:,.<>?~\\]/g, (char) => {
        return encodeURIComponent(char);
    });
};

// 临时图片映射表
const tempImageMap = new Map();

// 生成唯一图片ID
const generateImageId = () => 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// 添加临时图片
export const addTempImage = (file) => {
    if (!(file instanceof Blob)) {
        console.error('Invalid file object');
        return null;
    }
    const imageId = generateImageId();
    const url = URL.createObjectURL(file);
    tempImageMap.set(imageId, { file, url, uploaded: false });
    return imageId;
};

// 获取临时图片URL
export const getTempImageUrl = (imageId) => tempImageMap.get(imageId)?.url || null;

// 上传所有未上传的临时图片
export const uploadPendingImages = async (content) => {
    const imageIds = Array.from(content.matchAll(/!\[.*?\]\((temp_[^)]+)\)/g))
        .map(match => match[1])
        .filter(id => tempImageMap.has(id));

    for (const imageId of imageIds) {
        const image = tempImageMap.get(imageId);
        if (!image.uploaded) {
            try {
                const form = { etype: 'note', ctype: 'image' };
                const path = image.file.name;
                const result = await saveEntry({
                    onSuccess: null,
                    form,
                    path,
                    file: image.file,
                    onProgress: null,
                    showMessage: false
                });

                if (result?.status === 'success' && result.list?.[0]) {
                    content = content.replace(
                        new RegExp(`!\\[.*?\\]\\(${imageId}\\)`, 'g'),
                        `![](${encodeSpecialChars(result.list[0])})`
                    );
                    image.uploaded = true;
                }
            } catch (error) {
                console.error('Failed to upload image:', error);
                throw error;
            }
        }
    }
    return content;
};

// 清理未使用的临时图片
export const cleanupTempImages = (content) => {
    const usedIds = Array.from(content.matchAll(/!\[.*?\]\((temp_[^)]+)\)/g)).map(match => match[1]);
    for (const [imageId, image] of tempImageMap) {
        if (!usedIds.includes(imageId)) {
            URL.revokeObjectURL(image.url);
            tempImageMap.delete(imageId);
        }
    }
};

// markdownIt 配置
export const getMarkdownItConfig = (md) => {
    const defaultImageRender = md.renderer.rules.image;
    md.renderer.rules.image = (tokens, idx, options, env, self) => {
        const token = tokens[idx];
        const srcIndex = token.attrIndex('src');
        if (srcIndex >= 0) {
            const src = token.attrs[srcIndex][1];
            if (src.startsWith('temp_')) {
                const tempUrl = getTempImageUrl(src);
                if (tempUrl) {
                    token.attrs[srcIndex][1] = tempUrl;
                    return defaultImageRender(tokens, idx, options, env, self);
                }
            }
            if (!src.startsWith('http://') && !src.startsWith('https://')) {
                token.attrs[srcIndex][1] = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
                handleImageLoad(src).then(newSrc => {
                    if (newSrc) {
                        document.querySelectorAll(`img[data-original-src="${src}"]`).forEach(img => {
                            img.src = newSrc;
                        });
                    }
                });
                const html = defaultImageRender(tokens, idx, options, env, self);
                return html.replace('<img', `<img data-original-src="${src}"`);
            }
        }
        return defaultImageRender(tokens, idx, options, env, self);
    };
};


export const handleImageLoad = async (src) => {
    if (!src) return src;
    
    if (src.startsWith('./') || src.startsWith('../')) { // later adjust
        console.log('Relative path detected:', src);
        return src;
    }
    
    if (!src.startsWith('http://') && !src.startsWith('https://')) {
        try {
            setDefaultAuthHeader();
            const response = await axios.get(getURL() + 'api/entry/tool/', {
                params: {
                    etype: 'note',
                    rtype: 'getimage',
                    addr: src
                }
            });
            
            if (response.data.status === 'success' && response.data.data_url) {
                return response.data.data_url;
            }
            return src;
        } catch (error) {
            console.error('Error loading image:', error);
            return src;
        }
    }    
    return src;
};


/*
export const handleImageUpload = async (files, callback) => {
    try {
        const imgUrls = [];
        for (const file of files) {
            const form = {
                etype: 'note',
                ctype: 'image' // later adjust
            };
            const path = file.webkitRelativePath || file.name; // later adjust
            const result = await saveEntry({
                onSuccess: null,
                form: form,
                path: path,
                file: file,
                onProgress: null,
                showMessage: false
            });

            if (result && result.status === 'success') {
                if (result.list) {
                    for (const item of result.list) {
                        const encodedItem = encodeSpecialChars(item);
                        imgUrls.push(encodedItem);
                    }
                }
            } else {
                throw new Error('upload failed');
            }
        }        
        callback(imgUrls);
        return true;
    } catch (error) {
        console.error('Upload failed:', error);
        ElMessage.error('Upload failed');
        return false;
    }
};
*/
