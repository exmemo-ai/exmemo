import os
import re
import json
from easy_literature.arxiv import arxivInfo
from scholarly import scholarly, ProxyGenerator
from backend.common.llm.llm_hub import llm_query
from django.utils.translation import gettext as _

PAPER_ROLE = "You are a paper reading expert robot, automatically collecting, extracting, and summarizing effective information for students from the perspective of paper learning."


def match_markdown_links(line):
    pattern = r"- \[([^\[]+)\]\(([^)]+)\)"
    matches = re.findall(pattern, line)
    return matches


def get_title(string, debug=False):
    """
    Extract paper titles and authors information
    """
    lines = string.split("\n")
    lines_new = []
    for line in lines:
        if line == "table_of_contents" or line == _("table_of_contents"):
            continue
        if match_markdown_links(line):
            continue
        lines_new.append(line)
    string = "\n".join(lines_new)

    idx = string.find(_("abstract"))
    if idx == -1:
        idx = string.lower().find("abstract")
    if debug:
        print("abstract", idx)
    if idx != -1:
        return string[:idx]
    else:
        return string[:1000]


def parse_paper_title(uid, string, debug=False):
    """
    Parse the description at the beginning of the paper, include institution
    demo: ret_dic, total_tokens = parse_paper_title(xxx)
    """
    if string is None or len(string.strip()) == 0:
        return {}, 0
    string = get_title(string)

    ret_format = '{"title":"","title_zh":"","author":"","institution":""}'
    text = f"""
Below is the opening information of a paper, please return the information: English Title, Chinese Title (please translate the English Title to Chinese Title), Author, Institution; 
where institution names should be translated into Chinese and deduplicated into a comma-separated string in dictionary format, 
such as: {ret_format} Content as follows: '{string}'
"""
    if debug:
        print("req", text)

    rt, answer, detail = llm_query(uid, PAPER_ROLE, text[:4096], "paper", debug=debug)
    try:
        answer = json.loads(answer)
    except Exception as e:
        print("failed", e)
        print("ret", answer)
        answer = {}
    return answer, detail["token_count"]


def get_info_by_google(title, proxy=None, debug=False):
    """
    Get paper information from Google Scholar, submitted code 240119 this function is normal
    demo: get_info_by_google('Attention is all you need', proxy="192.168.10.106:12346")
    """
    try:
        pg = ProxyGenerator()
        if proxy is None:
            proxy = os.environ.get("HTTP_PROXY", None)
        if debug:
            print("proxy", proxy)
        pg.SingleProxy(http=proxy)
        scholarly.use_proxy(pg, ProxyGenerator())
        search_query = scholarly.search_pubs(title)
        if debug:
            print("search query", search_query)
        for idx, paper in enumerate(search_query):
            print("paper idx {idx}")
            dic = {}
            if "bib" in paper:
                dic = paper["bib"]
            if "pub_url" in paper:
                dic["url"] = paper["pub_url"]
            if "num_citations" in paper:
                dic["citations"] = paper["num_citations"]
            if "author" in dic and isinstance(dic["author"], list):
                dic["author"] = ", ".join(dic["author"])                
            if debug:
                print(paper)
            return dic
    except Exception as e:
        print("get_info_by_google", e)
        return {}
    if debug:
        print("found none")
    return {}


class MyArxivInfo(arxivInfo):
    def extract_json_info(self, item):
        dic = {}
        if "published" in item:
            dic["published_date"] = item["published"][:10]
        if "link" in item:
            dic["url"] = item["link"]
            dic["pdf_link"] = (item["link"].replace("abs", "pdf") + ".pdf",)
        if "summary" in item:
            dic["abstract"] = item["summary"]
        if "title" in item:
            dic["title"] = item["title"]
        if "authors" in item:
            dic["author"] = ", ".join([a["name"] for a in item["authors"]])
        # display(item)
        return dic


def get_arxiv_info(arxivId, proxy=None):
    """
    Get paper information from arxiv
    demo: print(get_arxiv_info("2208.05623"))
    """
    arxiv_info = MyArxivInfo()
    arxiv_info.set_proxy_handler(proxy=proxy)
    bib_arxiv = arxiv_info.get_info_by_arxivid(arxivId)
    print("bib_arxiv", bib_arxiv)
    return bib_arxiv


def get_arxiv_info_by_title(title, proxy=None, debug=False):
    """
    Get paper information from arxiv
    demo: print(get_arxiv_info_by_title("Attention is all you need", "http://192.168.10.106:12346", debug=True))
    """
    arxiv_info = MyArxivInfo()
    arxiv_info.set_proxy_handler(proxy=proxy)
    bib_arxiv = arxiv_info.get_info_by_title(title)
    if debug:
        print("get_arxiv_info_by_title ret", type(bib_arxiv), bib_arxiv)
    print("@@@@", bib_arxiv)
    if isinstance(bib_arxiv, list):
        if len(bib_arxiv) > 0:
            bib_arxiv = bib_arxiv[0]
        else:
            bib_arxiv = {}
    return bib_arxiv
