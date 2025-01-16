import axios from 'axios';
import { ElMessage } from 'element-plus';
import { getURL, parseBackendError, parseBlobData } from '@/components/support/conn'
import { t } from '@/utils/i18n'

export async function saveEntry({
    parentObj,
    form,
    file,
    onProgress,
    onUploadStart
}) {
    let func = 'api/entry/data/';
    const formData = new FormData();

    if (form.etype === 'record') {
        if (form.raw === '') {
            ElMessage.error(t('inputRecordContent'));
            return false;
        }
        formData.append('raw', form.raw);
    } else if (form.etype === 'file' && form.idx === null) {
        if (!file) {
            ElMessage.error(t('selectFileError'));
            return false;
        }
        formData.append('etype', 'file');
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
        formData.append('filepaths', `${fileName}`);
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

    if (form.idx !== null) {
        formData.append('idx', form.idx);
    }

    const cancelTokenSource = axios.CancelToken.source();
    onUploadStart?.(cancelTokenSource);

    try {
        if (form.idx !== null) {
            func += form.idx + '/';
            const response = await axios.put(getURL() + func, formData);
            if (response.data.status === 'success') {
                ElMessage({ type: 'success', message: t('updateSuccess') });
                parentObj?.fetchData();
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
                ElMessage({ type: 'success', message: t('saveSuccess') });
                parentObj?.fetchData();
            } else {
                ElMessage({ type: 'error', message: t('saveFail') });
            }
        }
        return true;
    } catch (error) {
        if (axios.isCancel(error)) {
            ElMessage({ type: 'info', message: t('operationCancelled') });
        } else {
            parseBackendError(parentObj, error)
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
