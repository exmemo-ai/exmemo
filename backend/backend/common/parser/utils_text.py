import re
import Levenshtein

MAX_BASE_HEADING_LEN = 40
MAX_KEYWORD_HEADING_LEN = 20
MAX_TOP_KEYWORD_HEADING_LEN = 40
MAX_MD_HEADING_LEN = 30
MAX_DOCX_NUM_HEADING_LEN = 20
STYLE_KEYWORD = 1000
STYLE_NONE = -1


def chinese_to_arabic(chinese_num, debug=False):
    """
    Convert Chinese numerals to Arabic numerals
    """
    if debug:
        print(chinese_num)
    chinese_num = chinese_num.strip()
    chinese_numerals = {
        "零": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "百": 100,
        "千": 1000,
        "万": 10000,
        "亿": 100000000,
    }

    result = 0
    partial_result = 0
    current_number = 0

    for char in chinese_num:
        if char in chinese_numerals:
            current_number = chinese_numerals[char]
            if current_number == 10 or current_number == 1000:
                if partial_result == 0:
                    partial_result = current_number
                else:
                    partial_result *= current_number
            else:
                partial_result += current_number
        else:
            result += partial_result
            partial_result = 0
        # print(result, partial_result, current_number)
    result += partial_result
    return result


EX_RULES = [r"^[\d.]+$"]

IN_RULES = [
    r"^目录",
    r"^[\d]+\.[\d]+\.[\d]+\.[\d]+",
    r"^[\d]+\.[\d]+\.[\d]+",
    r"^[\d]+\.[\d]+",
    r"^[\d.]+\s",
    # r'^[\d]+、', # 231109, Opening affects directory nesting
    r"^[\d.]{2,}",
    r"^[(（]*\d+[)）]*\s",
    # r'^[(（]+\d+[)）]+', # 231109，找开后影响目录嵌套
    r"^第[\d一二三四五六七八九十]+章",
    r"^第[\d一二三四五六七八九十]+条",
    r"^第[\d\.]+条",
    r"^[(（][一二三四五六七八九十]+[)）]",
    r"^附件[\d一二三四五六七八九十]+",
]


def is_keyword_title(line, keywords, max_length=MAX_KEYWORD_HEADING_LEN):
    if len(line) > max_length:  # Too long not as title
        return False
    if len(line) > max_length:
        if line[:max_length].find(":") == -1 and line[:max_length].find("：") == -1:
            return False
        line = line[:max_length]
    for keyword in keywords:
        if keyword in line:
            return True
    return False


def check_exclude(text, string, max_length=MAX_BASE_HEADING_LEN, debug=False):
    num_string = get_number_str(text)
    p = string.find("%")
    if (
        p != -1 and p < 10
    ):  # Percentage is not used as a title, percentage appears at the beginning
        return False
    if (
        max_length != -1 and len(string) > max_length
    ):  # If the title exceeds the limit, it will not be used as the title
        return False
    if (
        len(num_string) >= 3 and num_string.isdigit()
    ):  # Long numbers such as ID numbers, years, etc. are not used as titles
        return False
    if (
        count_decimal_places(num_string) >= 3
    ):  # If the number of decimal places is greater than 3, it is not used as a title
        return False
    for rule in EX_RULES:  # Only numbers, without titles, are not considered titles
        x = re.match(rule, string)
        if x is not None:
            if debug:
                print("ex rules", rule)
            return False
    return True


def is_base_title(text, max_length=MAX_BASE_HEADING_LEN, debug=False):
    """
    Use regex to determine if the title is numbered
    """
    text = text.replace("．", ".")
    for idx, rule in enumerate(IN_RULES):
        x = re.match(rule, text)
        if x is not None:
            string = x.group()
            if debug:
                print("before, exclude", string, text)
            if check_exclude(string, text, max_length=max_length, debug=debug):
                return True, string, idx
    return False, None, -1


def count_decimal_places(input_string):
    """
    Get the number of decimal places
    """
    # Use regular expressions to match decimal parts
    match = re.search(r"\.(\d+)", input_string)

    if match:
        decimal_part = match.group(1)
        return len(decimal_part)
    else:
        # If no fractional part is matched, return 0
        return 0


def get_number_str(text, debug=False):
    # Extracting Numbers in Sequence Numbers
    # print(text)
    x = re.findall(r"[一二三四五六七八九十]+", text)
    if len(x) > 0:
        return str(chinese_to_arabic(x[0], debug=debug))
    x = re.findall(r"[\d]+\.[\d]+\.[\d]+\.[\d]+", text)
    if len(x) > 0:
        return x[0]
    x = re.findall(r"[\d]+\.[\d]+\.[\d]+", text)
    if len(x) > 0:
        return x[0]
    x = re.findall(r"[\d]+\.[\d]+", text)
    if len(x) > 0:
        return x[0]
    x = re.findall(r"[\d]+", text)
    if len(x) > 0:
        return x[0]
    return text


def test_get_detail():
    print(get_number_str("第十一条", debug=True))
    print(get_number_str("第五十九章", debug=True))
    print(get_number_str("第五条", debug=True))
    print(get_number_str("1", debug=True))
    print(get_number_str("(1)", debug=True))
    print(get_number_str("附件二", debug=True))
    print(get_number_str("1.2", debug=True))
    print(get_number_str("1.2.3", debug=True))
    print(get_number_str("1.2.3.4", debug=True))


def compare_number_str(a, b, debug=False):
    """
    Compare the size of two numeric strings
    """
    if debug:
        print(a, ">", b)
    if a == b:
        return 0
    try:
        if isinstance(a, str) and isinstance(b, str):
            a = a.split(".")
            b = b.split(".")
            if len(a) != len(b):  # Unable to compare
                return None
            for i in range(len(a)):
                if i == len(a) - 1:  # Compared to last place only
                    if int(a[i]) > int(b[i]):
                        return 1
                    elif int(a[i]) < int(b[i]):
                        return -1
                else:
                    if int(a[i]) != int(b[i]):  # Skip Unable to Compare
                        return None
    except Exception as e:
        print(e)
        # traceback.print_exc()
    return None


def test_compare_number_str():
    print("  ret", compare_number_str("1", "2", debug=True))
    print("  ret", compare_number_str("2", "1", debug=True))
    print("  ret", compare_number_str("19", "2", debug=True))
    print("  ret", compare_number_str("1.1", "1", debug=True))
    print("  ret", compare_number_str("1.2", "1.5", debug=True))


def number_to_letter(number):
    if isinstance(number, int) and 1 <= number <= 26:
        letter = chr(ord("a") + number - 1)
        return f"({letter})"
    else:
        return f"({number})"


def number_to_roman(number):
    if isinstance(number, int) and 1 <= number <= 100:
        roman_numerals = {
            1: "i",
            2: "ii",
            3: "iii",
            4: "iv",
            5: "v",
            6: "vi",
            7: "vii",
            8: "viii",
            9: "ix",
            10: "x",
            20: "xx",
            30: "xxx",
            40: "xl",
            50: "l",
            60: "lx",
            70: "lxx",
            80: "lxxx",
            90: "xc",
            100: "c",
        }

        if number in roman_numerals:
            return f"({roman_numerals[number]})"
        else:
            tens_digit = number // 10 * 10
            ones_digit = number % 10
            return f"({roman_numerals[tens_digit]},{roman_numerals[ones_digit]})"
    else:
        return f"({number})"


def calc_index_by_level(parent_num, current_num):
    if parent_num == "":
        return f"{current_num}"
    if re.match(r"\d+", parent_num):
        return f"({current_num})"
    if re.match(r"\(\d+\)", parent_num):
        return number_to_letter(current_num)
    if re.match(r"\([ivx]+\)", parent_num):
        return "*"
    if re.match(r"\([a-z]\)", parent_num):
        return number_to_roman(current_num)


def get_index_str(text):
    p = text.find(" ")
    if p != -1:
        return text[:p]
    return text


def get_index_level(text):
    """
    Get the level of the title
    """
    if text is None:
        return 0
    text = get_index_str(text)
    arr = text.split(".")
    arr = [x for x in arr if x != ""]  # xieyan 231108 add
    return len(arr)


def get_real_index(text):
    """
    Extract the real number from the title
    """
    # At least one number
    if text is None:
        return []
    ret, _, _ = is_base_title(text, max_length=-1)
    if not ret:
        return []
    text = get_index_str(text)
    arr = text.split(".")
    if len(arr) > 1:
        return arr
    num = get_number_str(text)
    return [num]


def calc_similarity(str1, str2):
    """
    Calculate the similarity between two strings
    """
    distance = Levenshtein.distance(str1, str2)
    max_length = max(len(str1), len(str2))
    similarity = 1 - (distance / max_length)
    return similarity
