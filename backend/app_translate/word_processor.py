import json
from loguru import logger
import pandas as pd
import os
from app_translate import localdict, translate
from backend.settings import BASE_DATA_DIR

class WordItem:
    def __init__(self, word, freq = localdict.DEFAULT_FREQ, phonetic = None, meaning = None, wfrom = None, example = None):
        self.word = word
        self.phonetic = phonetic
        self.freq = freq
        if type(meaning) == dict:
            self.meaning_dict = meaning
        elif type(meaning) == str and type(wfrom) == str:
            self.meaning_dict = {wfrom: meaning}
        else:
            self.meaning_dict = {}
        if type(wfrom) == list:
            self.from_list = wfrom
        elif type(wfrom) == str:
            self.from_list = [wfrom]
        else:
            self.from_list = []
        if type(example) == list:
            self.example_list = example
        elif type(example) == dict:
            self.example_list = [example]
        else:
            self.example_list = []

    def __repr__(self):
        return f"WordItem(word={self.word}, phonetic={self.phonetic}, from_list={self.from_list})"
    
class WordManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WordManager()
        return cls._instance
    
    def __init__(self):
        self.word_dict = {}
        self.path = os.path.join(BASE_DATA_DIR, "en_words.csv.gz")
        self.load()
        
    def add_word(self, word, freq=localdict.DEFAULT_FREQ, phonetic=None, meaning=None, wfrom=None, example=None):
        if word in self.word_dict:
            word_item = self.word_dict[word]
            if freq is not None and word_item.freq > freq:
                word_item.freq = freq
            if phonetic is not None and word_item.phonetic is None:
                word_item.phonetic = phonetic
            if meaning is not None and wfrom is not None and wfrom not in word_item.meaning_dict:
                word_item.meaning_dict[wfrom] = meaning
            if wfrom is not None and wfrom not in word_item.from_list:
                word_item.from_list.append(wfrom)
            if example is not None and example not in word_item.example_list:
                word_item.example_list.append(example)
        else:
            self.word_dict[word] = WordItem(word, freq, phonetic, meaning, wfrom, example)
                
    def get_word(self, word):
        return self.word_dict.get(word)
    
    def save(self):
        data = []
        for word, word_item in self.word_dict.items():
            if len(word_item.meaning_dict) > 0:
                meaning = json.dumps(word_item.meaning_dict, ensure_ascii=False)
            else:
                meaning = None
            if len(word_item.from_list) > 0:
                wfrom = json.dumps(word_item.from_list, ensure_ascii=False)
            else:
                wfrom = None
            if len(word_item.example_list) > 0:
                example = json.dumps(word_item.example_list, ensure_ascii=False)
            else:
                example = None
            data.append({
                'word': word,
                'freq': word_item.freq,
                'phonetic': word_item.phonetic,
                'meaning': meaning,
                'from': wfrom,
                'example': example,
            })
        df = pd.DataFrame(data)
        logger.info(f"save len = {len(data)}")
        df.to_csv(self.path, index=False, encoding='utf-8-sig', compression='gzip')
        
    def load(self):
        if os.path.exists(self.path):
            df = pd.read_csv(self.path, compression='gzip')
            for idx, item in df.iterrows():
                if pd.isna(item['meaning']):
                    meaning = None
                else:
                    meaning = json.loads(item['meaning'])
                if pd.isna(item['from']):
                    wfrom = None
                else:
                    wfrom = json.loads(item['from'])
                if pd.isna(item['example']):
                    example = None
                else:
                    example = json.loads(item['example'])
                word_item = WordItem(item['word'], item['freq'], item['phonetic'], meaning, wfrom, example)
                self.word_dict[item['word']] = word_item
        logger.info(f"load len = {len(self.word_dict)}")


def insert_words(user_id, wfrom = 'USER', limit = -1, debug=False):
    wm = WordManager.get_instance()
    count = 0
    for key,value in wm.word_dict.items():
        if wfrom not in value.from_list or wfrom not in value.meaning_dict:
            continue
        ret, obj = translate.add_to_db(word = value.word, regular_word = value.word, dst = value.meaning_dict[wfrom], 
                            user_id = user_id, freq = value.freq, wfrom = wfrom)
        if ret:
            count += 1        
        if debug and count % 100 == 0:
            logger.info(f'insert {wfrom} {count}')
        if limit > 0 and count >= limit:
            break
    logger.info(f'insert total {count}')