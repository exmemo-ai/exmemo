import pandas as pd
import os
from nltk.stem import PorterStemmer
from nltk.stem import LancasterStemmer
from nltk.stem import SnowballStemmer
from nltk.stem import WordNetLemmatizer
from django.utils.translation import gettext as _

from . import freq_en
from backend.common.llm.llm_hub import llm_query

WORD_ROOT_PATH = "/opt/git/toolpal/data/word_root.csv"

porter_stemmer = PorterStemmer()
snowball_stemmer = SnowballStemmer("english")
wordnet_lemmatizer = WordNetLemmatizer()
lancaster_stemmer = LancasterStemmer()

DEFAULT_DESC = _("root_not_found")


class ParseWord:
    def __init__(self, data_path=WORD_ROOT_PATH):
        self.data_path = data_path
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            self.df = pd.read_csv(self.data_path)
        else:
            self.df = pd.DataFrame(columns=["word", "parse"])

    def save(self, debug=False):
        if debug:
            print(f"now save !!! {self.df.shape}, {self.data_path}")
        self.df.to_csv(self.data_path, index=False)

    def match(self, user_id, word, with_gpt=False, debug=False):
        items = self.df[self.df["word"] == word]
        if len(items) > 0:
            desc = items.iloc[0]["parse"]
            if desc == DEFAULT_DESC:
                return None
            else:
                return desc
        if with_gpt:
            return self.find_root_by_llm(user_id, word, debug=debug)
        return None

    def real_insert(self, word, parse):
        new_row = pd.DataFrame([{"word": word, "parse": parse}])
        # self.df = self.df.append(new_row, ignore_index=True)
        self.df = pd.concat([self.df, new_row]).reset_index(drop=True)

    def insert(self, word, parse, force=False, debug=False):
        if self.match(word, with_gpt=False) is None:
            self.real_insert(word, parse)
        else:
            if force:
                self.df = self.df[self.df["word"] != word]
                self.real_insert(word, parse)
        self.save(debug=debug)

    def parse(self, root):
        """
        Old interface, keep it for now
        """
        root = root.replace("。", "。\n")
        root = root.replace("；", "；\n")
        # print(root)
        root = root.replace("\n\n", "\n")
        arr = root.split("\n")
        # print(arr)
        ret = []
        for x in arr:
            if x.find(_("simple_answer")) != -1 and len(ret) > 0:
                break
            if x.find(_("root")) != -1 or x.find(_("the_root_of_the_word_is")) != -1:
                # print(x)
                ret.append(x)
            if x.find(_("affix")) != -1:
                # print(x)
                ret.append(x)
            if x.find(_("prefix")) != -1:
                # print(x)
                ret.append(x)
            if x.find(_("suffix")) != -1:
                # print(x)
                ret.append(x)
        return "\n".join(ret)

    def find_root_by_llm(self, user_id, en, debug=False):
        req = "Does the word {en} have a root? If yes, please answer 'YES', if not, answer 'NO'".format(
            en=en
        )
        sysinfo = "You are an English teacher"
        ret, desc, _ = llm_query(user_id, sysinfo, req, "translate", debug=debug)
        if ret.upper().find("YES") != -1:
            if debug:
                print("Is there a root word {en} {ret}".format(en=en, ret=ret))
            req = "Break down the root words and affixes of {en} completely, into the finest granularity, and explain the meaning of each part, no other responses".format(
                en=en
            )
            ret, desc, _ = llm_query(user_id, sysinfo, req, "translate", debug=debug)
            self.insert(en, ret, debug=debug)
            return ret
        self.insert(
            en, DEFAULT_DESC, debug=debug
        )  # Write it down to avoid searching again, whether found or not
        return None


class RootFinder:
    @staticmethod
    def get_root_manual(word):
        """
        Manually remove suffix
        """
        arr = {
            "ible": "y",
            "iness": "y",
            "ness": "",
            "ing": "",
            "ly": "",
            "ed": "",
            "en": "",
            "s": "",
        }
        edit = True
        while edit:
            edit = False
            for key, value in arr.items():
                if word.endswith(key):
                    word = word.replace(key, value)
                    edit = True
                    freq = freq_en.FreqTools.get_instance().get_freq(word)
                    if freq != -1:
                        print("@@@@@@@ word", word, freq)
                        return word
                    break
        # word = porter_stemmer.stem(word)
        return word


def find_root(word, debug=False):
    """
    Get Root Word
    """
    stem_word_1 = porter_stemmer.stem(word)
    if debug:
        print(f"porter {word} -> {stem_word_1}")
    stem_word_2 = snowball_stemmer.stem(word)
    if debug:
        print(f"snowball {word} -> {stem_word_2}")
    stem_word_3 = lancaster_stemmer.stem(word)
    if debug:
        print(f"lancaster {word} -> {stem_word_3}")
    stem_word_4 = wordnet_lemmatizer.lemmatize(word, pos="v")
    if debug:
        print(f"wordnet {word} -> {stem_word_4}")
    return list(set([stem_word_1, stem_word_2, stem_word_3, stem_word_4]))


def get_freq_max(word):
    """
    Find the Most Frequent Root Word
    """
    ret = find_root(word)
    arr = []
    for x in ret:
        freq = freq_en.FreqTools.get_instance().get_freq(x)
        if freq != -1:
            arr.append((x, freq))
    if len(arr) > 0:
        arr = sorted(arr, key=lambda x: x[1])
        return arr[0]
    return word, freq_en.FreqTools.get_instance().get_freq(word)
