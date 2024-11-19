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
