import os
import pandas as pd
from loguru import logger
import simplemma
from backend.settings import BASE_DATA_DIR # for test
#BASE_DATA_DIR = '/exports/exmemo/code/exmemo/backend/data/'

FREQ_FILE = os.path.join(BASE_DATA_DIR, "freq_20000_new.csv")
DEFAULT_FREQ = 99999

class FreqTools:
    __instance = None

    def __init__(self):
        logger.debug("load freq file")
        self.df = pd.read_csv(FREQ_FILE)

    @classmethod
    def get_instance(self):
        if self.__instance is None:
            self.__instance = self()
        return self.__instance

    def get_item(self, en):
        tmp = self.df[self.df['en'] == en]
        if tmp.shape[0] == 0:
            return None
        return tmp.iloc[0]
        
    def match(self, en):
        arr = self.df[self.df['en'].str.contains(en, case=False, na=False)]['en']
        return arr.tolist()
    
    def lookfor(self, en):
        '''
        return zh, rank, root
        '''
        item = self.get_item(en)
        if item is not None:
            return item['zh'], item['rank'], en
        lemmatized_text = simplemma.lemmatize(en, lang='en')
        if lemmatized_text == en:
            return None, -1, en
        item = self.get_item(lemmatized_text)
        if item is not None:
            return item['zh'], item['rank'], lemmatized_text
        return None, -1, en
    
    def get_freq(self, en):
        zh, rank, root = self.lookfor(en)
        if zh is None:
            return DEFAULT_FREQ
        return rank
