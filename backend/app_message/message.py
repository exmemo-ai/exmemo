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
from backend.common.files import utils_filemanager, filecache
from backend.common.utils.web_tools import (
    regular_url,
    get_url_content,
)
from backend.common.utils.net_tools import is_valid_url
from backend.common.utils.file_tools import (
    support_file,
    is_audio_file,
    is_doc_file,
    get_ext,
)
from backend.common.utils.text_tools import replace_fullwidth_numbers_with_halfwidth
from backend.common.utils.sys_tools import is_app_installed

from app_dataforge.entry import get_entry

from .command import *
from .function import *
from .session import *

from app_message import my_agent

my_agent.WebAgent().add_commands()
my_agent.DataAgent().add_commands()
my_agent.AudioAgent().add_commands()
my_agent.SettingAgent().add_commands()
my_agent.FileAgent().add_commands()
my_agent.HelpAgent().add_commands()

if is_app_installed("app_record"):
    my_agent.RecordAgent().add_commands()

if is_app_installed("app_diet"):
    #my_agent.DietAgent().register() # later use it
    my_agent.DietAgent().add_commands()

if is_app_installed("app_translate"):
    my_agent.TranslateAgent().add_commands()

####################

def msg_web_my_op(sdata):
    return True, {"type": "text", "content": "请输入网址或者分享网页给我"}

CommandManager.get_instance().register(
    Command(msg_web_my_op, ["操作网页"], level=LEVEL_NORMAL)
)


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
                return True, {"type": "text", "content": "没有找到网页内容"}

            length = len(content)
            cmd_list = []
            for func in my_agent.WebAgent().get_functions():
                cmd_list.append((func.__doc__, func.__doc__))
            return msg_common_select(
                sdata,
                cmd_list=cmd_list,
                detail=f"收到网页，正文共{length}字",
            )
    return True, {"type": "text", "content": _("please_enter_the_url_or_share_the_page_with_me")}

def msg_upload_main(sdata):
    (path, filename) = sdata.get_cache("file")
    if path is not None:
        cmd_list = [("收藏文件", "收藏文件")]
        if is_doc_file(path):
            cmd_list += [("总结文件内容", "总结文件内容"), ("文本转音频", "文本转音频")]
        elif is_audio_file(path):
            cmd_list += [("语音识别", "语音识别")]
        return msg_common_select(sdata, cmd_list, detail="收到文件")
    else:
        return True, {
            "type": "text",
            "content": _("please_upload_or_share_a_file_first"),
        }


def msg_search_detail(sdata):
    uid = sdata.user_id
    idx = sdata.current_content
    obj = get_entry(idx)
    if obj is not None:
        if obj.etype == "file" or obj.etype == "note":
            filename = os.path.basename(obj.path)
            ext = get_ext(filename)
            path = filecache.get_tmpfile(ext)
            if utils_filemanager.get_file_manager().get_file(uid, obj.path, path):
                return True, {"type": "file", "content": path, "filename": filename}
        elif obj.etype == "web":
            return True, {"type": "text", "content": obj.addr}
        else:
            detail = f"\n主题:\n{obj.title}\n\n内容:\n{obj.raw}"
            return True, {"type": "text", "content": detail}
    return True, {"type": "text", "content": _("failed_to_fetch_files")}


CommandManager.get_instance().register(
    Command(msg_search_detail, [CMD_INNER_GET], level=LEVEL_NORMAL)
)


def do_message(sdata:Session):
    """
    Handling WeChat Chat Entry
    """
    try:
        content = sdata.current_content
        if pd.isnull(content):
            return False, {"type": "text", "content": _("nothing_entered")}
        ret = False
        detail = {"type": "text", "content": _("unrecognized_command")}
        prev_cmd = sdata.get_cache("prev_cmd")

        if is_valid_url(content):  # Enter Website
            ret, detail = msg_web_main(sdata)
        if (not ret and prev_cmd is not None):  
            # The previous conversation was asking the user to enter information
            sdata.current_content = prev_cmd + " " + sdata.current_content
            prev_cmd = sdata.set_cache("prev_cmd", None)
            ret, detail = CommandManager.get_instance().msg_do_command(sdata)
        if not ret:  # Enter a numerical value
            ret, detail = parse_select_number(sdata)
        if not ret:  # Enter Command
            ret, detail = CommandManager.get_instance().msg_do_command(sdata)
        logger.info(f"content:{content} ret:{ret} detail:{detail}")
        if not ret:
            ret, detail = do_chat(sdata)
            if ret:
                detail = SessionManager.get_instance().send_message(content, detail, sdata)
            else:
                detail = {"type": "text", "content": detail}
        return True, detail
    except Exception as e:
        traceback.print_exc()
        logger.warning(f"do_message error {e}")
        return True, {"type": "text", "content": _("failed_to_process_information")}


def parse_select_number(sdata):
    content = sdata.current_content
    content = content.strip().replace(".", "")
    content = replace_fullwidth_numbers_with_halfwidth(content)
    if content.isdigit():
        idx = int(content)
        next_cmd = sdata.get_cache("next_cmd")
        logger.info(f"next_cmd {next_cmd} idx {idx}")
        if next_cmd is None or len(next_cmd) < idx:
            return False, _("no_optional_commands")
        sdata.current_content = next_cmd[idx - 1][1]  # cmd value
        return CommandManager.get_instance().msg_do_command(sdata)
    return False, _("not_a_number")


def msg_recv_file(base_path, filename, sdata):
    """
    Parse the uploaded file and store the data in the database
    """
    logger.debug(f"parse_file: {base_path}")
    sdata.set_cache("file", (base_path, filename))
    ret = False
    dic = {}
    if support_file(base_path):
        ret, dic = msg_upload_main(sdata)
    if ret:
        return True, dic["content"]
    else:
        if "content" in dic:
            return True, dic["content"]
        else:
            return False, _("the_file_type_is_not_valid_or_not_supported")


CommandManager.get_instance().check_conflict()
