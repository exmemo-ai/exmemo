import axios from 'axios';
import { getURL, parseBackendError, setDefaultAuthHeader } from '@/components/support/conn';
import SettingService from '@/components/settings/settingService';
import { t } from '@/utils/i18n';

export const LEARN_WORD_VOC = 'learn_word_voc';
export const LEARN_WORD_VOC_DEFAULT = 'ALL';
export const LEARN_WORD_VOC_BASE = 'BASE';

export async function getSummary() {
    const dateStr = new Date().toISOString().slice(0, 10);
    let func = 'api/translate/learn';
    setDefaultAuthHeader();
    const formData = new FormData();
    formData.append('rtype', 'summary');
    if (dateStr) {
        formData.append('date', dateStr);
    }
    return await axios.post(getURL() + func, formData).then((res) => {
        console.log(res.data)
        if ('total_words' in res.data) {
            let desc =  t('trans.total_words') + ': ' +  res.data.total_words +'\n';
            desc = desc + t('trans.learned') + ': ' + res.data.learned + '\n';
            desc = desc + t('trans.not_learned') + ': ' + res.data.not_learned + '\n';
            desc = desc + t('trans.to_review_today') + ': ' + res.data.today_review + '\n';
            desc = desc + t('trans.to_learn_today') + ': ' + res.data.today_learning + '\n';
            desc = desc + t('trans.to_review') + ': ' +  res.data.to_review;
            return [desc, res.data.learn_data, res.data.review_data];
        }

    }).catch((err) => {
        if (err.response && err.response.status === 401) {
            parseBackendError(null, err);
            throw new Error('Token expired');
        }
        console.error(err);
        return ['Error: ' + err, null];
    });
}

export async function fetchWordList(rtype, status=null, date=null, wfrom=null) {
    let func = 'api/translate/learn';
    setDefaultAuthHeader();
    const formData = new FormData();
    formData.append('rtype', rtype);
    if (status) {
       formData.append('status', status);
    }
    if (date) {
        formData.append('date', date);
    }
    if (wfrom) {
        formData.append('wfrom', wfrom);
    }
    return await axios.post(getURL() + func, formData).then((res) => {
        return res.data.list;
    }).catch((err) => {
        if (err.response && err.response.status === 401) {
            parseBackendError(null, err);
            throw new Error('Token expired');
        }
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
            console.log('Word list updated successfully, list', wordList.length);
        }).catch((err) => {
            if (err.response && err.response.status === 401) {
                parseBackendError(null, err);
                throw new Error('Token expired');
            }    
            console.error('Error updating word list', err);
        });
    }
}

export async function getExamples(word) {
    let func = 'api/translate/learn';
    setDefaultAuthHeader();
    const formData = new FormData();
    formData.append('rtype', 'get_sentence');
    formData.append('word', word);
    
    return axios.post(getURL() + func, formData)
        .then((res) => {
            console.log('Response data:', res.data);
            return res.data;
        })
        .catch((err) => {
            if (err.response && err.response.status === 401) {
                parseBackendError(null, err);
                throw new Error('Token expired');
            }    
            console.error('Error fetching examples:', err);
            throw err;
        });
}

export async function getMeaning(info, voc_name = null) {
    let meaning = ''
    if (info && info.base && info.base.meaning_dict) {
        const meaning_dict = info.base.meaning_dict;
        if (voc_name === null) {
            const settingService = SettingService.getInstance();
            await settingService.loadSetting();
            voc_name = settingService.getSetting(LEARN_WORD_VOC, LEARN_WORD_VOC_DEFAULT);
        }
        if (voc_name in meaning_dict) {
            meaning = meaning_dict[voc_name];
        } else if (LEARN_WORD_VOC_BASE in meaning_dict) {
            meaning = meaning_dict[LEARN_WORD_VOC_BASE];
        } else if (Object.keys(meaning_dict).length > 0) {
            meaning = meaning_dict[Object.keys(meaning_dict)[0]];
        }
    } else if (info.translate) {
        meaning = info.translate;
    }
    return meaning;
}
