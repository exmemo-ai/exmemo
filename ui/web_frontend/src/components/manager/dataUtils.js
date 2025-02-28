import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getURL, parseBackendError, parseBlobData, setDefaultAuthHeader } from '@/components/support/conn'
import { t } from '@/utils/i18n'

export async function saveEntry({
    onSuccess,
    form,
    path,
    file,
    onProgress,
    onUploadStart, 
    showMessage = true
}) {
    let func = 'api/entry/data/';
    const formData = new FormData();

    if (form.etype === 'record') {
        if (form.raw === '') {
            ElMessage.error(t('inputRecordContent'));
            return false;
        }
        formData.append('raw', form.raw);
    } else if (form.etype === 'file'||form.etype === 'note') {
        if (!file && (form.idx === null || form.idx === undefined)) {
            if (form.etype === 'file') {
                ElMessage.error(t('selectFileError'));
                return false;
            } else { // ‘note'
                file = new File([''], 'empty.md', { type: 'text/markdown' });
            }
        }
        if (file) {
            formData.append('files', file);
            let fileName = file.name;
            if (form.title !== '') {
                if (fileName.indexOf('.') > 0) {
                    const fileExt = fileName.split('.').pop();
                    const titleExt = form.title.split('.').pop();
                    if (fileExt !== titleExt) {
                        fileName = `${form.title}.${fileExt}`;
                    } else {
                        fileName = form.title;
                    }
                } else {
                    fileName = form.title;
                }
            }
            formData.append('filenames', fileName);
            if (path && path.length > 0) {
                if (path[path.length - 1] !== '/') {
                    formData.append('filepaths', `${path}`);
                } else {
                    formData.append('filepaths', `${path}${fileName}`);
                }
            } else {
                formData.append('filepaths', `${fileName}`);
            }
        }
    } else if (form.etype === 'web') {
        if (form.addr === '') {
            ElMessage.error(t('inputWebAddressError'));
            return false;
        }
        formData.append('addr', form.addr);
    }

    const fields = ['ctype', 'etype', 'title', 'status', 'atype'];
    fields.forEach(field => {
        if (form[field]) {
            formData.append(field, form[field]);
        }
    });
    if (form.meta) {
        formData.append('meta', JSON.stringify(form.meta));
    }

    if (form.idx && form.idx !== null) {
        formData.append('idx', form.idx);
    }

    const cancelTokenSource = axios.CancelToken.source();
    onUploadStart?.(cancelTokenSource);

    try {
        if (form.idx && form.idx !== null) {
            func += form.idx + '/';
            const response = await axios.put(getURL() + func, formData);
            if (response.data.status === 'success') {
                if (showMessage) ElMessage({ type: 'success', message: t('updateSuccess') });
                onSuccess?.(response.data);
                return response.data;
            } else {
                ElMessage({ type: 'error', message: t('updateFail') });
            }
        } else {
            const response = await axios.post(getURL() + func, formData, {
                onUploadProgress: progressEvent => {
                    onProgress?.(Math.round((progressEvent.loaded * 100) / progressEvent.total));
                },
                cancelToken: cancelTokenSource.token
            });
            if (response.data.status === 'success') {
                if (showMessage) ElMessage({ type: 'success', message: t('saveSuccess') });
                onSuccess?.(response.data);
                return response.data;
            } else {
                if (response.data.info) {
                    ElMessage({ type: 'error', message: response.data.info });
                } else {
                    ElMessage({ type: 'error', message: t('saveFail') });
                }
            }
        }
        return false;
    } catch (error) {
        if (axios.isCancel(error)) {
            ElMessage({ type: 'info', message: t('operationCancelled') });
        } else {
            parseBackendError(null, error)
        }
        return false;
    }
}

export function downloadFile(idx, filename) {
    //console.log(t('downloadFile', { idx, filename }));
    let table_name = 'data'
    axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/' + 'download', {
        responseType: 'blob',
    })
        .then(response => {
            parseBlobData(response, filename);
        });
}

export async function fetchItem(idx) {
    let table_name = 'data';
    setDefaultAuthHeader();
    try {
        const response = await axios.get(getURL() + 'api/entry/' + table_name + '/' + idx + '/');
        return {
            success: true,
            data: response.data
        };
    } catch (error) {
        if (error.response && error.response.status === 401) {
            parseBackendError(null, error);
        } else {
            console.error(error);
            ElMessage.error(t('operationFailed'));
        }
        return {
            success: false,
            error
        };
    }
}

export const confirmOpenNote = (data) => {
    if (data && data.list && data.list.length > 0) {
        const addr = data.list[0];
        let func = 'api/entry/data/'
        let params = {
            keyword: addr, 
            etype: 'note',
            max_count: 1
        }
        axios.get(getURL() + func, { params: params })
            .then(response => {
                const results = response.data['results'];
                if (results && results.length > 0) {
                    showConfirm(results[0].idx);
                }
            })
            .catch(error => {
                parseBackendError(null, error);
            });
    }
};

const showConfirm = (idx) => {
    ElMessageBox.confirm(
        t('viewMarkdown.openNote'), 
        t('viewMarkdown.openNoteTitle'), 
        {
            confirmButtonText: t('confirm'),
            cancelButtonText: t('cancel'),
            type: 'info',
        }
    ).then(() => {
        window.open(`${window.location.origin}/edit_markdown?idx=${idx}`, '_blank');
    }).catch(() => {
    });
};
