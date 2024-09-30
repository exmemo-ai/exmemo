import os
import re
import json
import chardet
from chardet.universaldetector import UniversalDetector
from langdetect import detect
import tiktoken


def create_dir(dir_path, debug=False):
    """
    Create Directory
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    else:
        if debug:
            print(dir_path, "is already exist")


def get_basename(path):
    """
    Get the file name without the extension
    """
    filename = os.path.basename(path)
    return ".".join(filename.split(".")[:-1])


def write_file(path, text, ftype="w", debug=False):
    """
    Write content to a file
    """
    with open(path, ftype) as f:
        if debug:
            print("write", len(text))
        f.write(text)
        f.close()


def read_file_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def check_language(text, debug=False):
    """
    Determine if text is Chinese/English/Mixed
    """
    # Use regular expressions to check for Chinese characters
    chinese_pattern = re.compile(r"[\u4e00-\u9fa5]")
    chinese_match = chinese_pattern.findall(text)

    # Use regular expressions to check for English characters
    english_pattern = re.compile(r"[a-zA-Z]")
    english_match = english_pattern.findall(text)

    if debug:
        print("ch string", len(chinese_match), "en string", len(english_match))

    if len(chinese_match) > len(english_match) * 2:
        # A Chinese document is considered a Chinese document if it contains 80% or more Chinese characters, even though it may contain some English words.
        return "zh"
    elif len(chinese_match) > 0 and len(english_match) > 0:
        # Includes Chinese and English
        return "mix"
    elif len(english_match) > 0:
        # English only
        return "en"
    else:
        return "unknow"


def check_file_language(path, debug=True):
    with open(path, errors="ignore") as fp:
        text = fp.read()
        fp.close()
        return check_language(text, debug=debug)
    return "UNKNOWN"


def change_extension(file_path, new_extension=".txt"):
    """
    Change Extension
    """
    base_name, old_extension = os.path.splitext(file_path)
    return base_name + new_extension


def get_value_from_json(json_str, keyword=None):
    try:
        json_str = json_str.replace("'", '"')
        json_str = json_str.replace("False", '"False"')
        json_str = json_str.replace("True", '"True"')
        json_str = json_str.replace("None", '"None"')
        json_str = json_str.replace("null", '"null"')
        json_str = json_str.replace("false", '"false"')
        json_str = json_str.replace("true", '"true"')
        json_str = json_str.replace("none", '"none"')
        dic = json.loads(json_str)
        if keyword is None:
            return dic
        return dic[keyword]
    except Exception as e:
        print(e.with_traceback())
        return None


def detect_encoding(file_path):
    with open(file_path, "rb") as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        file.close()
        if result["encoding"] is None:
            return detect_encoding_2(file_path)
        return result["encoding"]
    return None


def detect_encoding_2(file_path):
    detector = UniversalDetector()
    with open(file_path, "rb") as file:
        for line in file:
            detector.feed(line)
            if detector.done:
                break
    detector.close()
    return detector.result["encoding"]


def detect_encoding_by_data(raw_data):
    result = chardet.detect(raw_data)
    return result["encoding"]


def check_language_by_data(text):
    """
    Determine the language of the text
    """
    try:
        return detect(text)
    except Exception as e:
        print("detect language error", e)
        return "UNKNOWN"


def count_tokens(string, model_name="gpt-3.5-turbo"):
    """
    Count the number of tokens
    """
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(string))


def count_file_token(path, model_name="gpt-3.5-turbo"):
    """
    Count the number of tokens in the file
    """
    with open(path, errors="ignone") as fp:
        data = fp.read()
        enc = tiktoken.encoding_for_model(model_name)
        count = len(enc.encode(data))
        return count
    return -1


def get_all_files(dir_path, ext):
    """
    Get all markdown files in the directory
    :param dir_path:
    :return:
    """
    md_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(ext):
                md_files.append(os.path.join(root, file))
    return md_files  # Return the paths of all markdown files


def count_embedding_cost(dir_path, debug=False):
    """
    Calculate the cost of embedding
    demo: count_embedding_cost('/exports/share/notes/notes_work/')
    """
    ll = get_all_files(dir_path, ".md")
    total = 0
    for path in ll:
        ret = count_file_token(path)
        if debug:
            print(path, ret)
        total += ret

    print(_("total_{len_files}_files").format(len_files=len(ll)))
    print(_("total_{total}_tokens").format(total=total))
    print(
        _("embedding_costs_about_{cost}_yuan").format(
            cost=round(total / 1000 * 0.0001 * 7, 2)
        )
    )
