import re
import json
import datetime
from loguru import logger
from babel import Locale
import mistune

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
    if dic is None:
        return None
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
    
def normalize_markdown_text(text):
    """
    Normalize markdown text by removing unnecessary line breaks while preserving markdown formatting
    """
    markdown = mistune.create_markdown()
    ast = markdown.parse(text)
    def is_special_block(block):
        return block['type'] in [
            'code', 'code_block', 'block_quote', 'list', 
            'list_item', 'heading', 'thematic_break',
            'table'
        ]

    def process_block(block):
        if is_special_block(block):
            return block
        
        if block['type'] == 'paragraph':
            text = block.get('text', '')
            
            # 保留以下情况的换行：
            # 1. 行尾有两个或以上空格（markdown强制换行）
            # 2. 以 |、-、* 开头的行（可能是表格或列表）
            # 3. 以 > 开头的行（引用）
            lines = text.split('\n')
            processed_lines = []
            
            for i, line in enumerate(lines):
                if (i > 0 and  # 不是第一行
                    not line.strip().startswith(('|', '-', '*', '>')) and  # 不是特殊行
                    not lines[i-1].endswith('  ')):  # 上一行不是强制换行
                    processed_lines.append(' ' + line.strip())
                else:
                    processed_lines.append(line)
            
            block['text'] = ''.join(processed_lines)
        
        return block

    def process_ast(ast_tree):
        for item in ast_tree:
            if isinstance(item, dict):
                process_block(item)
                if 'children' in item:
                    process_ast(item['children'])

    process_ast(ast)
    markdown = mistune.create_markdown()
    normalized_text = markdown(text)
    normalized_text = re.sub(r'\n{3,}', '\n\n', normalized_text)
    
    return normalized_text