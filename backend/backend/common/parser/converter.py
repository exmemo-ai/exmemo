import os
import mistune
from bs4 import BeautifulSoup
from django.utils.translation import gettext as _

from .doc_parser import DOCParser
from .docx_parser import DOCXParser
from .pdf_parser import PDFParser
from .mobi_parser import MOBIParser
from .epub_parser import EPUBParser
from .txt_parser import TxtParser
from .html_parser import HtmlParser
from . import utils_md as tools_md
from backend.common.files import utils_file as utils_file


def markdown_to_txt(path_in, path_out):
    """
    Convert markdown to txt, remove all links
    demo:
        path_in = '/exports/books/2024/Prediction_Algorithms.md'
        path_out = '/exports/books/2024/Prediction_Algorithms.txt'
        markdown_to_txt(path_in, path_out)
    """
    with open(path_in, "r") as file:
        md_content = file.read()

    html_content = mistune.markdown(md_content)
    soup = BeautifulSoup(html_content, "html.parser")
    for a in soup.findAll("a"):  # Remove all links
        a.replaceWithChildren()
    text_content = soup.get_text()
    with open(path_out, "w") as file:
        file.write(text_content)


def is_markdown(path):
    """
    Determine whether the file is a markdown
    """
    if path.lower().endswith(".md"):
        return True
    return False


def is_support(path):
    """
    Determine if the file is supported
    """
    if path.lower().endswith(".docx"):
        return True
    if path.lower().endswith(".doc"):
        return True
    if path.lower().endswith(".pdf"):
        return True
    if path.lower().endswith(".mobi"):
        return True
    if path.lower().endswith(".epub"):
        return True
    if path.lower().endswith(".txt"):
        return True
    if path.lower().endswith(".html"):
        return True
    return False


def convert(path_in, path_out, **kwargs):
    """
    Convert docx file to markdown format
    """
    force = kwargs.get("force", False)
    keywords = kwargs.get("keywords", None)
    debug = kwargs.get("debug", False)

    if os.path.exists(path_out) and not force:
        return True, "file exists"

    if path_in.lower().endswith(".docx"):
        parser = DOCXParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".doc"):
        parser = DOCParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".pdf"):
        parser = PDFParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".mobi"):
        parser = MOBIParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".epub"):
        parser = EPUBParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".txt"):
        parser = TxtParser(path_in, with_parse=False, **kwargs)
    elif path_in.lower().endswith(".html"):
        parser = HtmlParser(path_in, with_parse=False, **kwargs)
    else:
        return False, "failed: not support " + path_in

    if keywords is not None:
        parser.set_keywords(keywords)
    parser.root_block = parser.parse(parser.data, debug=debug)
    info = parser.get_meta_info()

    if parser.root_block is not None:
        parser.fm = tools_md.get_front_matter(path_in, info=info)
        parser.save(path_out)
        return True, "success"
    return False, "failed: parser is None"


# Please write a few test cases in standard format
if __name__ == "__main__":
    in_path = "/exports/books/2023/Addiction.pdf"
    out_path = utils_file.change_(in_path, ".txt")
    convert(in_path, out_path, force=True, debug=False)
