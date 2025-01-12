import axios from 'axios';
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';

export async function fetchWordList(status='not_learned') {
    let func = 'api/translate/learn';
    setDefaultAuthHeader();
    const formData = new FormData();
    formData.append('rtype', 'get_words');
    formData.append('status', status);
    return await axios.post(getURL() + func, formData).then((res) => {
        return res.data.list;
    }).catch((err) => {
        console.error(err);
        throw err;
    });
}

export async function realUpdate(wordList) {
    if (wordList.length > 0) {
        let func = 'api/translate/learn';
        setDefaultAuthHeader();
        const formData = new FormData();
        formData.append('rtype', 'update');
        formData.append('list', JSON.stringify(wordList));
        await axios.post(getURL() + func, formData).then((res) => {
            console.log('Word list updated successfully');
        }).catch((err) => {
            console.error('Error updating word list', err);
        });
    }
}
