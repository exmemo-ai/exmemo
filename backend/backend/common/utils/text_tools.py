import json
import datetime
from loguru import logger


def replace_chinese_punctuation_with_english(s):
    punctuation_dict = {
        "，": ",",
        "。": ".",
        "：": ":",
        "；": ";",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "？": "?",
        "！": "!",
    }
    trans_table = str.maketrans(punctuation_dict)
    return s.translate(trans_table)


def replace_fullwidth_numbers_with_halfwidth(s):
    numbers_dict = {
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
    }
    trans_table = str.maketrans(numbers_dict)
    return s.translate(trans_table)


def date_handler(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def convert_dic_to_json(dic):
    try:
        return json.dumps(dic, default=date_handler)
    except Exception as e:
        logger.warning(f"convert_dic_to_json failed {e}")
        return None
