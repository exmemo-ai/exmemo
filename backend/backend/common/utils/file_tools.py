import os
import frontmatter
from loguru import logger

from backend.common.parser import converter

import backend.common.files.filecache as filecache
from backend.common.files import utils_file
from backend.common.utils.web_tools import get_text_extract


def get_ext(path):
    """
    Get File Extension
    """
    arr = path.split(".")
    if len(arr) > 1:
        ext = arr[-1].lower()
        return "." + ext
    else:
        return ""


def is_audio_file(path):
    ext = get_ext(path)
    if ext in [".mp3", ".wav", ".m4a"]:
        return True
    return False


def is_doc_file(path):
    ext = get_ext(path)
    if ext in [".txt", ".pdf", ".html", ".mobi", ".epub", ".doc", ".docx", ".md"]:
        return True
    return False


def is_image_file(path):
    ext = get_ext(path)
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]:
        return True
    return False


def support_file(path):
    """
    Determine if the file is supported
    """
    if is_audio_file(path):
        return True
    if is_doc_file(path):
        return True
    if is_image_file(path):
        return True
    return False


def parse_file_type(path):
    ext = get_ext(path)
    return ext


def is_plain_text(path):
    """
    Determine if the file is plain text
    """
    ext = get_ext(path)
    if ext in [".txt", ".md"]:
        return True
    return False


def get_content_type(path):
    """
    Get the Content-Type of the file
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".md":
        return "text/plain"
    if ext == ".txt":
        return "text/plain"
    if ext == ".pdf":
        return "application/pdf"
    if ext == ".html":
        return "text/html"
    if ext == ".doc":
        return "application/msword"
    if ext == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if ext == ".excel":
        return "application/vnd.ms-excel"
    return "application/octet-stream"


def convert_to_md(base_path, md_path=None, force=False, use_ocr=False):
    """
    Convert the file to markdown
    """
    if md_path is None:
        md_path = utils_file.change_extension(base_path, ".md")
    ret = True
    if force or not os.path.exists(md_path):
        ret = converter.convert(base_path, md_path, force=force, use_ocr=use_ocr)
        filecache.TmpFileManager.get_instance().add_file(md_path)
    return ret, md_path


def get_file_content(data):
    """
    Get file content
    """
    if not isinstance(data, tuple):
        return False, None, None, None
    base_path = data[0]
    if base_path is None:
        return False, None, None, None
    ret, md_path = convert_to_md(base_path)
    title = os.path.basename(base_path)
    title = os.path.splitext(title)[0]
    try:
        with open(md_path, "r", encoding="utf-8") as fp:
            md = frontmatter.load(fp)
            return True, base_path, title, md.content
    except Exception as e:
        logger.debug(f"get_file_content: failed {e}")
        return False, base_path, None, None


def get_file_abstract(data, uid):
    """
    Summary of file content, retrieved from cache, mainly used for file summary in WeChat
    """
    ret, path, title, content = get_file_content(data)
    logger.warning(f"get_file_abstract: {ret}, {path}, {title}")
    if ret:
        info = filecache.TmpFileManager.get_instance().get_file_info(path)
        logger.warning(f"info: {info}")
        if info is not None and "abstract" in info and info["abstract"] is not None:
            return True, info["abstract"]
        detail = get_text_extract(uid, content)
        if detail is not None:
            filecache.TmpFileManager.get_instance().set_file_info(
                path, "abstract", detail
            )
            return True, detail
    return False, ""
