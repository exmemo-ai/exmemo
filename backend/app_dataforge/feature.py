import os
import re
import pandas as pd
import traceback
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.llm.llm_hub import llm_query, llm_query_json
from backend.settings import BASE_DATA_DIR
from .prompt import PROMPT_CLASSIFY, PROMPT_TITLE
from backend.common.utils.text_tools import get_language_name
from backend.common.utils.file_tools import convert_to_md
from backend.common.utils.web_tools import read_md_content, get_web_title, download_file
from backend.common.utils.text_tools import replace_chinese_punctuation_with_english
from backend.settings import LANGUAGE_CODE

DEFAULT_CATEGORY = _("unclassified")
DEFAULT_STATUS = "init"
RECORD_ROLE = "You are a personal assistant, and your master is a knowledge worker."
TITLE_LENGTH = 20

class EntryFeatureTool:
    _instance = None

    @staticmethod
    def get_instance():
        if EntryFeatureTool._instance is None:
            EntryFeatureTool._instance = EntryFeatureTool()
        return EntryFeatureTool._instance

    def __init__(self):
        if LANGUAGE_CODE.lower().find("zh") >= 0:
            path = os.path.join(BASE_DATA_DIR, "record_keyword_zh.xlsx")
        else:
            path = os.path.join(BASE_DATA_DIR, "record_keyword_en.xlsx")
        self.df_record = pd.read_excel(path, sheet_name="record")
        self.df_web = pd.read_excel(path, sheet_name="web")
        # display(self.df_note)
        self.calist = self.get_all_categories(
            debug=True
        )  # Only manual records may have prefix descriptions

    def parse(self, dic, content, use_llm=True, debug=False):
        # from input params
        if "ctype" not in dic or pd.isnull(dic["ctype"]) or len(dic["ctype"]) == 0:
            dic["ctype"] = None
        if "status" not in dic or pd.isnull(dic["status"]) or len(dic["status"]) == 0:
            dic["status"] = None
        if "atype" not in dic or pd.isnull(dic["atype"]) or len(dic["atype"]) == 0:
            dic["atype"] = None
        if "title" not in dic or pd.isnull(dic["title"]) or len(dic["title"]) == 0:
            dic["title"] = None
        if dic["etype"] == "record" or dic["etype"] == "chat":
            if dic["title"] is None:
                ret, title = self.get_title(
                    dic["user_id"], content, use_llm=use_llm, debug=debug
                )
                if ret:
                    dic["title"] = title
            if dic["ctype"] is None or dic["status"] is None:
                dic_new, content = self.get_ctype(
                    dic["user_id"], content, dic["etype"], use_llm=use_llm, debug=debug
                )
                if dic["ctype"] is None and "ctype" in dic_new:
                    dic["ctype"] = dic_new["ctype"]
                if dic["status"] is None and "status" in dic_new:
                    dic["status"] = dic_new["status"]
            if dic["atype"] is None:
                dic["atype"] = "subjective"
        elif dic["etype"] == "note":
            if dic["title"] is None:
                filename = os.path.basename(content)
                dic["title"] = os.path.splitext(filename)[0]
            if dic["ctype"] is None:
                dic["ctype"] = DEFAULT_CATEGORY
            if dic["status"] is None:
                dic["status"] = "collect"
            if dic["atype"] is None:
                dic["atype"] = "subjective"
        elif dic["etype"] == "file":
            if dic["title"] is None:
                filename = os.path.basename(content)
                dic["title"] = filename
            if dic["ctype"] is None:
                dic_new, content = self.get_ctype(
                    dic["user_id"],
                    dic["title"],
                    dic["etype"],
                    use_llm=use_llm,
                    debug=debug,
                )
                if "ctype" in dic_new:
                    dic["ctype"] = dic_new["ctype"]
            if dic["status"] is None:
                dic["status"] = "collect"
            if dic["atype"] is None:
                dic["atype"] = "objective"
        elif dic["etype"] == "web":
            if dic["title"] is None or dic["ctype"] is None:
                dret, path = download_file(content)
                if dret:
                    if dic["title"] is None:
                        dic["title"] = get_web_title(path)
                    if dic["ctype"] is None:
                        ret, md_path = convert_to_md(path)
                        if ret:
                            content = read_md_content(md_path)
                            dic_new, content = self.get_ctype(
                                dic["user_id"],
                                content,
                                dic["etype"],
                                use_llm=use_llm,
                                debug=debug,
                            )
                            if "ctype" in dic_new:
                                dic["ctype"] = dic_new["ctype"]
            if dic["status"] is None:
                dic["status"] = "collect"
            if dic["atype"] is None:
                dic["atype"] = "third_party"
        # if not set, set default value
        if dic["ctype"] is None:
            dic["ctype"] = DEFAULT_CATEGORY
        if dic["status"] is None:
            dic["status"] = DEFAULT_STATUS
        if dic["atype"] is None:
            dic["atype"] = "subjective"
        if dic["title"] is None:
            dic["title"] = content
        if len(dic["title"]) > TITLE_LENGTH:
            dic["title"] = dic["title"][:TITLE_LENGTH] + "..."
        return True, dic

    def regular_status(self, dic_base, dic_detect):
        """
        Normalized State
        dic: Extracted state and other information
        Priority: dic_new > dic_base
        """
        if "status" in dic_base and dic_base["status"] in ["todo", "collect"]:
            # Prioritizing Custom Statuses
            return dic_base["status"]
        elif "status" in dic_detect and dic_detect["status"] is not None:
            status = dic_detect["status"]
        elif "status" in dic_base and dic_base["status"] is not None:
            status = dic_base["status"]
        else:
            status = "init"
        map_dic = {_("to_be_organized"): "collect", _("to-do_list"): "todo"}
        if status in map_dic:
            status = map_dic[status]
        logger.info(f"base {dic_base}, detect {dic_detect}, regular status {status}")
        return status

    def get_all_categories(self, debug=False):
        """
        Return all sub-categories
        """
        clist = []
        for idx, row in self.df_record.iterrows():
            clist.append(row["ctype"])
            if not pd.isnull(row["alias"]):
                clist += row["alias"].split(",")
        clist = list(set(clist))
        if debug:
            print(clist)
        return clist

    def get_ctype_by_keyword(self, content, etype, debug=False):
        if debug:
            logger.debug(f"keywords list {len(self.calist)}, {self.calist[:3]}...")
        for l in self.calist:
            if content.startswith(l):
                content = content[len(l) :].strip()
                if content.startswith(".") or content.startswith("。"):
                    content = content[1:]
                return True, self.get_regular_ctype(l, etype), content
        return False, None, content

    def get_ctype(self, user_id, content, etype, use_llm=True, debug=False):
        """
        Return category
        """
        ret, ctype, content = self.get_ctype_by_keyword(content, etype, debug=debug)
        if ret:
            dic = {"ctype": ctype}
        elif use_llm:
            dic = self.get_type_by_llm(user_id, content, etype, debug=debug)
        else:
            dic = {"ctype": DEFAULT_CATEGORY}
        dic = self.fill_info(dic)
        return dic, content

    def get_regular_ctype(self, keyword, etype):
        """
        Return refined category
        """
        if etype == "record":
            df = self.df_record
        else:
            df = self.df_web
        for idx, row in df.iterrows():
            if row["ctype"] == keyword:
                return row["ctype"]
            if not pd.isnull(row["alias"]):
                for a in row["alias"].split(","):
                    if a == keyword:
                        return row["ctype"]
        return DEFAULT_CATEGORY

    def fill_info(self, dic, debug=True):
        """
        Return the complete information of the category, existing information will not be overwritten.
        """
        if debug:
            logger.debug(f"fill_info {dic}")
        default_info = {"ctype": DEFAULT_CATEGORY, "atype": None, "status": None}
        if "etype" in dic and dic["etype"] == "web":
            df = self.df_web
        else:
            df = self.df_record
        for idx, row in df.iterrows():
            if "ctype" in dic and row["ctype"] == dic["ctype"]:
                default_info = row.to_dict()
        for key, value in dic.items():
            if pd.notnull(value):
                default_info[key] = value
        for key, value in default_info.items():
            if key not in dic:
                dic[key] = value
        if debug:
            logger.debug(f"after fill_info {dic}")
        return dic

    def get_title(self, user_id, content, use_llm=True, debug=False):
        """
        Determine the title through the language model
        """
        # Get the first line of content
        if pd.isnull(content):
            return False, None
        content = content.strip()
        line = content.split("\n")[0]
        if len(line) <= 15:
            return True, line
        try:
            query = PROMPT_TITLE.format(
                content=content, language=get_language_name(LANGUAGE_CODE.lower())
            )
            if use_llm:
                ret, answer, detail = llm_query(
                    user_id, RECORD_ROLE, query, "record", debug=True
                )
                if ret:
                    answer = replace_chinese_punctuation_with_english(answer)
                    answer = re.sub(r"[^\w\s]", "", answer)
                    return True, answer
        except Exception as e:
            print("failed", e)
        return False, None

    def get_type_by_llm(self, user_id, content, etype, debug=False):
        """
        Determine the Category Through the Language Model
        """
        if etype == "record" or etype == "chat":
            df = self.df_record
        else:
            df = self.df_web
        ctype_list = df["ctype"].unique()
        status_list = df["status"].unique()
        auth_list = df["auth"].unique()
        if debug:
            logger.info(
                f"get_type_by_llm, types {len(ctype_list)}, content {content[:10]}..."
            )
        try:
            if len(content) > 100:
                content = content[:100] + "..."
            query = PROMPT_CLASSIFY.format(
                content=content,
                ctype_list=",".join(ctype_list),
                auth_list=",".join(auth_list),
                status_list=",".join(status_list),
                demo=str(
                    {
                        "ctype": ctype_list[0],
                        "atype": auth_list[0],
                        "status": status_list[0],
                    }
                ),
            )
            ret, dic, detail = llm_query_json(
                user_id, RECORD_ROLE, query, "record", debug=True
            )
            if "status" in dic and dic["status"] is not None:
                if dic["status"] not in status_list:
                    del dic["status"]
            if "ctype" in dic and dic["ctype"] is not None:
                if dic["ctype"] not in ctype_list:
                    del dic["ctype"]
            if "atype" in dic and dic["atype"] is not None:
                if dic["atype"] not in auth_list:
                    del dic["atype"]
            if 'ctype' not in dic:
                dic['ctype'] = DEFAULT_CATEGORY
            if 'status' not in dic:
                dic['status'] = DEFAULT_STATUS
            if 'atype' not in dic:
                dic['atype'] = None
            return dic
        except Exception as e:
            traceback.print_exc()
            print("failed", e)
        return {"ctype": DEFAULT_CATEGORY, "atype": None, "status": None}
