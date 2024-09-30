"""
main interface to call other file and functions
"""

import datetime
import traceback
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.user.user import *
from backend.common.llm.llm_hub import llm_query

from . import regular_en
from . import freq_en
from . import dict
from . import word_root
from .models import StoreTranslate

TRANS_DEFAULT = "NOT FOUND"
MSG_ROLE = _("you_are_a_middle_school_english_teacher")

dtools = dict.MyDict.get_instance()
pw_tools = word_root.ParseWord()


def get_freq(en):
    """
    Get word frequency
    """
    freq = freq_en.FreqTools.get_instance().get_freq(en)
    if freq == -1:
        freq = 99999
    return freq


def get_zh(en, base_zh, etc=False):
    """
    Use xdict for translation
    """
    ret, regular_en, zh = dtools.en_to_ch(en, etc=etc)
    if ret:
        return ret, regular_en, zh
    else:
        return ret, en, base_zh


def get_root(user_id, en, with_gpt, debug):
    """
    Translation of the root word
    """
    root = dtools.en_root(en)  # 1. Get the root from the dictionary, e.g., rejection

    print("ret root", root)
    if len(root) > 0:
        return True, en, root
    else:
        if len(en) > 5:  # Consider length 5 and below as no root word
            ret_chat = pw_tools.match(en, user_id, with_gpt=with_gpt, debug=debug)
            if ret_chat is not None:  ## 2: gpt, e.g.: suitcase
                return True, en, ret_chat
            else:  # 3. Strong Removal, Remove Its Suffix, e.g., bookment
                print("in section 3")
                ret_root, root_freq = word_root.get_freq_max(en)
                if ret_root != en:
                    ret, en_regular, zh = dtools.en_to_ch(ret_root)
                    if ret:
                        return (
                            True,
                            en_regular,
                            _("{}__enter_word_frequency_{}__enter_meaning_{}").format(
                                en_regular, root_freq, zh
                            ),
                        )
                    else:
                        return False, en, None
    return False, en, None


def trans_inner(user_id, base_en, base_zh, with_gpt=True, debug=False):
    """
    core function, rearrange English to Chinese, add frequency, root words, etc., not yet seen where it is called
    """
    ret_dic = {"base_en": base_en, "base_zh": base_zh}
    ret, regular_en, zh = get_zh(ret_dic["regular_en"], base_zh)
    ret_dic["regular_en"] = regular_en
    ret_dic["simple_zh"] = zh
    ret_dic["freq"] = get_freq(ret_dic["regular_en"])
    ret, regular_en, zh = get_root(user_id, ret_dic["regular_en"], with_gpt, debug)
    ret_dic["root"] = zh
    return ret_dic


def add_translate(content, user_id, save=True):
    """
    message call this function
    """
    logger.debug(f"add_translate {content}")

    ret, regular_en, zh = get_zh(content, TRANS_DEFAULT, etc=False)
    if ret:
        if save:
            return add_to_db(regular_en, zh, user_id)
        else:
            return True, ret
    else:
        return False, ""


def add_to_db(src, dst, user_id, sentence=None):
    logger.info("now add_to_db inner", sentence)
    times = 1
    now = datetime.datetime.now()
    timestr = now.strftime("%Y-%m-%d %H:%M:%S")
    freq = get_freq(src)
    info = {"word": src, "translate": dst, "freq": freq}
    if sentence is not None:
        arr = sentence.split(" ")
        if len(arr) > 3:
            info["sentence"] = sentence
    logger.debug(f"info {info}")

    if StoreTranslate.objects.filter(word=src, user_id=user_id).exists():
        obj = StoreTranslate.objects.get(word=src, user_id=user_id)
        obj.times = obj.times + 1
        obj.info = info
        obj.save()
        times = obj.times
    else:
        StoreTranslate.objects.create(
            word=src, info=info, freq=freq, user_id=user_id, created_time=timestr
        )
    return True, _(
        "word_colon__{src}_enter_translation_colon__{dst}_enter_freq_colon__{freq}_enter_count_colon__{times}"
    ).format(src=src, dst=dst, freq=freq, times=times)


def translate_sentence(user_id, sentence):
    content = "Please translate the following sentence to Chinese: {sentence}".format(
        sentence=sentence
    )
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def translate_word_role(user_id, word, sentence):
    content = 'Please explain the meaning of the word "{word}" in the sentence "{sentence}", and try to keep the answer brief'.format(
        word=word, sentence=sentence
    )
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def translate_common(user_id, content):
    ret, answer, _ = llm_query(user_id, MSG_ROLE, content, "translate", debug=True)
    logger.info(f"test {ret} {answer}")
    return ret, answer


def translate_word(word, uid, with_gpt=False):
    ret = True
    zh = None
    regular_word = word
    logger.debug(f"translate_word {word}")
    try:
        word = regular_en.extract_first_en_seq(word)
        logger.debug(f"extract_first_en_seq {word}")
        regular_word = regular_en.regular_lemma(word)
        logger.debug(f"regular_word {regular_word}")
        ret, regular_en_word, zh = get_zh(regular_word, TRANS_DEFAULT, etc=False)
        logger.debug(f"get_zh {zh}")
        if ret:
            regular_word = regular_en_word
        else:
            ret, regular_en_word, zh = get_root(
                uid, regular_word, with_gpt=with_gpt, debug=False
            )
            logger.debug(f"get_root {zh}")
            if ret:
                regular_word = regular_en_word
    except Exception as e:
        logger.error(f"translate_word {e}")
        zh = None
        traceback.print_exc()
    if zh is None or zh == "":
        ret = False
    logger.debug(f"result {ret} {zh}")
    return ret, regular_word, zh
