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

export const deleteDir = async (path, etype) => {
    try {
        const response = await axios.delete(getURL() + 'api/entry/tool/', {
            params: { rtype: 'delete', path: path, etype: etype, is_folder: true, is_async: true }
        });
        return response.data;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
}

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
                is_async: true
            }
        });
        return response.data;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
};

export const importNotes = async (sourcePath, targetPath, is_folder, is_async, overwrite) => {
    try {
        let func = 'api/entry/tool/'
        const response = await axios.get(getURL() + func, {
            params: {
                rtype: 'import',
                source: sourcePath,
                target: targetPath,
                is_folder: is_folder,
                is_async: true,
                overwrite: overwrite, 
            }
        });
        return response.data;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
};

const pathArrayToTree = (paths) => {
    const root = { name: '', children: {}, isFile: false };
    if (!Array.isArray(paths)) {
        return root;
    }

    const validPaths = paths.filter(path => typeof path === 'string');
    validPaths.forEach(path => {
        if (!path) return;
        const parts = path.split('/').filter(Boolean);
        let current = root;
        
        parts.forEach((part, index) => {
            if (!current.children[part]) {
                current.children[part] = {
                    name: part,
                    children: {},
                    isFile: index === parts.length - 1 && part.length === 40
                };
            }
            current = current.children[part];
        });
    });
    return root;
};

export const getDir = async (etype, path="") => {
    try {
        let func = 'api/entry/tool/'
        const response = await axios.get(getURL() + func, {
            params: {
                rtype: 'getdir',
                etype: etype,
                path: path
            }
        });
        const treeStructure = pathArrayToTree(response.data.dirs);
        return treeStructure;
    } catch (error) {
        parseBackendError(error);
        throw error;
    }
};

export const refreshData = async (path, etype, is_folder) => {
    try {
        setDefaultAuthHeader();
        const response = await axios.get(getURL() + 'api/entry/tool/', {
            params: {
                rtype: 'refreshdata',
                etype: etype,
                path: path, 
                is_folder: is_folder,
                is_async: true
            }
        });
        return response.data;
    }
    catch (error) {
        parseBackendError(error);
        throw error;
    }
}

