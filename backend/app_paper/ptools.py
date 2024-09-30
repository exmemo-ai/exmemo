import os
import re
import json
import datetime
import pandas as pd
import frontmatter
import requests
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.parser import converter, pdf_parser, block
from backend.common.llm.llm_hub import llm_query
from backend.common.files import utils_file
from backend.common.files import filecache

from .paper_info import *

# Important Note: Different papers can present different architectures.
# Please summarize this paper in bullet points and structure the bullet points in different categories, out in Chinese.

PAPER_ROLE = "You are an academic research expert, primarily specializing in the fields of computer science and medicine."
PAPER_KEYWORDS = [
    "Abstract",
    "Introduction",
    "Background",
    "Related Work",
    "Method",
    "Experiment",
    "Conclusion",
    "Acknowledgements",
    "References",
]


def get_year(x):
    if pd.notnull(x["tags"]) and x["tags"].find("20") != -1:
        return x["tags"][x["tags"].find("20") : x["tags"].find("20") + 4]
    if pd.notnull(x["added_date"]):
        return x["added_date"][:4]
    return "unknown"


def fill_info(uid, item, parse_abstract=False, debug=False):
    """
    According to the title and abstract of the paper, fill in the Chinese title, Chinese abstract, Chinese keywords, and Chinese category structured information of the paper
    """
    ret = {}
    ret_tokens = 0
    if "title" in item:
        title = item["title"]
    else:
        title = None
    if "abstract" in item:
        abstract = item["abstract"]
    else:
        abstract = None

    if pd.notna(title):
        types = [
            _("natural_language_processing"),
            _("medicine"),
            _("computer_vision"),
            _("audio"),
            _("video"),
            _("reinforcement_learning_(rl)"),
            _("knowledge_map"),
            _("machine_learning"),
        ]

        text = "Please translate the thesis title, output only the translated Chinese content: {title}".format(
            title=title
        )
        ret, answer, detail = llm_query(uid, PAPER_ROLE, text, "paper", debug=True)
        total_tokens = detail["token_count"]
        ret["title_zh"] = answer
        ret_tokens += total_tokens

        if pd.isnull(abstract):
            text = 'Please classify the paper by its title. Paper title: "{title}", Categories: {types_str}. Please answer directly, for example: {example_type}'.format(
                title=title, types_str=",".join(types), example_type=types[0]
            )
        else:
            text = 'Please categorize the paper based on its title. Paper title: "{title}", Paper abstract: "{abstract}", Categories: {types}. Please respond directly, for example: {example}'.format(
                title=title,
                abstract=abstract[:1024],
                types=",".join(types),
                example=types[0],
            )
        ret, answer, detail = llm_query(uid, PAPER_ROLE, text, "paper", debug=True)
        total_tokens = detail["token_count"]
        ret["class"] = answer
        ret_tokens += total_tokens

    if parse_abstract and pd.notnull(abstract):
        ret1, total_tokens = parse_paper_abstract(uid, abstract, debug=debug)
        if debug:
            print("Answer: {ret1}".format(ret1=ret1))
            print(f"total_tokens: {total_tokens}")
        ret_tokens += total_tokens
        ret.update(ret1)

    return ret, ret_tokens


def get_status(tags):
    """
    Determine the reading status of a paper based on its tags
    """
    dic_map = {
        _("have_read"): [_("have_read")],
        _("unread"): [_("to_read"), _("unseen")],
        _("reading_section"): [
            _("unread"),
            _("watching"),
            _("watch_a_little"),
            _("reading_section"),
        ],
    }
    if pd.isnull(tags):
        return _("unknown")
    for key, value in dic_map.items():
        for x in value:
            if tags.find(x) != -1:
                return key
    return _("unknown")


def translate_text(uid, string, lang="zh-CN", debug=False):
    """
    Translation
    """
    if string is None or len(string.strip()) == 0:
        return {}, 0

    if lang == "zh-CN":
        lang = _("chinese")
    text = f"""
Please translate into {lang} and output only the translated {lang} content: '{string}'
"""
    if debug:
        print("req", text)

    ret, answer, detail = llm_query(uid, PAPER_ROLE, text[:4096], "paper", debug=True)
    return answer, detail["token_count"]


def test_translate_text():
    ret1, ret_all = translate_text("The quick brown fox jumps over the lazy dog.")
    print(ret1)
    print(ret_all)


def parse_paper_abstract(uid, string, debug=False):
    """
    Parse paper abstract
    demo: ret_dic, total_tokens = parse_paper_abstract(ablock.get_text())
    """
    if string is None or len(string.strip()) == 0:
        return {}, 0

    sys_info = "You are a paper reading expert robot, automatically collecting, extracting, and summarizing valid information for students from a paper learning perspective."
    ret_format = '{"purpose": "xxx", "method": "xxx", "result": "xxx"}'
    text = f"""
Please extract the following from the summary in the shortest, professional, and easy-to-understand language: purpose, method, experimental results.
Return in json format, content in Chinese, as follows: {ret_format}
Content is as follows: '{string}'
"""
    if debug:
        print("req", text)

    ret, answer, detail = llm_query(uid, sys_info, text[:4096], "paper", debug=True)
    try:
        answer = json.loads(answer)
    except Exception as e:
        print("failed", e)
        answer = {}
    return answer, detail["token_count"]


def get_doi_id(text):
    """
    take doi id
    """
    if text is None:
        return None
    if re.search("doi", text.lower()):
        return re.findall(r"\d+\.\d+", text)[0]


def get_arxiv_id(text):
    """
    Get arxiv_id
    """
    if text is None:
        return None
    if re.search("\d{4}\.\d{4,}", text.lower()):
        return re.findall(r"\d+\.\d+", text)[0]
    return None


def get_pdf_url(url):
    """
    Get the real URL of the PDF from the url variable
    """
    new_url = url
    id = None
    if re.search("arxiv", url.lower()) or re.match("\d{4}\.\d{4,}$", url):
        if re.match("^arxiv:\d{4}\.\d{4,}$", url.lower()):
            id = url.split(":")[1]
            new_url = f"https://arxiv.org/pdf/{id}.pdf"
        elif re.match("\d{4}\.\d{4,}$", url):
            id = url
            new_url = f"https://arxiv.org/pdf/{id}.pdf"
        else:
            if re.search("\d{4}\.\d{4,}", url.lower()):
                id = re.findall(r"\d+\.\d+", url)[0]
            if not url.startswith("http"):
                url = "https://" + url
            if url.startswith("https://arxiv.org/pdf/"):
                pass
            if url.startswith("https://arxiv.org/abs/"):
                new_url = re.sub(r"/abs/(\d+\.\d+)", r"/pdf/\1.pdf", url)
    else:
        id = os.path.basename(url)
        if id.endswith(".pdf"):
            id = id[:-4]
    return new_url, id


def test_get_pdf_url():
    print(get_pdf_url("https://arxiv.org/abs/2301.10405"))
    print(get_pdf_url("https://arxiv.org/pdf/2301.10405.pdf"))
    print(get_pdf_url("arxiv.org/abs/2301.10405"))
    print(get_pdf_url("2301.10405"))
    print(get_pdf_url("arXiv:2301.10405"))


def is_path(text):
    """
    Determine if text is a file path
    """
    if text is None:
        return False
    if text.startswith("/"):
        return True
    return False


def is_url(text):
    """
    Determine whether text is a URL
    """
    if text is None:
        return False
    if text.startswith("http"):
        return True
    return False


def is_arxiv(text):
    """
    Determine whether text is an arxiv URL
    """
    if text is None:
        return False
    if text.lower().find("arxiv") != -1:
        return True
    return False


def is_doi(text):
    """
    Determine whether text is a DOI id
    """
    if text is None:
        return False
    if text.lower().find("doi") != -1:
        return True
    return False


def get_paper(dir_path, addr, save=True, debug=False):
    """
    Download the paper pdf and convert it into an md file
    Args:
        dir_path: Directory to download the file
        addr: Address of the paper, can be a URL or an arXiv ID
        save: Whether to save the file
        debug: Whether to print debug information
    demo: get_paper("arXiv:2301.10405")
    """
    if os.path.exists(dir_path) == False:
        os.makedirs(dir_path)
    pdf_path = None
    url = None
    if is_path(addr):
        if not os.path.exists(addr):
            return pdf_path, url
        pdf_path = addr
        md_path = utils_file.change_extension(pdf_path, ".md")
    else:
        url, id = get_pdf_url(addr)
        if not is_url(url):
            return pdf_path, url
        pdf_path = os.path.join(dir_path, f"{id}.pdf")
        logger.info(f"pdf_path {pdf_path}")
        md_path = utils_file.change_extension(pdf_path, ".md")

        if not os.path.exists(pdf_path):
            if save:
                r = requests.get(url)
                if r.status_code == 200:
                    logger.debug(f"parse_url: {url}")
                content_type = r.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type:
                    # Write to pdf file
                    with open(pdf_path, "wb") as f:
                        f.write(r.content)
                else:
                    logger.error(
                        f"download: {url} failed: {r.status_code} {content_type}"
                    )
    if save and not os.path.exists(md_path) and os.path.exists(pdf_path):
        ret, detail = converter.convert(pdf_path, md_path, keywords=PAPER_KEYWORDS)
        filecache.TmpFileManager.get_instance().add_file(md_path)
        if not ret:
            logger.error(f"convert: {md_path} failed: {detail}")
    """
    parser = md_parser.MarkdownParser(md_path)
    if parser.fm is not None:
        item = {}
        if 'title' in parser.fm:
            item['title'] = parser.fm['title']
        if 'abstract' in parser.fm:
            item['abstract'] = parser.fm['abstract']
        paper_tools.fill_info(item, parse_abstract = False, debug = False)
        print(item)
    """
    if not os.path.exists(pdf_path):
        pdf_path = None
    return pdf_path, url


def parse_paper_info(uid, root_block, use_llm=True, debug=False):
    """
    Using a large model to parse paper information
    """
    info = {}
    ablock = block.get_block_by_heading(root_block, ["Abstract", _("abstract")])
    if ablock is not None:
        if use_llm:
            ret_dic, abstract_tokens = parse_paper_abstract(uid, ablock.get_text())
            if "purpose" in ret_dic:
                info["desc"] = ret_dic["purpose"][: pdf_parser.MAX_DESC_LEN]
                info["purpose"] = ret_dic["purpose"][: pdf_parser.MAX_DESC_LEN]
            if "method" in ret_dic:
                info["method"] = ret_dic["method"][: pdf_parser.MAX_DESC_LEN]
            if "result" in ret_dic:
                info["result"] = ret_dic["result"][: pdf_parser.MAX_DESC_LEN]
        info["abstract"] = ablock.get_text()

    if use_llm:
        info_title, title_tokens = parse_paper_title(
            uid, root_block.get_text(), debug=debug
        )
        print(f"### use_llm {info_title}")
        info.update(info_title)
    if debug:
        print(f"abstract_tokesn {abstract_tokens} + {title_tokens}")
    return info


def paper_info_to_ob(info):
    """
    Print paper information in obsidian format
    """
    ret = []
    print(f"doi: ''")
    if "venue" in info:
        ret.append(f"journal: {info['venue']}")
    else:
        ret.append(f"journal: ''")
    ret.append(f"status: {_('Unread')}")
    ret.append(f"tags:")
    ret.append(f"- {_('Paper Reading')}")
    if "title_zh" in info:
        ret.append(f"title: {info['title_zh']}")
    else:
        ret.append(f"title: ''")
    # Today Date
    datestr = datetime.datetime.now().strftime("%Y-%m-%d")
    ret.append(f"date: {datestr}")
    ret.append("")
    if "title" in info:
        ret.append(_("english_title_colon__{title}").format(title=info["title"]))
    else:
        ret.append(_("english_name_colon_"))
    if "title_zh" in info:
        ret.append(_("chinese_name_colon__{title_zh}").format(title_zh=info["title_zh"]))
    else:
        ret.append(_("chinese_name_colon_"))
    if "url" in info:
        ret.append(_("link_colon__{url}").format(url=info["url"]))
    else:
        ret.append(_("link_colon_"))
    ret.append(_("code_colon_"))
    if "author" in info:
        ret.append(_("author_colon__{author}").format(author=info["author"]))
    else:
        ret.append(_("author_colon_"))
    if "institution" in info:
        ret.append(
            _("institution_colon__{institution}").format(institution=info["institution"])
        )
    else:
        ret.append(_("institution_colon_"))
    if "published_date" in info:
        ret.append(
            _("date_colon__{published_date}").format(published_date=info["published_date"])
        )
    else:
        ret.append(_("date_colon_"))
    if "citations" in info:
        ret.append(_("citations_colon__{citations}").format(citations=info["citations"]))
    else:
        ret.append(_("number_of_citations_colon_"))
    ret.append("")
    ret.append("## " + _("abstract"))
    if "purpose" in info:
        ret.append(_("objective_colon__{purpose}").format(purpose=info["purpose"]))
    else:
        ret.append(_("target_colon_"))
    if "method" in info:
        ret.append(_("method_colon__{method}").format(method=info["method"]))
    else:
        ret.append(_("method_colon_"))
    if "result" in info:
        ret.append(_("conclusion_colon__{result}").format(result=info["result"]))
    else:
        ret.append(_("Conclusion:"))
    print("\r\n".join(ret))
    return "\r\n".join(ret)


def get_paper_info_from_pdf(path, debug=False):
    """
    Get information from the PDF paper
    demo: get_paper_info_from_pdf('/exports/tmp/media/files/20231215_102919.pdf', debug=False)
    """
    meta_info, _ = pdf_parser.PdfMeta.extract_pdf_info(path, debug=debug)
    content = None
    if debug:
        print("pdf meta_info", meta_info)
    md_path = path.replace(".pdf", ".md")
    if os.path.exists(md_path):
        with open(md_path, "r") as f:
            md = frontmatter.loads(f.read())
            if debug:
                print("md has keys", md.keys())
            if "title" in md.keys():
                meta_info["title"] = md["title"]
            if "abstract" in md.keys():
                meta_info["abstract"] = md["abstract"]
            if "purpose" in md.keys():
                meta_info["purpose"] = md["purpose"]
            if "method" in md.keys():
                meta_info["method"] = md["method"]
            if "result" in md.keys():
                meta_info["result"] = md["result"]
            content = md.content
    elif "title" not in meta_info:
        parser = pdf_parser.PDFParser(path, debug=debug)
        info = parser.get_meta_info()
        meta_info.update(info)
        content = parser.root_block.get_text()
    return meta_info, content


def parse_paper(
    uid,
    text,
    dst_dir,
    save=True,
    use_llm=False,
    use_trans=True,
    use_google=False,
    debug=False,
):
    """
    Parse the paper and store it in the database
    Args:
        text Supports: paper path, paper URL, doi, arxiv_id, paper title
    Return:
        Returns the paper information in the form of a dictionary

    Later:
        text could be path, url, title, should first check in the database, if found return directly
    """
    path, url = get_paper(dst_dir, text, save=save, debug=debug)
    info = {}
    title = None
    content = None
    arxiv_id = None
    if debug:
        print(f"path {path} url {url}")

    if path is not None and os.path.exists(path):
        info, content = get_paper_info_from_pdf(path, debug=debug)
        if "title" in info:
            title = info["title"]

    if is_url(url):
        info["url"] = url
        if is_arxiv(url):
            arxiv_id = get_arxiv_id(url)
            print("arxiv", arxiv_id)
    elif url is not None:
        title = url

    # Fetch information from arxiv
    if arxiv_id is not None:
        print("get_arxiv_info", arxiv_id)
        new_info = get_arxiv_info(arxiv_id)
        if new_info is not None:
            info.update(new_info)
        info.update()  # Not sure if this is correct, don't remember why I changed it this way
    elif title is not None:
        print("get_arxiv_info_by_title", title)
        new_info = info.update(get_arxiv_info_by_title(title))
        if new_info is not None:
            info.update(new_info)

    # Fetching from Google Scholar
    if title is not None and use_google:
        print("get_info_by_google", title)
        google_dic = get_info_by_google(title)
        if google_dic is not None:
            info.update(google_dic)

    try:
        if use_llm:
            if (
                content is not None
            ):  # Solve file headers with large models only if saved locally
                print("get_info_by_llm", len(content), content[:50].replace("\n", " "))
                ret_dic, tokens = parse_paper_title(uid, content, debug=debug)
                # if debug:
                print("parse_parer_title, token", tokens, "ret_dic", ret_dic)
                info.update(ret_dic)
            if "abstract" in info and "purpose" not in info:
                ret_dic, tokens = parse_paper_abstract(
                    uid, info["abstract"], debug=debug
                )
                info.update(ret_dic)

        if use_trans:
            if "title" in info and "title_zh" not in info:
                info["title_zh"], tokens = translate_text(uid, info["title"])
    except Exception as e:
        print("failed", e)
        import traceback

        traceback.print_exc()

    print(f"after parse_paper, info {info}")
    return paper_info_to_ob(info)


def gpt(uid, content, debug=False):
    """
    Direct question GPT
    """
    debug = True
    if content is None or len(content.strip()) == 0:
        return False, _("empty_contents")
    try:
        if debug:
            print("req", content)
        ret, answer, detail = llm_query(
            uid, PAPER_ROLE, content[:4096], "chat", debug=debug
        )
        return True, answer
    except Exception as e:
        return False, e


def polish(uid, content, debug=False):
    """
    Polish the paper information
    """
    if content is None or len(content.strip()) == 0:
        return False, _("empty_contents")
    try:
        text = "Please polish the following content: '{content}'".format(
            content=content
        )
        if debug:
            print("req", text)
        ret, answer, detail = llm_query(
            uid, PAPER_ROLE, text[:4096], "chat", debug=debug
        )
        return True, _(
            "Original text\n{content}\n=====================\nPolished text\n{answer}"
        ).format(content=content, answer=answer)
    except Exception as e:
        return False, e


def translate(uid, content):
    """
    Translating paper information
    """
    if content is None:
        return None, _("empty_contents")
    try:
        ret, token = translate_text(uid, content)
        return (
            True,
            _("Original Text")
            + "\n"
            + content
            + "\n=====================\n"
            + _("Translated Text")
            + "\n"
            + ret,
        )
    except Exception as e:
        return False, e
