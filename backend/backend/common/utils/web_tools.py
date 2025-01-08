from bs4 import BeautifulSoup
import re
import os
import json
import html2text

from loguru import logger
import mistune
import frontmatter
from mistune import HTMLRenderer
import requests

from django.utils.translation import gettext as _
import backend.common.files.filecache as filecache
import backend.common.files.utils_file as utils_file
from backend.common.llm.llm_hub import llm_query

DEFAULT_TITLE = _("unknown_title")


def get_text_extract(uid, content, limit=2000, debug=False):
    """
    Extract the main content from the text
    """
    try:
        if len(content) > limit:
            lang = utils_file.check_language(content)
            if lang == "en":
                content = content[: limit * 4]
            else:
                content = content[:limit]
            content = content[:limit]
        logger.info(f"get_text_extract: {content[:50]}, len {len(content)}")
        if len(content) == 0:
            return _("empty_file_content")
        sys_info = "You are a secretary, and your master is a knowledge worker."
        text = "Please automatically extract the main summary of the following text in Chinese, limited to within 200 characters. The content is as follows: {content}".format(
            content=content
        )
        ret, answer, detail = llm_query(
            uid, sys_info, text, "web", debug=debug
        )
        if ret:
            return answer
    except Exception as e:
        print("failed", e)
    return None


def get_file_extract(uid, path, debug=False):
    """
    Extract main content from the file, not yet called
    """
    try:
        content = read_md_content(path)
        return get_text_extract(uid, content, debug=debug)
    except Exception as e:
        print("failed", e)
    return None


def get_web_title(path, from_content=True):
    """
    Get Web Page Information
    """
    with open(path, "r", errors="ignore") as file:
        file_content = file.read()
        soup = BeautifulSoup(file_content, "html.parser")
        if soup.title is not None and soup.title.string is not None:
            title = soup.title.string
            return title.strip()
        else:
            text = soup.get_text()
            if text is not None:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if len(lines) > 0:
                    title = lines[0]
                    if len(title) > 10:
                        parts = re.split("[,.!?，。！？]", title)
                        if len(parts[0]) >= 3:
                            title = parts[0]
                    if len(title) > 20:
                        title = title[:20] + "..."
                    return title
    return DEFAULT_TITLE

def get_url_content(url, format='text'):
    logger.info(f"get_url_content {url}")
    if url is not None:
        try:
            ret, base_path = download_file(url)
            logger.debug(f"download {url}, base_path {base_path}")
            if ret:
                ext = os.path.splitext(base_path)[1][1:]
                logger.debug(f"ext {ext}")
                if ext == "html":
                    return get_web_title(base_path), get_html_content(base_path, format)
                if ext == "pdf":
                    return "pdf", _("parsing_content_is_not_supported_at_this_time")
        except Exception as e:
            logger.warning(f"get_url_content failed {e}")
    return None, None


def regular_url(url):
    url = re.sub(r"&amp;$", "", url)
    url = re.sub(r"&?sharer_shareinfo_first=[^&]*", "", url)
    url = re.sub(r"&amp;$", "", url)
    url = re.sub(r"&?sharer_shareinfo=[^&]*", "", url)
    url = re.sub(r"&amp;$", "", url)
    url = re.sub(r"&amp;", "&", url)
    return url


def read_md_content(path):
    """
    Read the content of the md file
    """
    if os.path.exists(path):
        with open(path) as fp:
            md = frontmatter.load(fp)
            markdown = mistune.create_markdown(renderer=HTMLRenderer())
            html = markdown(md.content)
            soup = BeautifulSoup(html, features="html.parser")
            return soup.get_text()
    return _("failure_reading_file")


def download_file(url, debug=False):
    """
    download file by url
    """
    path = filecache.TmpFileManager.get_instance().get_file_by_key("url", url)
    if path is not None:  # has been downloaded
        return True, path

    logger.debug(f"real download_file: {url}")
    # Pretend to be a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; V2005A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/123.0.6312.118 Mobile Safari/537.36 VivoBrowser/20.8.0.0"
    }
    try:
        r = requests.get(
            url, headers=headers, timeout=10
        )  # in case the timeout takes up too much time
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout occurred while trying to download {url}")
        return False, "error " + "Timeout"
    except (
        Exception
    ) as e:  # Exception caused by SSL certificate error leading to connection failure
        error_mes = str(e)
        first_colon_index = error_mes.find(":")
        if first_colon_index != -1:
            result = error_mes[:first_colon_index]
        else:
            result = error_mes
        return False, "error " + result
    if r.status_code == 200:
        if debug:
            logger.debug(f"parse_url: {url}")

        content_type = r.headers.get("Content-Type", "").lower()
        if any(
            mime in content_type
            for mime in ["text/html", "application/xhtml+xml", "application/xml"]
        ):
            ext = ".html"
        elif "application/pdf" in content_type:
            ext = ".pdf"
        else:
            logger.info("add web unsupport type {content_type}")
            return False, f"error not support type {content_type}"
        if debug:
            logger.debug("download type ", ext)
        base_path = filecache.get_tmpfile(ext)
        with open(base_path, "wb") as f:
            f.write(r.content)
        filecache.TmpFileManager.get_instance().add_file(base_path, {"url": url})
        return True, base_path
    else:
        logger.debug(f"parse_url: failed {url}, code {r.status_code}")
        return False, f"error {r.status_code}"


def get_web_abstract(uid, url):
    """
    Get Webpage Summary
    """
    path = filecache.TmpFileManager.get_instance().get_file_by_key("url", url)
    if path is not None:
        info = filecache.TmpFileManager.get_instance().get_file_info(path)
        if info is not None and "abstract" in info and len(info["abstract"]) > 0:
            return info["abstract"]
    title, content = get_url_content(url)
    content_show = content.replace("\n", " ")
    logger.debug(f"get_web_abstract: {title[:20]} {content_show[:20]}")
    detail = get_text_extract(uid, content, limit=4000, debug=False)

    if detail is not None:
        path = filecache.TmpFileManager.get_instance().get_file_by_key("url", url)
        filecache.TmpFileManager.get_instance().set_file_info(path, "abstract", detail)
        return detail
    return None


def visit_all(dic, debug=False):
    # Recursively visit all key-value pairs in a dictionary. If the value is html, extract the text from it.
    ret = {}
    for key, value in dic.items():
        if isinstance(value, dict):
            ret.update(visit_all(value))
        else:
            # check if value is html
            if isinstance(value, str) and re.match(r"<.*?>", value):
                soup = BeautifulSoup(value, "html.parser")
                if debug:
                    print("inner html", soup.text[:100])
                ret[key] = soup.text
    return ret


def get_html_content(path, format):
    """
    Get content from HTML file
    Args:
        path: HTML file path
        format: Output format, 'text' or 'markdown'
    Returns:
        str: Formatted content
    """
    ret = {}
    with open(path, "r", errors="ignore") as file:
        file_content = file.read()
        soup = BeautifulSoup(file_content, "html.parser")
        
        if format == 'markdown':
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_tables = False
            text = h.handle(str(soup))
        else:
            text = soup.get_text()
            text = re.sub(r"\n+", "\n", text)
            
        if text is not None:
            ret[_("body")] = text
            
        # Handle embedded JSON in scripts
        scripts = soup.find_all("script")
        for script in scripts:
            string = script.string
            if string is not None and len(string) > 0:
                string_pattern = re.compile(r"({.*})")
                arr_json = string_pattern.findall(string)
                for str_json in arr_json:
                    try:
                        dic = json.loads(str_json)
                        visited_dic = visit_all(dic)
                        if format == 'markdown':
                            # Convert HTML in JSON to markdown
                            markdown_dic = {}
                            for k, v in visited_dic.items():
                                markdown_dic[k] = h.handle(v) if isinstance(v, str) else v
                            ret.update(markdown_dic)
                        else:
                            ret.update(visited_dic)
                    except Exception as e:
                        print("--", e)

    # Combine all sections
    ret_string = ""
    for key, value in ret.items():
        if format == 'markdown':
            ret_string += f"{value}\n\n"
        else:
            ret_string += f"{key}\n{value}\n\n"
    
    return ret_string

# for test
# print(get_html_content('/tmp/files/20240808_122110.html'))
