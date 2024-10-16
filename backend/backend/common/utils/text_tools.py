import re
import json
import datetime
from loguru import logger
from babel import Locale

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

def parse_json(string):
    '''
    Convert a JSON string into a dict, supporting multiline JSON strings.
    demo: parse_json("""
    {
        "ctype": "Knowledge Technology", 
        "atype": "Subjective", 
        "status": "Pending Organization"
    }
    """)
    '''
    if isinstance(string, dict):
        return string

    try:
        # Match the content within curly braces and remove leading/trailing whitespace
        match = re.search(r'{.*}', string, re.DOTALL)
        if match is not None:
            string = match.group().strip()
            string = string.replace("'", '"')
            return json.loads(string, strict=False)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
    except Exception as e:
        print(f"Error in parsing JSON: {e}")
    try:
        return eval(string)
    except Exception as e:
        print(f"Error in eval: {e}")
        return {}


def get_language_name(language_code):
    try:
        base_language_code = language_code.split('-')[0]
        locale = Locale.parse(base_language_code)
        return locale.get_display_name()
    except Exception as e:
        logger.warning(f"Error: {e}")
        return None