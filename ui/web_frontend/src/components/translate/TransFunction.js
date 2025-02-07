import axios from 'axios';
import { getURL, parseBackendError } from '@/components/support/conn';

export function translateFunc(obj, rtype, word, sentence, callback) {
    console.log('translate', 'type:', rtype, 'word:', word, 'sent:', sentence);
    let func = 'api/translate/translate';
    const formData = new FormData();
    if (word !== null) {
        formData.append('word', word);
    }
    if (sentence !== null) {
        formData.append('sentence', sentence);
    }
    formData.append('rtype', rtype)
    console.log('formData:', formData);
    axios.post(getURL() + func, formData).then((res) => {
        console.log(res.data);
        if (res.data.status == 'success') {
            if (res.data.info) {
                callback(res.data.info);
            }
        }
    }).catch((err) => {
        parseBackendError(obj, err);
    });
}

export async function importWordList(obj, option, callback) {
    console.log('importWordList', 'wordList:', option);
    let func = 'api/translate/learn';
    const formData = new FormData();
    formData.append('rtype', 'insert_wordlist');
    formData.append('wfrom', option);
    try {
        const res = await axios.post(getURL() + func, formData);
        console.log(res.data);
        if (res.data.status == 'success') {
            if (res.data.info) {
                callback(res.data.info);
            }
        }
    } catch (err) {
        parseBackendError(obj, err);
    }
}

export async function deleteWordList(obj, option, callback) {
    console.log('deleteWordList', 'deleteOption:', option);
    let func = 'api/translate/learn';
    const formData = new FormData();
    formData.append('rtype', 'delete_wordlist');
    formData.append('status', option);
    try {
        const res = await axios.post(getURL() + func, formData);
        console.log(res.data);
        if (res.data.status == 'success') {
            if (res.data.info) {
                callback(res.data.info);
            }
        }
    } catch (err) {
        parseBackendError(obj, err);
    }
}

export async function getWordsFrom(obj) {
    console.log('getWordsFrom');
    let func = 'api/translate/learn';
    const formData = new FormData();
    formData.append('rtype', 'get_wordsfrom');
    try {
        const res = await axios.post(getURL() + func, formData);
        console.log(res.data);
        if (res.data.status == 'success') {
            if (res.data.list) {
                return res.data.list;
            }
        }
    } catch (err) {
        parseBackendError(obj, err);
    }
    return [];
}
