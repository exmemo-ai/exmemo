import json
from loguru import logger
import pandas as pd
import os
from app_translate import localdict, translate
from backend.settings import BASE_DATA_DIR

class ItemWord:
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
        return f"ItemWord(word={self.word}, phonetic={self.phonetic}, from_list={self.from_list})"

    def update(self, word):
        if word is None:
            return
        if word.phonetic is not None:
            self.phonetic = word.phonetic
        if word.freq is not None and word.freq < self.freq:
            self.freq = word.freq
        if word.meaning_dict is not None:
            for k, v in word.meaning_dict.items():
                if k not in self.meaning_dict:
                    self.meaning_dict[k] = v
        if word.from_list is not None:
            for f in word.from_list:
                if f not in self.from_list:
                    self.from_list.append(f)
        if word.example_list is not None:
            for e in word.example_list:
                if e not in self.example_list:
                    self.example_list.append(e)        
        
    def serialize(self):
        if pd.isna(self.phonetic):
            phonetic = None
        else:
            phonetic = self.phonetic
        return {
            "word": self.word,
            "phonetic": phonetic,
            "freq": self.freq,
            "meaning_dict": self.meaning_dict,
            "from_list": self.from_list,
            "example_list": self.example_list,
        }
        
    def get_meaning(self, wfrom = None):
        if wfrom is not None and wfrom in self.meaning_dict:
            return self.meaning_dict[wfrom]
        if len(self.meaning_dict) > 0:
            return list(self.meaning_dict.values())[0]
        return None

class ItemOpt:
    def __init__(self, learn_times = 0, review_times = 0, last_review_time = None, learn_date = None):
        self.learn_times = learn_times
        self.review_times = review_times
        self.last_review_time = last_review_time
        self.learn_date = learn_date
    
    def update(self, opt):
        if opt is None:
            return
        if opt.learn_times > self.learn_times:
            self.learn_times = opt.learn_times
        if opt.review_times > self.review_times:
            self.review_times = opt.review_times
        if opt.last_review_time is not None:
            self.last_review_time = opt.last_review_time
        if opt.learn_date is not None:
            self.learn_date = opt.learn_date
        
    def serialize(self):
        return {
            "learn_times": self.learn_times,
            "review_times": self.review_times,
            "last_review_time": self.last_review_time,
            "learn_date": self.learn_date,
        }

class ItemInfo:
    def __init__(self, word = None, opt = None):
        if word is None:
            self.word = ItemWord(None)
        else:
            self.word = word
        if opt is None:
            self.opt = ItemOpt()
        else:
            self.opt = opt
    
    def update(self, info):
        self.word.update(info.word)
        self.opt.update(info.opt)
        
    def serialize(self):
        return {
            "base": self.word.serialize(),
            "opt": self.opt.serialize(),
        }

    @staticmethod    
    def deserialize(data):
        if data is None:
            return None
        if "base" in data:
            itemWord = ItemWord(
                word=data["base"]["word"],
                phonetic=data["base"]["phonetic"],
                freq=data["base"]["freq"],
                meaning=data["base"]["meaning_dict"],
                wfrom=data["base"]["from_list"],
                example=data["base"]["example_list"],
            )
        elif "word" in data and "translate" in data and "freq" in data:
            wm = WordManager.get_instance()
            itemword = wm.get_word(data["word"])
            if itemword is None:
                if "examples" in data:
                    examples = data["examples"]
                else:
                    examples = []            
                itemWord = ItemWord(
                    word=data["word"],
                    freq=data["freq"],
                    wfrom='USER',
                    meaning=data["translate"],
                    example_list=examples)
        else:
            return None
        if "opt" in data:
            itemOpt = ItemOpt(
                learn_times=data["opt"]["learn_times"],
                review_times=data["opt"]["review_times"],
                last_review_time=data["opt"]["last_review_time"],
                learn_date=data["opt"]["learn_date"],
            )
        else:
            itemOpt = ItemOpt(learn_times=data.get('learn_times', 0), 
                               review_times=data.get('review_times', 0), 
                               last_review_time=data.get('last_review_time', None), 
                               learn_date=data.get('learn_date', None))
        return ItemInfo(itemWord, itemOpt)
    
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
            if phonetic is not None and (word_item.phonetic is None or len(word_item.phonetic) == 0):
                word_item.phonetic = phonetic
            if meaning is not None and wfrom is not None and wfrom not in word_item.meaning_dict:
                word_item.meaning_dict[wfrom] = meaning
            if wfrom is not None and wfrom not in word_item.from_list:
                word_item.from_list.append(wfrom)
            if example is not None and example not in word_item.example_list:
                word_item.example_list.append(example)
        else:
            self.word_dict[word] = ItemWord(word, freq, phonetic, meaning, wfrom, example)
                
    def get_word(self, word):
        return self.word_dict.get(word, None)
    
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
                word_item = ItemWord(item['word'], item['freq'], item['phonetic'], meaning, wfrom, example)
                self.word_dict[item['word']] = word_item
        logger.info(f"load len = {len(self.word_dict)}")


def insert_words(user_id, wfrom = 'USER', limit = -1, debug=False):
    wm = WordManager.get_instance()
    count = 0
    for key,value in wm.word_dict.items():
        if wfrom not in value.from_list or wfrom not in value.meaning_dict:
            continue
        ret, obj = translate.add_to_db(user_id = user_id, word = value.word, 
                                             freq = value.freq, wfrom = wfrom,
                                             word_info = value)
        if ret:
            count += 1        
        if debug and count % 100 == 0:
            logger.info(f'insert {wfrom} {count}')
        if limit > 0 and count >= limit:
            break
    logger.info(f'insert total {count}')