import os
import re
import traceback
import datetime
import hashlib
import yaml
import pandas as pd
import mistune
import frontmatter


def get_pure_text(text):
    """
    Remove special characters from the text
    """
    text = text.replace("### ", "")
    text = text.replace("## ", "")
    text = text.replace("# ", "")
    text = re.sub(r"<!--(.*?)-->", "", text, flags=re.DOTALL)
    text = re.sub(r"{.underline}", "", text, flags=re.DOTALL)
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return text


def markdown_gettext(x):
    """
    Get the text contained in the element
    Args:
        x: mistune markdown element
    """
    ret = ""
    if "children" in x:
        ret = "".join([markdown_gettext(y) for y in x["children"]])
    elif "raw" in x:
        ret = x["raw"]
    elif "type" in x and x["type"] == "softbreak":
        ret = "\n"
    ret = get_pure_text(ret)
    return ret


def check_link(x):
    """
    Check if it's a link
    """
    # print('check_link', x)
    if "type" in x and x["type"] == "link":
        # print('has link')
        return True
    elif "children" in x:
        return any([check_link(y) for y in x["children"]])
    return False


def get_file_md5(path):
    with open(path, "rb") as file:
        data = file.read()
    md5 = hashlib.md5(data).hexdigest()
    return md5


def get_front_matter(info_path, info=None):
    """
    Extract raw file information
    """
    if info_path.lower().endswith(".docx"):
        fileformat = "docx"
    elif info_path.lower().endswith(".pdf"):
        fileformat = "pdf"
    elif info_path.lower().endswith(".doc"):
        fileformat = "doc"
    elif info_path.lower().endswith(".epub"):
        fileformat = "epub"
    elif info_path.lower().endswith(".mobi"):
        fileformat = "mobi"
    elif info_path.lower().endswith(".html"):
        fileformat = "html"
    elif info_path.lower().endswith(".txt"):
        fileformat = "txt"
    else:
        fileformat = "other_format"

    front_matter_dic = {
        "file_name": os.path.basename(info_path),
        "file_size": os.path.getsize(info_path),
        "file_md5": get_file_md5(info_path),
        "file_format": fileformat,
        "convert_date": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    if info is not None:
        front_matter_dic.update(info)
    return front_matter_dic


def write_front_matter(fp, fm):
    front_matter = yaml.dump(fm, sort_keys=False, allow_unicode=True)
    fp.write("---\n")
    fp.write(front_matter)
    fp.write("---\n")
    fp.write("\n")
    fp.flush()


def parse_front_matter(markdown_text, debug=False):
    """
    Parse the front matter of a markdown document
    """
    try:
        pattern = re.compile(r"---\n(.*?)\n---\n", re.DOTALL)
        matches = pattern.search(markdown_text)
        if matches:
            front_matter_data = yaml.safe_load(matches.group(1))
            body = re.sub(pattern, "", markdown_text)
            if debug:
                print("Front Matter:")
                print(front_matter_data)
                print("Markdown Content:")
                print(body[:100])
            return front_matter_data, body
    except Exception as e:
        print("parse md header failed", e)
        traceback.print_exc()
    return None, markdown_text


def table_to_md(df):
    # Check if df.columns is empty

    if len(df) == 0:
        return ""
    is_default_index = all(str(column) == str(i) for i, column in enumerate(df.columns))
    table = "|"
    if is_default_index:
        table += "|".join(map(str, df.iloc[0])) + "|"
    else:
        table += "|".join(df.columns) + "|"
    table += "\n|"

    table += "|".join(["---"] * len(df.columns)) + "|"
    table += "\n"

    for idx, row in df.iterrows():
        if is_default_index and idx == 0:
            continue
        table += "|"
        table += "|".join(map(str, row)) + "|"
        table += "\n"

    return table


def table_from_md(token):
    header = []
    rows = []
    for c in token["children"]:
        if c["type"] == "table_head":
            for cell in c["children"]:
                header.append(markdown_gettext(cell))
        else:
            for b in c["children"]:
                if b["type"] == "table_row":
                    row = []
                    for cell in b["children"]:
                        row.append(markdown_gettext(cell))
                    if len(row) > 0:
                        rows.append(row)
    return pd.DataFrame(rows, columns=header)


def markdown_to_html(md_file_path, html_file_path):
    """
    Convert markdown files to html files
    """
    with open(md_file_path, "r") as f:
        post = frontmatter.load(f)
        markdown = mistune.create_markdown()
        html = markdown(post.content)
        html_with_charset = '<meta charset="UTF-8">\n' + html

        with open(html_file_path, "w") as f:
            f.write(html_with_charset)
