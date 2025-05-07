import { ElMessage } from 'element-plus';
import { saveEntry } from '../datatable/dataUtils';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'

const encodeSpecialChars = (str) => {
    return str.replace(/[ !@#$%^&*()+=[\]{};:,.<>?~\\]/g, (char) => {
        return encodeURIComponent(char);
    });
};

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
