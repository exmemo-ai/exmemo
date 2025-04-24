import os
import re
import traceback
import pandas as pd
from loguru import logger
from django.utils.translation import gettext as _
from backend.settings import BASE_DATA_DIR
from backend.common.utils.web_tools import get_url_content
from backend.settings import LANGUAGE_CODE
from backend.common.files import utils_file
from backend.common.llm.llm_hub import llm_query_json
from backend.common.utils.file_tools import is_image_file
from backend.common.utils.web_tools import truncate_content
from backend.common.utils.text_tools import replace_chinese_punctuation_with_english, get_language_name
from backend.common.user.user import UserManager
from backend.settings import LANGUAGE_CODE
from .prompt import PROMPT_COMPREHENSIVE

DEFAULT_CATEGORY = _("unclassified")
IMAGE_CATEGORY = _("image")
DEFAULT_STATUS = "init"
RECORD_ROLE = "You are a personal assistant, and your master is a knowledge worker."
TITLE_MAX_LENGTH = 128

class CategoryConfigLoader:
    _instance = None
    
    @staticmethod
    def get_instance():
        if CategoryConfigLoader._instance is None:
            CategoryConfigLoader._instance = CategoryConfigLoader()
        return CategoryConfigLoader._instance

    def __init__(self):
        if LANGUAGE_CODE.lower().find("zh") >= 0:
            path = os.path.join(BASE_DATA_DIR, "record_keyword_zh.xlsx")
        else:
            path = os.path.join(BASE_DATA_DIR, "record_keyword_en.xlsx")
        self.df_record = pd.read_excel(path, sheet_name="record")
        self.df_web = pd.read_excel(path, sheet_name="web")
        self.calist = self._get_all_categories(debug=True)

    def _get_all_categories(self, debug=False):
        """Return all sub-categories"""
        clist = []
        for idx, row in self.df_record.iterrows():
            clist.append(row["ctype"])
            if not pd.isnull(row["alias"]):
                clist += row["alias"].split(",")
        clist = list(set(clist))
        if debug:
            logger.debug(clist)
        return clist

    def get_dataframe(self, etype="record"):
        """Return the appropriate dataframe based on entry type"""
        return self.df_web if etype == "web" else self.df_record

    def get_categories_list(self):
        """Return the list of all categories"""
        return self.calist

    def get_regular_ctype(self, keyword, etype):
        """Return refined category"""
        df = self.get_dataframe(etype)
        for idx, row in df.iterrows():
            if row["ctype"] == keyword:
                return row["ctype"]
            if not pd.isnull(row["alias"]):
                for a in row["alias"].split(","):
                    if a == keyword:
                        return row["ctype"]
        return DEFAULT_CATEGORY

class EntryFeatureTool:
    _instance = None

    @staticmethod
    def get_instance():
        if EntryFeatureTool._instance is None:
            EntryFeatureTool._instance = EntryFeatureTool()
        return EntryFeatureTool._instance

    def __init__(self):
        self.category_loader = CategoryConfigLoader.get_instance()
        self.calist = self.category_loader.get_categories_list()

    def get_base_path(self, path, title):
        if title in path:
            base_path = path.split(title)[0].rstrip('/')
            return base_path
        return path

    def update_bookmark_paths(self, dic, new_title, base_path):
        new_path = f"{base_path}/{new_title}"
        dic.update({
            "path": new_path,
            "meta": {
                **dic.get("meta", {}),
                "update_path": new_path,
                "resource_path": new_path
            }
        })

    def parse(self, dic, content, use_llm=True, force=False, debug=False):
        user = UserManager.get_instance().get_user(dic["user_id"])
        description = None

        required_fields = ["ctype", "status", "atype", "title"]
        for field in required_fields:
            if field not in dic or pd.isnull(dic[field]) or len(str(dic[field])) == 0:
                dic[field] = None

        if dic["etype"] in ["record", "chat"]:
            if dic["title"] is None or dic["ctype"] is None or dic["status"] is None:
                ret, features = get_features_by_llm(
                    dic["user_id"], content, dic["etype"], use_llm=use_llm, debug=debug
                )
                if ret:
                    if dic["title"] is None and "title" in features:
                        dic["title"] = features["title"]
                    if "category" in features:
                        if dic["ctype"] is None:
                            dic["ctype"] = features["category"].get("ctype")
                        if dic["status"] is None:
                            dic["status"] = features["category"].get("status")
                        if dic["atype"] is None:
                            dic["atype"] = features["category"].get("atype")
                    if "summary" in features:
                        description = features["summary"]
        elif dic["etype"] in ["note", "file"]:
            if dic["title"] is None:
                dic["title"] = os.path.basename(content)
            if dic["ctype"] is None:
                if is_image_file(content):
                    dic["ctype"] = IMAGE_CATEGORY
                elif (dic["etype"] == "note" and user.get("note_get_category") == False and not force) or \
                     (dic["etype"] == "file" and user.get("file_get_category") == False and not force):
                    dic["ctype"] = DEFAULT_CATEGORY
                else:
                    ret, features = get_features_by_llm(
                        dic["user_id"], dic["title"], dic["etype"], 
                        use_llm=use_llm, debug=debug
                    )
                    if ret and "category" in features:
                        dic["ctype"] = features["category"].get("ctype")
                        dic["status"] = dic["status"] or features["category"].get("status")
                        dic["atype"] = dic["atype"] or features["category"].get("atype")
                    if "summary" in features:
                        description = features["summary"]
            dic["status"] = dic["status"] or "collect"
            if dic["etype"] == "note":
                dic["atype"] = dic["atype"] or "subjective"
            else:
                dic["atype"] = dic["atype"] or "third_party"
        elif dic["etype"] == "web":
            if dic["title"] is None or (dic["ctype"] is None and user.get("web_get_category") != False):
                title, web_content = get_url_content(content)
                if dic["title"] is None:
                    dic["title"] = title
                if dic["ctype"] is None and user.get("web_get_category") != False:
                    ret, features = get_features_by_llm(
                        dic["user_id"], web_content, dic["etype"], 
                        title=title, use_llm=use_llm, debug=debug
                    )
                    if ret and "category" in features:
                        dic["ctype"] = features["category"].get("ctype")
                        dic["status"] = dic["status"] or features["category"].get("status")
                        dic["atype"] = dic["atype"] or features["category"].get("atype")
                    if "summary" in features:
                        description = features["summary"]
            dic["status"] = dic["status"] or "collect"
            dic["atype"] = dic["atype"] or "third_party"                        

        # Set default values
        dic["ctype"] = dic["ctype"] or DEFAULT_CATEGORY
        dic["status"] = dic["status"] or DEFAULT_STATUS
        dic["atype"] = dic["atype"] or "subjective"
        dic["title"] = dic["title"] or content

        # Check if title is too long
        if len(dic["title"]) > TITLE_MAX_LENGTH:
            title_copy = dic["title"]
            new_title = dic["title"][:TITLE_MAX_LENGTH] + "..."
            dic["title"] = new_title
            # Update path, add wanglei
            if dic.get('source') == 'bookmark':
                base_path = self.get_base_path(dic["path"], title_copy)
                self.update_bookmark_paths(dic, new_title, base_path)

        # fill description
        if description is not None:
            if 'meta' not in dic:
                dic['meta'] = {}
            if 'description' not in dic['meta']:
                dic['meta']['description'] = description
            else:
                dic['meta']['description'] = dic['meta']['description'] or description

        return True, dic


def get_features_by_llm(user_id, content, etype, title=None, use_llm=True, debug=False):
    """
    Returns:
        (success, {
            "title": str,
            "category": {"ctype": str, "atype": str, "status": str},
            "summary": str
        })
    """
    try:
        if not use_llm:
            return False, None

        user = UserManager.get_instance().get_user(user_id)
        is_truncate=user.get("truncate_content")
        truncate_mode=user.get("truncate_mode")
        logger.info(f'get_text_extract {is_truncate} {truncate_mode} {len(content)}')

        if is_truncate:
            max_length=user.get("truncate_max_length")
            content = truncate_content(content, title, max_length, truncate_mode)
            logger.info(f'truncate_content {len(content)}')
        logger.info(f"get_text_extract: {content[:50]}, len {len(content)}")
        if len(content) == 0:
            return False, None

        df = CategoryConfigLoader.get_instance().get_dataframe(etype)
        ctype_list = df["ctype"].unique()
        status_list = df["status"].unique()
        auth_list = df["auth"].unique()
        
        # later get user setting
        lang = utils_file.check_language(content)
        max_length = 400 if lang == "en" else 100
        truncated_content = content[:max_length] + "..." if len(content) > max_length else content
        
        query = PROMPT_COMPREHENSIVE.format(
            content=truncated_content,
            language=get_language_name(LANGUAGE_CODE.lower()),
            ctype_list=",".join(ctype_list),
            auth_list=",".join(auth_list),
            status_list=",".join(status_list)
        )
        
        ret, result, detail = llm_query_json(
            user_id, RECORD_ROLE, query, "data_manager", debug=debug
        )
        
        if not ret or not isinstance(result, dict):
            return False, None
            
        if "category" in result:
            cat = result["category"]
            if cat.get("ctype") not in ctype_list:
                cat["ctype"] = DEFAULT_CATEGORY
            if cat.get("status") not in status_list:
                cat["status"] = DEFAULT_STATUS
            if cat.get("atype") not in auth_list:
                cat["atype"] = None
        
        if "title" in result:
            result["title"] = replace_chinese_punctuation_with_english(result["title"])
            result["title"] = re.sub(r"[^\w\s]", "", result["title"])        
        return True, result
        
    except Exception as e:
        logger.warning(f"get_content_features failed: {e}")
        if debug:
            traceback.print_exc()
        return False, None
