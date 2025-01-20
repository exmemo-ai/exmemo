"""
main interface to call other file and functions
"""

import re
import datetime
import traceback
from translate import Translator
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.user.user import *
from backend.common.llm.llm_hub import llm_query, llm_query_json

from . import localdict
from .models import StoreTranslate

TRANS_DEFAULT = "NOT FOUND"
MSG_ROLE = _("you_are_a_middle_school_english_teacher")


def find_word_local(word):
    translation, rank, root = localdict.FreqTools.get_instance().lookfor(word)
    if translation is not None:
        return True, root, rank, translation
    obj = StoreTranslate.objects.filter(word=word).first()
    if obj:
        if "regular_word" in obj.info:
            return True, obj.info["regular_word"], obj.freq, obj.info["translate"]
        else:
            return True, obj.info["word"], localdict.DEFAULT_FREQ, obj.info["translate"]
    return False, None, localdict.DEFAULT_FREQ, None


def add_to_db(word, regular_word, dst, user_id, sentence=None, freq = localdict.DEFAULT_FREQ):
    logger.info("now add_to_db inner", sentence)
    now = datetime.datetime.now()
    timestr = now.strftime("%Y-%m-%d %H:%M:%S")
    if freq == localdict.DEFAULT_FREQ:
        freq = localdict.FreqTools.get_instance().get_freq(regular_word)
    info = {"word": word, "regular_word": regular_word, "translate": dst, "freq": str(freq)}
    if sentence is not None:
        arr = sentence.split(" ")
        if len(arr) > 3:
            info["sentence"] = sentence
    logger.debug(f"info {info}")

    db_word = regular_word
    if StoreTranslate.objects.filter(word=db_word, user_id=user_id).exists():
        obj = StoreTranslate.objects.filter(word=db_word, user_id=user_id).first()
        obj.times = obj.times + 1
        obj.info = info
        obj.save()
    else:
        obj = StoreTranslate.objects.create(
            word=db_word, info=info, freq=freq, user_id=user_id, times=1,
            created_time=timestr
        )
    return True, obj


def translate_sentence(user_id, sentence):
    content = "Please translate the following sentence to Chinese: {sentence}".format(
        sentence=sentence
    )
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def translate_word_role(user_id, word, sentence):
    content = 'Please explain the meaning of the word "{word}" in the sentence "{sentence}", and try to keep the answer brief in Chinese.'.format(
        word=word, sentence=sentence
    )
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def translate_common(user_id, content):
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def extract_word(string):
    word = re.search(r"\b\w+\b", string).group()
    return word


def get_json_obj(string):
    ret = re.search(r"{.*}", string, re.DOTALL)
    if ret is None:
        return None
    json_str = ret.group()
    try:
        return json.loads(json_str)
    except json.decoder.JSONDecodeError:
        return None


class TranslateWord:
    _instance = None

    @staticmethod
    def get_instance():
        if TranslateWord._instance is None:
            TranslateWord._instance = TranslateWord()
        return TranslateWord._instance

    def __init__(self):
        self.translator = Translator(to_lang="zh", from_lang="en")

    def translate_word(self, word, user_id, with_gpt=False, sentence = None, debug=False):
        word = extract_word(word)
        if word is None:
            return False, None, None
        if debug:
            logger.debug(f"translate {word}, with_gpt {with_gpt}")

        ret, en_regular, rank, translation = self.get_word_info(word, with_gpt, user_id, debug)
        if ret:
            r, obj = add_to_db(word, en_regular, translation, user_id, sentence=sentence, freq = rank)
            if r:
                if 'regular_word' in obj.info:
                    src = obj.info["regular_word"]
                else:
                    src = obj.info["word"]
                translation = _(
                    "word_colon__{src}_enter_translation_colon__{dst}_enter_freq_colon__{freq}_enter_count_colon__{times}"
                ).format(
                    src=src,
                    dst=obj.info["translate"],
                    freq=obj.info["freq"],
                    times=obj.times,
                )
        return ret, en_regular, translation

    def get_word_info(self, word, with_gpt, user_id, debug):
        ret, en_regular, rank, translation = find_word_local(word)
        if ret:
            logger.debug("found in local")
        else:
            if with_gpt:
                ret, en_regular, translation = translate_word_gpt(
                    word, user_id, debug=debug
                )
            else:
                translation = self.translator.translate(word)
                if translation != "" and translation != word:
                    ret, en_regular, translation = True, word, translation
                else:
                    ret, en_regular, translation = False, None, None
        return ret, en_regular, rank, translation

def translate_word(word, uid, with_gpt=True, sentence=None):
    return TranslateWord.get_instance().translate_word(
        word, uid, with_gpt, sentence=sentence
    )


def translate_word_gpt(self, word, user_id, debug=False):
    demo = "{'en_regular':'xxx', 'zh_main':'yyy', 'zh_all':'zzz'}"
    req = f"""
    Please take "{word}" and obtain its base form: when extracting the base form, 
    the part of speech remains unchanged, but plural forms, tenses, etc., are removed. 
    Translate its main meaning and all meanings into Chinese, and return them in JSON format: {demo}
    """
    sysinfo = "You are an English teacher"
    ret, dic, _ = llm_query_json(
        user_id,
        sysinfo,
        req,
        "translate",
        # engine_type='deepseek',
        debug=False,
    )
    if ret:
        if dic is not None and "en_regular" in dic and "zh_main" in dic and 'zh_all' in dic:
            return ret, dic["en_regular"], dic["zh_all"]
    return False, None, None


def generate_sentence_example(user_id, word):
    demo = '{"sentence": "This is a book.", "sentence_meaning": "这是一本书。", "word_meaning": "书"}'
    query = "Please give me a simple sentence with the word '{word}' in it, and translate the sentence to Chinese. result like {demo}".format(
        word=word, demo=demo
    )
    try:
        ret, dic, detail = llm_query_json(
            user_id, MSG_ROLE, query, "translate", debug=True
        )
        if ret and dic is not None and "sentence" in dic and "sentence_meaning" in dic and "word_meaning" in dic:
            return True, dic
    except Exception as e:
        logger.warning(f"generate_sentence_example error: {e}")
    return False, {}