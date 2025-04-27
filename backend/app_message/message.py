"""
wechat message
"""

import os
import traceback
from loguru import logger
import pandas as pd

from django.utils.translation import gettext as _
from backend.common.user.user import *
from backend.common.user.resource import *
from backend.common.utils.web_tools import WEB_URL
from backend.common.files import utils_filemanager, filecache
from backend.common.utils.net_tools import is_valid_url
from backend.common.utils.file_tools import (
    support_file,
    is_audio_file,
    is_doc_file,
    get_ext,
)
from backend.common.utils.text_tools import replace_fullwidth_numbers_with_halfwidth
from app_dataforge.entry import get_entry
from app_dataforge.entry_storage import EntryStorage
from .command import *
from .function import *
from .session import *
from .chat_tools import do_chat
from app_message.agent import agent_manager
from app_message.agent import data_agent


def msg_search_detail(dic):
    sdata = dic['sdata']
    uid = sdata.user_id
    idx = sdata.current_content
    obj = get_entry(idx)
    if obj is not None:
        if obj.etype == "file" or obj.etype == "note":
            filename = os.path.basename(obj.path)
            # check req from web
            if sdata.source == "web":
                return {"type": "text", "info": f"[{filename}]({WEB_URL}/view_markdown?idx={obj.idx})"}
            else:
                ext = get_ext(filename)
                path = filecache.get_tmpfile(ext)
                if utils_filemanager.get_file_manager().get_file(uid, obj.path, path):
                    return {"type": "file", "path": path, "filename": filename}
        elif obj.etype == "web":
            if sdata.source == "web":
                return {"type": "text", "info": f"[{obj.title}]({WEB_URL}/view_markdown?idx={obj.idx})"}
            else:
                return obj.addr
        elif obj.etype == "record":
            detail = EntryStorage.get_content(uid, obj.addr)
            detail = f"\n{_('title')}:\n{obj.title}\n\n_('content'):\n{detail}"
            return detail
        elif obj.etype == "chat":
            if sdata.source == "web":
                return {"type": "text", "info": f"[{obj.title}]({WEB_URL}/view_markdown?idx={obj.idx})"}
            else:
                detail = f"\n{_('title')}:\n{obj.title}\n\n_('content'):\n{obj.raw}"
            return detail
    return _("failed_to_fetch_files")

def do_message(sdata:Session):
    """
    Handling WeChat Chat Entry
    """

    agent = agent_manager.AllAgentManager.get_instance()
    try:
        content = sdata.current_content
        if pd.isnull(content) or content == "":
            return False, _("nothing_entered")
        ret = False
        detail = _("unrecognized_command")
        prev_cmd = sdata.get_cache("prev_cmd")

        if is_valid_url(content):  # Enter Website
            ret, detail = data_agent.msg_web_main(sdata)
        if (not ret and prev_cmd is not None):  
            # The previous conversation was asking the user to enter information
            sdata.current_content = prev_cmd + " " + sdata.current_content
            prev_cmd = sdata.set_cache("prev_cmd", None)
            ret, detail = CommandManager.get_instance().msg_do_command(sdata)
        if not ret: # Enter a numerical value
            ret, detail = parse_select_number(sdata)
        if not ret: # Enter Command
            ret, detail = CommandManager.get_instance().msg_do_command(sdata)
        if not ret: 
            if content.startswith('/'):
                ret, detail = CommandManager.get_instance().msg_do_command(sdata)
                if not ret:
                    ret, detail = agent.do_command(sdata)
            else:
                ret = True
                ret, detail = do_chat(sdata)
                if ret:
                    #sid = SessionManager.get_instance().send_message(content, detail, sdata)
                    #detail = {"type": "text", "info": detail, "sid": sid}
                    detail = {"type": "text", "info": detail}
            logger.info(f"content:{content} ret:{ret} detail:{detail}")
        if not isinstance(detail, dict):
            detail = {"type": "text", "info": detail}
        if "info" in detail:
            response = detail["info"]
        else:
            response = None
        sid = SessionManager.get_instance().send_message(content, response, sdata)
        detail["sid"] = sid
        return True, detail
    except Exception as e:
        traceback.print_exc()
        logger.warning(f"do_message error {e}")
        return False, {"sid": sdata.sid, "info":_("failed_to_process_information")}


def parse_select_number(sdata):
    content = sdata.current_content
    content = content.strip().replace(".", "")
    content = replace_fullwidth_numbers_with_halfwidth(content)
    if content.isdigit():
        idx = int(content)
        next_cmd = sdata.get_cache("next_cmd")
        logger.info(f"next_cmd {next_cmd} idx {idx} sid {sdata.sid}")
        if next_cmd is None:
            return False, _("no_optional_commands")
        elif len(next_cmd) < idx:
            return True, _("no_optional_commands") + f": {idx}"
        sdata.current_content = next_cmd[idx - 1][1]  # cmd value
        return CommandManager.get_instance().msg_do_command(sdata)
    return False, _("not_a_number")

def msg_upload_main(sdata):
    (path, filename) = sdata.get_cache("file")
    if path is not None:
        cmd_list = [(_("collect_file"), _("collect_file"))]
        if is_doc_file(path):
            cmd_list += [
                (_("summarize_file_content"), _("summarize_file_content")), 
                (_("file_to_audio"), _("file_to_audio"))
            ]
        elif is_audio_file(path):
            cmd_list += [(_("speech_recognition"), _("speech_recognition"))]
        return True, msg_common_select(sdata, cmd_list, detail=_("file_received"))
    else:
        return False, _("please_upload_or_share_a_file_first")

def msg_recv_file(base_path, filename, sdata):
    """
    Parse the uploaded file and store the data in the database
    """
    logger.debug(f"parse_file: {base_path}")
    sdata.set_cache("file", (base_path, filename))
    ret = False
    detail = _("unsupported_document_type")
    if support_file(base_path):
        ret, detail = msg_upload_main(sdata)
    return ret, {"type": "text", "sid": sdata.sid, "info": detail}


CommandManager.get_instance().register(
    Command(msg_search_detail, [CMD_INNER_GET], level=LEVEL_NORMAL)
)
CommandManager.get_instance().check_conflict()
