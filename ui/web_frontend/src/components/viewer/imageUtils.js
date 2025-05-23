import { saveEntry } from '../datatable/dataUtils';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'
import SettingService from '@/components/settings/settingService'

const IMAGE_PREFIX = 'Pasted_image_'

const encodeSpecialChars = (str) => {
    return str.replace(/[ !@#$%^&*()+=[\]{};:,.<>?~\\]/g, (char) => {
        return encodeURIComponent(char);
    });
};

const getImagePattern = (image_storage_location, fullPath = true) => {
    const imagePath = fullPath ? `${image_storage_location}/${IMAGE_PREFIX}` : IMAGE_PREFIX;
    return `!\\[.*?\\]\\((${imagePath}[^)]+)\\)`;
};

class TempImageManager {
    constructor() {
        this.imageMap = new Map();
        this.initialize();
    }

    async initialize() {
        const settingService = SettingService.getInstance();
        await settingService.loadSetting();
        this.image_storage_location = settingService.getSetting('image_storage_location', 'attachments');
    }

    getPrefix(fullPath = true) {
        if (fullPath) {
            return `${this.image_storage_location}/${IMAGE_PREFIX}`;
        }
        return IMAGE_PREFIX;
    }

    generateImageId(extension = '') {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const milliseconds = String(now.getMilliseconds()).padStart(3, '0');
        return this.getPrefix() + `${year}${month}${day}${hours}${minutes}${seconds}${milliseconds}${extension}`;
    }

    addTempImage(file) {
        if (!(file instanceof Blob)) {
            console.error('Invalid file object');
            return null;
        }
        const extension = file.name ? `.${file.name.split('.').pop()}` : '';
        const imageId = this.generateImageId(extension);
        const url = URL.createObjectURL(file);
        this.imageMap.set(imageId, { file, url, uploaded: false });
        return imageId;
    }

    getTempImageUrl(imageId) {
        return this.imageMap.get(imageId)?.url || null;
    }

    async uploadPendingImages(content, vault) {
        const imageIds = Array.from(content.matchAll(new RegExp(getImagePattern(this.image_storage_location), 'g')))
            .map(match => match[1])
            .filter(id => this.imageMap.has(id));

        for (const imageId of imageIds) {
            const image = this.imageMap.get(imageId);
            if (!image.uploaded) {
                try {
                    const form = { etype: 'note', vault: vault };
                    const path = imageId;
                    //console.log('Uploading image:', image.file, 'to path:', path);
                    const result = await saveEntry({
                        form,
                        path,
                        file: image.file,
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
    }

    cleanupTempImages(content) {
        const usedIds = Array.from(content.matchAll(new RegExp(getImagePattern(this.image_storage_location), 'g')))
            .map(match => match[1]);
        for (const [imageId, image] of this.imageMap) {
            if (!usedIds.includes(imageId)) {
                URL.revokeObjectURL(image.url);
                this.imageMap.delete(imageId);
            }
        }
    }
}

const tempImageManager = new TempImageManager();

export const addTempImage = (file) => tempImageManager.addTempImage(file);
export const getTempImageUrl = (imageId) => tempImageManager.getTempImageUrl(imageId);
export const uploadPendingImages = (content, vault) => tempImageManager.uploadPendingImages(content, vault);
export const cleanupTempImages = (content) => tempImageManager.cleanupTempImages(content);

export const getMarkdownItConfig = (md) => {
    const defaultImageRender = md.renderer.rules.image;
    md.renderer.rules.image = (tokens, idx, options, env, self) => {
        const token = tokens[idx];
        const srcIndex = token.attrIndex('src');
        if (srcIndex >= 0) {
            const src = token.attrs[srcIndex][1];
            if (src.startsWith(tempImageManager.getPrefix())) {
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
    
    if (src.startsWith('./') || src.startsWith('../')) {
        console.log('Relative path detected:', src);
        return src;
    }
    
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
        parseBackendError(error);
        return src;
    }
};

export const resizeImageIfNeeded = (file, max_size=1024) => {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                let width = img.width;
                let height = img.height;
                let needResize = false;
                
                if (width > max_size || height > max_size) {
                    needResize = true;
                    if (width > height) {
                        height = Math.round(height * (max_size / width));
                        width = max_size;
                    } else {
                        width = Math.round(width * (max_size / height));
                        height = max_size;
                    }
                }
                
                if (!needResize) {
                    resolve(file);
                    return;
                }
                
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob((blob) => {
                    if (file.name) {
                        Object.defineProperty(blob, 'name', {
                            value: file.name,
                            writable: false
                        });
                    }
                    resolve(blob);
                }, file.type || 'image/jpeg', 0.4);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
};

export const handleSingleImage = async (file, imageProcessRef, addTempImageCallback) => {
    if (!file || !(file instanceof Blob)) {
        console.error('Invalid file object');
        return null;
    }

    const resizedFile = await resizeImageIfNeeded(file, 1600);
    const url = URL.createObjectURL(resizedFile);
    
    const processed = await new Promise(resolve => {
        imageProcessRef.open(url, async (result) => {
            resolve(result);
        });
    });

    let result = { type: 'none', error: null };

    if (processed?.file) {
        let processedFile = processed.file;
        
        if (typeof processedFile === 'string' && processedFile.startsWith('data:')) {
            try {
                const base64Data = processedFile.split(',')[1];
                const binaryStr = atob(base64Data);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }
                
                const originalName = file.name;
                const lastDotIndex = originalName.lastIndexOf('.');
                const nameWithoutExt = lastDotIndex !== -1 ? originalName.slice(0, lastDotIndex) : originalName;
                const extension = lastDotIndex !== -1 ? originalName.slice(lastDotIndex) : '.png';
                const newFileName = `${nameWithoutExt}_edit${extension}`;
                
                const mimeType = processedFile.split(';')[0].split(':')[1];
                processedFile = new Blob([bytes], { type: mimeType || 'image/png' });
                Object.defineProperty(processedFile, 'name', {
                    value: newFileName,
                    writable: false
                });
            } catch (e) {
                console.error('Failed to convert base64 to Blob:', e);
                return { error: 'processing_failed' };
            }
        } else if (!(processedFile instanceof Blob)) {
            console.error('Invalid processed file type:', typeof processedFile);
            return { error: 'invalid_format' };
        }
        
        const finalResizedFile = await resizeImageIfNeeded(processedFile, 1024);
        const imageId = addTempImage(finalResizedFile);
        if (imageId) {
            result.type = 'image';
            result.imageId = imageId;
        } else {
            result.error = 'failed_to_add_temp_image';
        }
    }
    
    if (processed?.text) {
        if (result.type === 'image') {
            result.type = 'combined';
            result.text = processed.text;
        } else {
            result.type = 'text';
            result.text = processed.text;
        }
    }
    
    return result;
};