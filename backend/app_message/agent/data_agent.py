from loguru import logger
from django.utils.translation import gettext as _
from backend.common.utils.web_tools import (
    get_url_content,
    get_web_abstract,
)
from backend.common.utils.file_tools import (
    get_file_content,
    get_file_abstract,
)
from backend.common.speech.tts import run_tts
from app_message.agent.base_agent import BaseAgent, agent_function
from app_message.command import msg_common_select

import pandas as pd
import os
from app_record.record import get_export_file
from app_message.function import search_data, regular_title
from app_dataforge.entry import add_data
from app_dataforge.misc_tools import add_url

class RecordAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("record_agent")
        self.instructions = "This agent provides functions for recording, searching records, and exporting records. "

    @agent_function(_("search_records"))
    def _afunc_record_search(context_variables: dict, content: str = None):
        """Search records"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
            sdata.set_cache("prev_cmd", _("search_records"))
            return True, {
                "type": "text",
                "content": _("please_enter_search_content"),
                "user_id": sdata.user_id,
                "etype": "record",
            }
        else:
            return search_data(sdata, dic={"etype": "record"})

    @agent_function(_("record"))
    def _afunc_record_input(context_variables: dict, content: str = None):
        """Input record"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
            sdata.set_cache("prev_cmd", _("record"))
            return True, {"type": "text", "content": _("please_enter_the_record_content")}
        else:
            dic = {
                "user_id": sdata.user_id,
                "etype": "record",
                "raw": content,
                "source": "wechat",
            }
            ret, ret_emb, info = add_data(dic)
            return True, {"type": "text", "content": info}

    @agent_function(_("export_records"))
    def _afunc_record_export(context_variables: dict):
        """Export records"""
        sdata = context_variables["sdata"]
        ret, info = get_export_file(sdata.user_id)
        if ret:
            file_path = info
            filename = os.path.basename(file_path)
            return True, {
                "type": "file",
                "content": file_path,
                "filename": f"{filename}",
            }
        return True, {"type": "text", "content": info}



class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("web_processing_agent")
        self.instructions = "This agent provides functions for collecting web pages, setting web pages to-do, summarizing web content, getting web content, converting web pages to audio, and listing web functions."

    @agent_function(_("web_functions_list"))
    def _afunc_web_op(context_variables: dict, web_addr: str = None):
        """Web functions list"""
        sdata = context_variables["sdata"]
        sdata.current_content = web_addr
        return msg_web_main(sdata)

    @agent_function(_("collect_webpage"))
    def _afunc_web_collect(context_variables: dict, content: str = None):
        """Collect web page"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        url = sdata.get_cache("url")
        if url is not None:
            ret, info = msg_add_url(url, sdata, "collect")
            return ret, {"type": "text", "content": info}
        if pd.notna(content):
            ret, info = msg_add_url(content, sdata, "collect")
            return ret, {"type": "text", "content": info}
        return True, {"type": "text", "content": _("no_urls_dot_")}

    @agent_function(_("set_webpage_todo"))
    def _afunc_web_todo(context_variables: dict, content: str = None):
        """Set web page to-do"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        url = sdata.get_cache("url")
        if url is not None:
            ret, info = msg_add_url(url, sdata, "todo")
            return ret, {"type": "text", "content": info}
        if pd.notna(content):
            ret, info = msg_add_url(content, sdata, "todo")
            return ret, {"type": "text", "content": info}
        return True, {"type": "text", "content": _("no_urls_dot_")}

    @agent_function(_("summarize_webpage_content"))
    def _afunc_web_extract(context_variables: dict):
        """Extract web content"""
        sdata = context_variables["sdata"]
        url = sdata.get_cache("url")
        logger.debug(f"msg_web_extract {url}")
        if url is not None:
            # ret, detail = get_url_detail(url)
            detail = get_web_abstract(sdata.user_id, url)
            if detail is not None:
                return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("failed_to_fetch_webpages")}

    @agent_function(_("get_text_content"))
    def _afunc_web_content(context_variables: dict):
        """Get web content"""
        sdata = context_variables["sdata"]
        url = sdata.get_cache("url")
        title, content = get_url_content(url)
        if content is not None:
            return True, {"type": "text", "content": content}
        return True, {"type": "text", "content": _("no_content_found")}

    @agent_function(_("webpage_to_audio"))
    def _afunc_web_audio(context_variables: dict):
        """Web page to audio"""
        sdata = context_variables["sdata"]
        url = sdata.get_cache("url")
        title, content = get_url_content(url)
        title = regular_title(title)
        if title is not None:
            title = f"{_('web_page')}_{title[:10]}"
            sdata.set_cache("tts_file_title", title)
            return run_tts(title, content, sdata.user_id)
        else:
            return True, {"type": "text", "content": _("page_not_found")}

WEB_URL = f"http://{os.getenv('FRONTEND_ADDR_OUTER', '')}:{os.getenv('FRONTEND_PORT_OUTER', '8084')}"

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("data_management_agent")
        self.instructions = "This agent provides functions for managing data, searching data, searching files, searching to-do web pages, searching collected web pages, and searching web pages."

    @agent_function(_("search_data"))
    def _afunc_data_search(context_variables: dict, content: str = None):
        """Search data"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", _("search_data"))
            return True, {"type": "text", "content": _("please_enter_search_content")}
        else:
            return search_data(sdata)

    @agent_function(_("search_files"))
    def _afunc_file_search(context_variables: dict, content: str = None):
        """Search files"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", _("search_files"))
            return True, {
                "type": "text",
                "content": _("please_enter_what_you're_looking_for"),
            }
        else:
            return search_data(sdata, dic={"etype": "file"})
        
    @agent_function(_("search_todo_webpages"))
    def _afunc_web_my_todo(context_variables: dict, content: str = None):
        """Search to-do web pages"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"status": "todo", "etype": "web"})

    @agent_function(_("search_collected_webpages"))
    def _afunc_web_my_collect(context_variables: dict, content: str = None):
        """Search collected web pages"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"status": "collect", "etype": "web"})

    @agent_function(_("search_webpages"))
    def _afunc_web_search(context_variables: dict, content: str = None):
        """Search web pages"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"etype": "web"})

    @agent_function(_("manage_data"))
    def _afunc_data_manage(context_variables: dict):
        """Manage data"""
        url = f"{WEB_URL}"
        return True, {"type": "sharing", "content": _("please_open_following_link") + f":\n{url}"}


class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("file_processing_agent")
        self.instructions = "This agent provides functions for extracting file content, converting text to audio, and collecting files."

    @agent_function(_("extract_file_content"))
    def _afunc_file_extract(context_variables: dict):
        """Extract file content"""
        logger.debug("in msg_extract_file")
        sdata = context_variables["sdata"]
        data = sdata.get_cache("file")
        ret, detail = get_file_abstract(data, sdata.user_id)
        if ret:
            return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}

    @agent_function(_("file_to_audio"))
    def _afunc_file_tts(context_variables: dict):
        """File to speech"""
        sdata = context_variables["sdata"]
        data = sdata.get_cache("file")
        ret, path, title, content = get_file_content(data)
        if ret:
            sdata.set_cache("tts_file_title", title)
            return run_tts(title, content, sdata.user_id)
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}

    @agent_function(_("collect_file"))
    def _afunc_file_save(context_variables: dict):
        """Save file"""
        sdata = context_variables["sdata"]
        (base_path, addr) = sdata.get_cache("file")
        if base_path is None:
            return False, _("file_collection_failed_colon__file_not_found")
        dic = {}
        dic["user_id"] = sdata.user_id
        dic["etype"] = "file"
        dic["source"] = "wechat"
        dic["addr"] = addr
        ret, ret_emb, info = add_data(dic, base_path)
        return ret, info

def msg_add_url(url, sdata, status):
    ret, base_path, info = add_url(url, sdata.args, status)
    if ret and info == "pdf":
        from app_message.message import msg_recv_file
        return msg_recv_file(base_path, None, sdata)
    else:
        return ret, info

from backend.common.utils.web_tools import regular_url

def msg_web_main(sdata):
    """
    Web functionality entry
    """
    if sdata.current_content != "":
        url = regular_url(sdata.current_content)
        logger.debug(
            f"before regular {sdata.current_content}\nafter regular {url}",
        )
        if url is not None:
            sdata.set_cache("url", url)
            title, content = get_url_content(url)
            if content is None:
                return True, {"type": "text", "content": _("no_webpage_content_found")}

            length = len(content)
            cmd_list = []
            for func in WebAgent().get_functions():
                cmd_list.append((func.__doc__, func.__doc__))
            return msg_common_select(
                sdata,
                cmd_list=cmd_list,
                detail=_("received_webpage_with_characters").format(length=length),
            )
    return True, {"type": "text", "content": _("please_enter_the_url_or_share_the_page_with_me")}
