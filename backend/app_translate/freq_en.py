import os
import pandas as pd
from backend.settings import BASE_DATA_DIR

FREQ_FILE = os.path.join(BASE_DATA_DIR, "freq_20000.xlsx")


class FreqTools:  # This code is temporarily unused, later remove
    __instance = None

    def __init__(self):
        print("load freq file")
        self.dic = {}
        if False:
            df = pd.read_excel(
                "/opt/toolpal/tmp/freq_20000.xlsx", sheet_name="1 lemmas"
            )
            for idx, item in df.iterrows():
                self.dic[item["lemma"]] = item["rank"]
        else:
            df = pd.read_excel(FREQ_FILE, header=None)
            for idx, item in df.iterrows():
                self.dic[item[1]] = item[0]

    @classmethod
    def get_instance(self):
        if self.__instance is None:
            self.__instance = self()
        return self.__instance

    def get_freq(self, en):
        if en in self.dic:
            return self.dic[en]
        else:
            return -1
