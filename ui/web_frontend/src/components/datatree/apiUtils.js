import axios from 'axios';
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';

export const loadTreeData = async (etype, path = '', level=null) => {
    if (etype === '' || etype === 'all' || etype === undefined || etype === null) {
        return [];
    }
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + 'api/entry/tool/', {
            params: {
                rtype: 'tree',
                etype: etype,
                path: path,
                level: level !== null ? level : undefined
            }
        });
        return response.data;
    } catch (error) {
        console.error('Load tree data error:', error);
        parseBackendError(error);
        return [];
    }
};

export const getFeatureOptions = async (ctype) => {
    try {
        const response = await axios.get(getURL() + 'api/entry/tool/', {
            params: { ctype: ctype, rtype: 'feature' }
        });
        return response.data;
    } catch (error) {
        console.error('Get options error:', error);
        return [];
    }
};

export const openItemData = async (idx) => {
    try {
        const response = await axios.get(getURL() + 'api/entry/data/' + idx + '/');
        return response.data;
    } catch (error) {
        parseBackendError(error);
        return null;
    }
};

export const deleteData = async (idx) => {
    try {
        const response = await axios.delete(getURL() + 'api/entry/data/' + idx + '/');
        return response.data;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
};

export const renameData = async (sourceId, targetId, etype, is_folder) => {
    try {
        setDefaultAuthHeader();
        let func = 'api/entry/tool/'
        const response = await axios.get(getURL() + func, {
            params: {
                rtype: 'move',
                source: sourceId,
                target: targetId,
                is_folder: is_folder,
                etype: etype,
            }
        });
        return response.data;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
}
