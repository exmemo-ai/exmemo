import { saveEntry } from '../datatable/dataUtils';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'

const IMAGE_DIR = 'attachments_2025'
const IMAGE_PREFIX = 'Pasted_image_'

const encodeSpecialChars = (str) => {
    return str.replace(/[ !@#$%^&*()+=[\]{};:,.<>?~\\]/g, (char) => {
        return encodeURIComponent(char);
    });
};

const getImagePattern = (fullPath = true) => {
    const imagePath = fullPath ? `${IMAGE_DIR}/${IMAGE_PREFIX}` : IMAGE_PREFIX;
    return `!\\[.*?\\]\\((${imagePath}[^)]+)\\)`;
};

class TempImageManager {
    constructor() {
        this.imageMap = new Map();
    }

    getPrefix(fullPath = true) {
        if (fullPath) {
            return `${IMAGE_DIR}/${IMAGE_PREFIX}`;
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
        const imageIds = Array.from(content.matchAll(new RegExp(getImagePattern(), 'g')))
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
    }

    cleanupTempImages(content) {
        const usedIds = Array.from(content.matchAll(new RegExp(getImagePattern(), 'g')))
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
        console.error('Error loading image:', error);
        return src;
    }
    return src;
};
