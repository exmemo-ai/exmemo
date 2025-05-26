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
import simplemma

from .models import StoreTranslate
from .word_processor import ItemInfo, ItemOpt, WordManager, ItemWord, DEFAULT_FREQ

TRANS_DEFAULT = "NOT FOUND"
MSG_ROLE = _("you_are_a_middle_school_english_teacher")


def add_to_db(user_id, word, freq = DEFAULT_FREQ, wfrom = "USER", 
                    word_info = None, debug=False):
    """
    support add and update
    """
    if debug:
        logger.info("now add_to_db inner")
    now = datetime.datetime.now()
    timestr = now.strftime("%Y-%m-%d %H:%M:%S")
    if debug:
        logger.debug(f"info {info}")
    new_info = ItemInfo(word_info, None)
    
    if StoreTranslate.objects.filter(word=word, user_id=user_id).exists():
        obj = StoreTranslate.objects.filter(word=word, user_id=user_id).first()
        obj.times = obj.times + 1
        if wfrom is not None:
            obj.wfrom = wfrom
        info = ItemInfo.deserialize(obj.info)
        if info is not None:
            info.update(new_info)
            obj.info = info.serialize()
        obj.save()
    else:
        if wfrom is None:
            wfrom = "USER"
        info = ItemInfo(word_info, ItemOpt())
        obj = StoreTranslate.objects.create(
            user_id=user_id, word=word, freq=freq, times=1, wfrom=wfrom, info=info.serialize(), 
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

        item_word = self.get_word_info(word, with_gpt, user_id, debug)
        if item_word is None:
            return False, None, None
        """ parse_sentence_example too long time
        if sentence is not None:
            found = False
            if item_word.example_list is None:
                item_word.example_list = []
            for example in item_word.example_list:
                if example['sentence'] == sentence:
                    found = True
                    break
            if not found:
                ret, example = parse_sentence_example(user_id, word, sentence, debug=debug)
                if ret:
                    item_word.example_list.append(example)
        """
        ret, obj = add_to_db(user_id, item_word.word, item_word.freq, None, 
                        item_word, debug=debug)
        translation = _(
            "word_{src}_translation_{dst}_phonetic_{phonetic}_freq_{freq}_count_{times}"
        ).format(
            src=item_word.word,
            dst=item_word.get_meaning(),
            phonetic=item_word.phonetic,
            freq=item_word.freq,
            times=obj.times,
        )
        return ret, item_word.word, translation

    def get_word_info(self, word, with_gpt, user_id, debug):        
        wm = WordManager.get_instance()
        word_item = wm.get_word(word)
        if word_item is None:
            lemmatized_text = simplemma.lemmatize(word, lang='en')
            if lemmatized_text != word:
                word_item = wm.get_word(lemmatized_text)
                if word_item is not None:
                    word = lemmatized_text
        if word_item is None:
            if with_gpt:
                ret, en_regular, translation, phonetic = translate_word_gpt(
                    word, user_id, debug=debug
                )
            else:
                translation = self.translator.translate(word)
                phonetic = None
                if translation != "" and translation != word:
                    ret, en_regular, translation = True, word, translation
                else:
                    ret, en_regular, translation = False, None, None
            if ret:
                word_item = ItemWord(
                    en_regular, DEFAULT_FREQ, phonetic=phonetic, wfrom='USER', meaning=translation
                )
        return word_item


def translate_word(word, uid, with_gpt=True, sentence=None):
    return TranslateWord.get_instance().translate_word(
        word, uid, with_gpt, sentence=sentence
    )


def translate_word_gpt(word, user_id, debug=False):
    demo = "{'en_regular':'xxx', 'zh_main':'yyy', 'zh_all':'zzz', 'phonetic':'[aaa]'}"
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
        if dic is not None and "en_regular" in dic and "zh_main" in dic and 'zh_all' in dic and 'phonetic' in dic:
            return ret, dic["en_regular"], dic["zh_all"], dic['phonetic']
    return False, None, None, None


def generate_sentence_example(user_id, word, debug=False):
    demo = '{"sentence": "This is a book.", "sentence_meaning": "这是一本书。", "word_meaning": "书"}'
    query = "Please give me a simple sentence with the word '{word}' in it, and translate the sentence to Chinese. result like {demo}".format(
        word=word, demo=demo
    )
    try:
        ret, dic, detail = llm_query_json(
            user_id, MSG_ROLE, query, "translate", debug=debug
        )
        if ret and dic is not None and "sentence" in dic and "sentence_meaning" in dic and "word_meaning" in dic:
            return True, dic
    except Exception as e:
        logger.warning(f"generate_sentence_example error: {e}")
    return False, {}

def parse_sentence_example(user_id, word, sentence, debug=False):
    demo = '{"sentence": "This is a book.", "sentence_meaning": "这是一本书。", "word_meaning": "书"}'
    query = "Please parse the sentence '{sentence}' and extract the meaning of the word '{word}' in it. result like {demo}".format(
        word=word, sentence=sentence, demo=demo
    )
    try:
        ret, dic, detail = llm_query_json(
            user_id, MSG_ROLE, query, "translate", debug=debug
        )
        if ret and dic is not None and "sentence" in dic and "sentence_meaning" in dic and "word_meaning" in dic:
            return True, dic
    except Exception as e:
        logger.warning(f"parse_sentence_example error: {e}")
    return False, {}