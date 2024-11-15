"""
wechat message
"""

import os
import re
import traceback
from loguru import logger
import pandas as pd

from django.utils.translation import gettext as _
from backend.common.user.user import *
from backend.common.user.session import *
from backend.common.user.resource import *
from backend.common.llm.llm_hub import llm_query
from backend.common.llm.llm_tools import DEFAULT_CHAT_LLM, get_llm_list
from backend.common.speech.tts import (
    stop_tts,
    get_tts_result,
    run_tts,
    tts_get_voice_and_engine,
    tts_set_engine,
)
from backend.common.speech.asr_tools import do_asr
from backend.common.files import utils_filemanager, filecache
from backend.common.utils.web_tools import (
    regular_url,
    get_url_content,
    get_web_abstract,
)
from backend.common.utils.net_tools import is_valid_url
from backend.common.utils.file_tools import (
    support_file,
    is_audio_file,
    is_doc_file,
    get_file_content,
    get_file_abstract,
    get_ext,
)
from backend.common.utils.text_tools import replace_fullwidth_numbers_with_halfwidth
from backend.common.utils.regular_tools import regular_str
from backend.common.utils.sys_tools import is_app_installed

from app_dataforge.entry import add_data, get_entry, get_entry_list
from app_dataforge.misc_tools import add_url

from .command import *
from .function import *
from .data_process import save_message

MSG_ROLE = "You're a smart assistant"
WEB_URL = f"http://{os.getenv('FRONTEND_ADDR_OUTER', '')}:{os.getenv('FRONTEND_PORT_OUTER', '8084')}"


def msg_common_select(sid, cmd_list, detail=None):
    """
    Unified processing of selection commands
    """
    logger.debug(cmd_list)
    SessionManager.get_instance().set_cache(sid, "next_cmd", cmd_list)
    if detail is not None:
        content = f"{detail}\n"
    else:
        content = _("please_choose_colon_\n")
    for idx, (label, value) in enumerate(cmd_list):
        content += f"\n{idx+1}.{label}"
    return True, {"type": "text", "content": content}


# Web Pages
def msg_web_collect(args):
    url = SessionManager.get_instance().get_cache(args["session_id"], "url")
    if url is not None:
        ret, info = msg_add_url(url, args, "collect")
        return ret, {"type": "text", "content": info}
    if pd.notna(args["content"]):
        ret, info = msg_add_url(args["content"], args, "collect")
        return ret, {"type": "text", "content": info}
    return True, {"type": "text", "content": _("no_urls_dot_")}


CommandManager.get_instance().register(
    Command(
        msg_web_collect, ["收藏网页", "记网页", "收录", "网页收藏"], level=LEVEL_NORMAL
    )
)


def msg_web_todo(args):
    url = SessionManager.get_instance().get_cache(args["session_id"], "url")
    if url is not None:
        ret, info = msg_add_url(url, args, "todo")
        return ret, {"type": "text", "content": info}
    if pd.notna(args["content"]):
        ret, info = msg_add_url(args["content"], args, "todo")
        return ret, {"type": "text", "content": info}
    return True, {"type": "text", "content": _("no_urls_dot_")}


CommandManager.get_instance().register(
    Command(msg_web_todo, ["设置待看网页", "待看网页"], level=LEVEL_NORMAL)
)


def msg_web_extract(args):
    url = SessionManager.get_instance().get_cache(args["session_id"], "url")
    logger.debug(f"msg_web_extract {url}")
    if url is not None:
        # ret, detail = get_url_detail(url)
        detail = get_web_abstract(args["user_id"], url)
        if detail is not None:
            return True, {"type": "text", "content": detail}
    return True, {"type": "text", "content": _("failed_to_fetch_webpages")}


CommandManager.get_instance().register(
    Command(msg_web_extract, ["总结网页内容"], level=LEVEL_NORMAL)
)


def msg_web_content(args):
    url = SessionManager.get_instance().get_cache(args["session_id"], "url")
    title, content = get_url_content(url)
    if content is not None:
        return True, {"type": "text", "content": content}
    return True, {"type": "text", "content": _("no_content_found")}


CommandManager.get_instance().register(
    Command(msg_web_content, ["获取文本内容"], level=LEVEL_NORMAL)
)


def msg_web_audio(args):
    url = SessionManager.get_instance().get_cache(args["session_id"], "url")
    title, content = get_url_content(url)
    title = regular_title(title)
    if title is not None:
        title = f"网页_{title[:10]}"
        return run_tts(title, content, args["user_id"], args["session_id"])
    else:
        return True, {"type": "text", "content": _("page_not_found")}


CommandManager.get_instance().register(
    Command(msg_web_audio, ["网页转音频", "网页音频"], level=LEVEL_NORMAL)
)


def msg_web_my_todo(args):
    return search_data(args, dic={"status": "todo", "etype": "web"})


CommandManager.get_instance().register(
    Command(msg_web_my_todo, ["待读的网页"], level=LEVEL_NORMAL)
)


def msg_web_my_collect(args):
    return search_data(args, dic={"status": "collect", "etype": "web"})


CommandManager.get_instance().register(
    Command(msg_web_my_collect, ["收藏的网页"], level=LEVEL_NORMAL)
)


def msg_web_search(args):
    return search_data(args, dic={"etype": "web"})


CommandManager.get_instance().register(
    Command(msg_web_search, ["搜索网页"], level=LEVEL_NORMAL)
)


def msg_web_my_op(args):
    return True, {"type": "text", "content": "请输入网址或者分享网页给我"}


CommandManager.get_instance().register(
    Command(msg_web_my_op, ["操作网页"], level=LEVEL_NORMAL)
)


def msg_web_main(args):
    """
    Web functionality entry
    """
    if args["content"] == "":
        cmd_list = [
            ("待读的网页", "待读的网页"),
            ("收藏的网页", "收藏的网页"),
            ("操作网页", "操作网页"),
        ]
        return msg_common_select(args["session_id"], cmd_list, detail="收到文件")
    else:
        url = regular_url(args["content"])
        logger.debug(
            f"before regular {args['content']}\nafter regular {url}",
        )
        if url is not None:
            SessionManager.get_instance().set_cache(args["session_id"], "url", url)
            title, content = get_url_content(url)
            if content is None:
                return True, {"type": "text", "content": "没有找到网页内容"}

            length = len(content)
            cmd_list = [
                ("总结网页内容", "总结网页内容"),
                ("获取文本内容", "获取文本内容"),
                ("网页转音频", "网页转音频"),
                ("收藏网页", "收藏网页"),
                ("设置待看网页", "设置待看网页"),
            ]
            return msg_common_select(
                args["session_id"],
                cmd_list=cmd_list,
                detail=f"收到网页，正文共{length}字",
            )
    return True, {"type": "text", "content": "未找到网页"}


CommandManager.get_instance().register(
    Command(msg_web_main, ["网页功能"], level=LEVEL_TOP)
)

# Doc File


def msg_file_extract(args):
    logger.debug("in msg_extract_file")
    ret, detail = get_file_abstract(args["session_id"], args["user_id"])
    if ret:
        return True, {"type": "text", "content": detail}
    return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}


CommandManager.get_instance().register(
    Command(msg_file_extract, ["总结文件内容"], level=LEVEL_NORMAL)
)


def msg_file_tts(args):
    ret, path, title, content = get_file_content(args["session_id"])
    if ret:
        return run_tts(title, content, args["user_id"], args["session_id"])
    return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}


CommandManager.get_instance().register(
    Command(msg_file_tts, ["文本转音频"], level=LEVEL_NORMAL)
)


def msg_file_save(args):
    (base_path, addr) = SessionManager.get_instance().get_cache(
        args["session_id"], "file"
    )
    if base_path is None:
        return False, _("file_collection_failed_colon__file_not_found")
    dic = {}
    dic["user_id"] = args["user_id"]
    dic["etype"] = "file"
    dic["source"] = "wechat"
    dic["addr"] = addr
    ret, ret_emb, info = add_data(dic, base_path)
    return ret, info


CommandManager.get_instance().register(
    Command(msg_file_save, ["收藏文件"], level=LEVEL_NORMAL)
)


def msg_upload_main(args):
    (path, filename) = SessionManager.get_instance().get_cache(
        args["session_id"], "file"
    )
    if path is not None:
        cmd_list = [("收藏文件", "收藏文件")]
        if is_doc_file(path):
            cmd_list += [("总结文件内容", "总结文件内容"), ("文本转音频", "文本转音频")]
        elif is_audio_file(path):
            cmd_list += [("语音识别", "语音识别")]
        return msg_common_select(args["session_id"], cmd_list, detail="收到文件")
    else:
        return True, {
            "type": "text",
            "content": _("please_upload_or_share_a_file_first"),
        }


CommandManager.get_instance().register(
    Command(msg_upload_main, ["上传文件"], level=LEVEL_NORMAL)
)


def msg_file_main(args):
    cmd_list = [
        ("上传文件", "上传文件"),
        ("找文件", "找文件"),
    ]
    return msg_common_select(args["session_id"], cmd_list, detail="文件功能")


CommandManager.get_instance().register(
    Command(msg_file_main, ["文件功能"], level=LEVEL_TOP)
)


def msg_search_detail(args):
    uid = args["user_id"]
    idx = args["content"]
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


def msg_file_search(args):
    if args["content"] == "":
        SessionManager.get_instance().set_cache(
            args["session_id"], "prev_cmd", "找文件"
        )
        return True, {
            "type": "text",
            "content": _("please_enter_what_you're_looking_for"),
        }
    else:
        return search_data(args, dic={"etype": "file"})


CommandManager.get_instance().register(
    Command(
        msg_file_search,
        ["找文件", "查找文件", "查文件", "搜文件", "搜索文件"],
        level=LEVEL_NORMAL,
    )
)


# Audio files
def msg_audio_asr(args):
    ret = SessionManager.get_instance().get_cache(args["session_id"], "file")
    if isinstance(ret, tuple):
        path = ret[0]
        if path is not None:
            # Fetch File Size
            size = os.path.getsize(path)
            if size > 50 * 1024 * 1024:
                return True, {
                    "type": "text",
                    "content": _(
                        "files_larger_than_50mb_are_currently_not_supported_for_recognition"
                    ),
                }
            path_out = re.sub(r"\.(mp3|wav|m4a)$", "_asr.txt", path)
            filename = os.path.basename(path_out)
            logger.debug(f"audio filename: {filename}")
            ret, text = do_asr(path, path_out, debug=True)
            filecache.TmpFileManager.get_instance().add_file(path_out)
            if ret:
                return True, {
                    "type": "file",
                    "content": path_out,
                    "filename": f"{filename}",
                }
            else:
                return True, {"type": "text", "content": text}
    return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}


CommandManager.get_instance().register(
    Command(msg_audio_asr, ["语音识别"], level=LEVEL_NORMAL)
)


def msg_audio_main(args):
    cmd_list = [("语音识别", "语音识别")]
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_audio_main, ["音频功能"], level=LEVEL_NORMAL)
)


# Entries
def msg_record_search(args):
    if args["content"] == "":
        SessionManager.get_instance().set_cache(
            args["session_id"], "prev_cmd", "查找记录"
        )
        return True, {
            "type": "text",
            "content": "请输入待查找内容",
            "user_id": args["user_id"],
            "etype": "record",
        }
    else:
        return search_data(args, dic={"etype": "record"})


CommandManager.get_instance().register(
    Command(
        msg_record_search,
        ["搜索记录", "查找记录", "查找笔记", "查记录"],
        level=LEVEL_NORMAL,
    )
)


def msg_record_input(args):
    if args["content"] == "":
        SessionManager.get_instance().set_cache(args["session_id"], "prev_cmd", "记录")
        return True, {"type": "text", "content": _("please_enter_the_record_content")}
    else:
        dic = {
            "user_id": args["user_id"],
            "etype": "record",
            "raw": args["content"],
            "source": "wechat",
        }
        ret, ret_emb, info = add_data(dic)
        return True, {"type": "text", "content": info}


CommandManager.get_instance().register(
    Command(msg_record_input, ["记录"], level=LEVEL_NORMAL)
)

if is_app_installed("app_record"):
    from app_record.record import get_export_file

    def msg_record_export(args):
        ret, info = get_export_file(args["user_id"])
        if ret:
            file_path = info
            filename = os.path.basename(file_path)
            return True, {
                "type": "file",
                "content": file_path,
                "filename": f"{filename}",
            }
        return True, {"type": "text", "content": info}

    CommandManager.get_instance().register(
        Command(msg_record_export, ["导出记录"], level=LEVEL_NORMAL)
    )


def msg_record_main(args):
    cmd_list = [("记录", "记录"), ("查找记录", "查找记录")]
    if is_app_installed("app_record"):
        cmd_list += [("导出记录", "导出记录")]
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_record_main, ["随手记"], level=LEVEL_TOP)
)


def msg_data_manage(args):
    url = f"{WEB_URL}"
    return True, {"type": "sharing", "content": f"请打开以下链接:\n{url}"}


CommandManager.get_instance().register(
    Command(msg_data_manage, ["管理数据"], level=LEVEL_NORMAL)
)


def msg_data_main(args):
    cmd_list = [("管理数据", "管理数据"), ("查找数据", "查找数据")]
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_data_main, ["我的数据"], level=LEVEL_TOP)
)

# Food

if is_app_installed("app_diet"):
    from app_diet.diet import calc_diet, edit_diet, del_diet

    def msg_diet_analysis(args):
        return True, {
            "type": "text",
            "content": calc_diet(args["content"], args["user_id"]),
        }

    CommandManager.get_instance().register(
        Command(msg_diet_analysis, ["饮食统计"], level=LEVEL_NORMAL)
    )

    def msg_diet_del(args):
        if args["content"] == "":
            SessionManager.get_instance().set_cache(
                args["session_id"], "prev_cmd", "饮食删除"
            )
            return True, {"type": "text", "content": "请输入饮食名称"}
        else:
            ret, detail = del_diet(args["content"], args["user_id"])
            return True, {"type": "text", "content": detail}

    CommandManager.get_instance().register(
        Command(msg_diet_del, ["饮食删除", "删除饮食"], level=LEVEL_NORMAL)
    )

    def msg_diet_edit(args):
        logger.debug(f"msg_diet_edit '{args['content']}'")
        if args["content"] == "":
            SessionManager.get_instance().set_cache(
                args["session_id"], "prev_cmd", "饮食记录"
            )
            return True, {"type": "text", "content": "请输入饮食内容"}
        else:
            ret, detail = edit_diet(args["content"], args["user_id"])
            return True, {"type": "text", "content": detail}

    CommandManager.get_instance().register(
        Command(msg_diet_edit, ["饮食记录", "记饮食"], level=LEVEL_NORMAL)
    )

    def msg_diet_main(args):
        cmd_list = [
            ("饮食统计", "饮食统计"),
            ("饮食删除", "饮食删除"),
            ("饮食记录", "饮食记录"),
        ]
        return msg_common_select(args["session_id"], cmd_list)

    CommandManager.get_instance().register(
        Command(msg_diet_main, ["饮食功能"], level=LEVEL_TOP)
    )

# 语音


def msg_tts_stop(args):
    ret, info = stop_tts(args["user_id"])
    return True, {"type": "text", "request_delay": -1, "content": info}


CommandManager.get_instance().register(
    Command(msg_tts_stop, ["停止"], level=LEVEL_NORMAL)
)


def msg_tts_result(args):
    ret, delay, info = get_tts_result(args["user_id"])

    if ret:
        session = SessionManager.get_instance().get_session(args["session_id"])
        title = session.get_cache("tts_file_title", "转换音频")
        return True, {"type": "audio", "content": info, "filename": f"{title}.mp3"}
    else:
        if delay != -1:
            return True, {"type": "text", "request_delay": delay, "content": info}
        else:
            return True, {"type": "text", "content": info}


CommandManager.get_instance().register(
    Command(msg_tts_result, ["取音频", "获取音频"], level=LEVEL_NORMAL)
)


def msg_tts_convert(args):
    if args["content"] == "":
        SessionManager.get_instance().set_cache(
            args["session_id"], "prev_cmd", "转语音"
        )
        return True, {"type": "text", "content": "请输入转换内容"}
    else:
        content = args["content"].strip()
        if len(content) > 0:
            return run_tts(
                f"文本_{content[:5]}", content, args["user_id"], args["session_id"]
            )
        else:
            return True, {"type": "text", "content": "没有找到相应内容"}


CommandManager.get_instance().register(
    Command(msg_tts_convert, ["转语音", "转音频"], level=LEVEL_NORMAL)
)


def msg_tts_setting(args):
    logger.debug(f"msg_tts_setting '{args['content']}'")
    if args["content"] == "":
        cmd_list = tts_get_voice_and_engine(args["user_id"], "设置语音合成")
        return msg_common_select(args["session_id"], cmd_list)
    else:
        name = args["content"]
        engine_setting = name.strip()
        ret, detail = tts_set_engine(engine_setting, args["user_id"])
        return True, {"type": "text", "content": detail}


CommandManager.get_instance().register(
    Command(
        msg_tts_setting,
        ["设置语音合成", "设置tts", "语音设置", "tts设置", "选择语音"],
        level=LEVEL_NORMAL,
    )
)


def msg_tts_main(args):
    cmd_list = [("设置语音合成", "设置语音合成"), ("转音频", "转音频")]
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_tts_main, ["语音功能"], level=LEVEL_TOP)
)


# Setting


def msg_user_privilege(args):
    user = UserManager.get_instance().get_user(args["user_id"])
    privilege = f"用户级别：{user.get_level_desc()}\n" + user.privilege.get_descript()
    return True, {"type": "text", "content": privilege}


CommandManager.get_instance().register(
    Command(msg_user_privilege, ["用户权限"], level=LEVEL_NORMAL)
)


def msg_resource_usage(args):
    return True, {
        "type": "text",
        "content": "\n"
        + ResourceManager.get_instance().get_usage_summary(args["user_id"]),
    }


CommandManager.get_instance().register(
    Command(msg_resource_usage, ["用量统计"], level=LEVEL_NORMAL)
)


def msg_logout(args):
    return True, {"type": "text", "content": json.dumps({"logout": True})}


CommandManager.get_instance().register(
    Command(msg_logout, ["用户登出"], level=LEVEL_NORMAL)
)


def msg_llm_setting(args):
    logger.debug(f"msg_llm_setting '{args['content']}'")
    user = UserManager.get_instance().get_user(args["user_id"])

    if args["content"] == "":
        llm_setting = user.get("llm_chat_model", DEFAULT_CHAT_LLM)
        logger.debug(f"llm_setting {llm_setting}")
        if user.privilege.b_llm:
            llm_list = get_llm_list()
            cmd_list = []
            for item in llm_list:
                if item["value"] == llm_setting:
                    cmd = (f"{item['label']} *", f"设置语言模型 {item['value']}")
                else:
                    cmd = (f"{item['label']}", f"设置语言模型 {item['value']}")
                cmd_list.append(cmd)
        logger.debug(f"cmd_list {cmd_list}")
        return msg_common_select(args["session_id"], cmd_list)
    else:
        name = args["content"]
        llm_setting = name.strip()
        user.set("llm_chat_model", llm_setting)
        return True, {"type": "text", "content": "设置成功"}


CommandManager.get_instance().register(
    Command(msg_llm_setting, ["设置语言模型", "设置llm"], level=LEVEL_NORMAL)
)


def msg_setting(args):
    cmd_list = [
        ("设置语音合成", "设置语音合成"),
        ("设置语言模型", "设置语言模型"),
        ("用量统计", "用量统计"),
        ("用户权限", "用户权限"),
        ("用户登出", "用户登出"),
    ]
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_setting, ["设置功能"], level=LEVEL_TOP)
)


def msg_help(args):
    commands = CommandManager.get_instance().commands
    cmd_list = []
    for cmd in commands:
        if cmd.level == LEVEL_TOP:
            name = cmd.cmd_list[0]
            cmd_list.append((name, name))
    return msg_common_select(args["session_id"], cmd_list)


CommandManager.get_instance().register(
    Command(msg_help, ["帮助", "命令"], level=LEVEL_NORMAL)
)


def msg_find_cmd(args):
    if args["content"] == "":
        SessionManager.get_instance().set_cache(
            args["session_id"], "prev_cmd", "找命令"
        )
        return True, {"type": "text", "content": "请输入命令关键字"}
    else:
        ret = CommandManager.get_instance().find_cmd(args["user_id"], args["content"])
        ret = [(x, x) for x in ret]
        return msg_common_select(args["session_id"], ret)
        if len(ret) == 0:
            return True, {"type": "text", "content": "匹配失败"}


CommandManager.get_instance().register(
    Command(msg_find_cmd, ["找命令"], level=LEVEL_TOP)
)

# 其它


def msg_kimi(args):
    content = args["content"]
    ret, answer, _ = llm_query(
        args["user_id"], MSG_ROLE, content, "chat", engine_type="kimi", debug=True
    )
    if ret:
        return True, {"type": "text", "content": f"[Kimi] {answer}"}
    else:
        return True, {"type": "text", "content": f"Kimi调用失败"}


CommandManager.get_instance().register(Command(msg_kimi, ["KIMI"], level=LEVEL_NORMAL))


def msg_gpt4(args):
    content = args["content"]
    if content is not None:
        content = content  # Miswriting possible
    ret, answer, _ = llm_query(
        args["user_id"], MSG_ROLE, content, "chat", engine_type="gpt-4o", debug=True
    )
    if ret:
        return True, {"type": "text", "content": f"[gpt-4o] {answer}"}
    else:
        return True, {"type": "text", "content": f"gpt-4o调用失败"}


CommandManager.get_instance().register(
    Command(msg_gpt4, ["GPT4", "GPT-4"], level=LEVEL_NORMAL)
)


def msg_gemini(args):
    content = args["content"]
    ret, answer, _ = llm_query(
        args["user_id"], MSG_ROLE, content, "chat", engine_type="gemini", debug=True
    )
    if ret:
        return True, {"type": "text", "content": f"[Gemini] {answer}"}
    else:
        return True, {"type": "text", "content": f"Gemini调用失败"}


CommandManager.get_instance().register(
    Command(msg_gemini, ["GEMINI"], level=LEVEL_NORMAL)
)

if is_app_installed("app_translate"):
    from app_translate.translate import add_translate

    def msg_translate(args):
        ret, detail = add_translate(args["content"], args["user_id"])
        return True, {"type": "text", "content": detail}

    CommandManager.get_instance().register(
        Command(msg_translate, ["翻译"], level=LEVEL_NORMAL)
    )


def msg_data_search(args):  # later maybe add to help main list
    if args["content"] == "":
        SessionManager.get_instance().set_cache(
            args["session_id"], "prev_cmd", "找数据"
        )
        return True, {"type": "text", "content": "请输入待查找内容"}
    else:
        return search_data(args)


CommandManager.get_instance().register(
    Command(
        msg_data_search,
        ["找数据", "查找数据", "查数据", "搜数据", "搜索数据"],
        level=LEVEL_NORMAL,
    )
)


def do_message(args):
    """
    Handling WeChat Chat Entry
    """
    try:
        content = args["content"]
        if pd.isnull(content):
            return False, {"type": "text", "content": _("nothing_entered")}
        ret = False
        detail = {"type": "text", "content": _("unrecognized_command")}
        prev_cmd = SessionManager.get_instance().get_cache(
            args["session_id"], "prev_cmd"
        )

        if is_valid_url(content):  # Enter Website
            ret, detail = msg_web_main(args)
        if (
            not ret and prev_cmd is not None
        ):  # The previous conversation was asking the user to enter information
            args["content"] = prev_cmd + " " + args["content"]
            prev_cmd = SessionManager.get_instance().set_cache(
                args["session_id"], "prev_cmd", None
            )
            ret, detail = CommandManager.get_instance().msg_do_command(args)
        if not ret:  # Enter a numerical value
            ret, detail = parse_select_number(args)
        if not ret:  # Enter Command
            ret, detail = CommandManager.get_instance().msg_do_command(args)
        logger.info(f"content:{content} ret:{ret} detail:{detail}")
        if not ret:
            ret, detail = do_chat(args)
        save_message(content, args, detail)
        return True, detail
    except Exception as e:
        traceback.print_exc()
        logger.warning(f"do_message error {e}")
        return True, {"type": "text", "content": _("failed_to_process_information")}


def parse_select_number(args):
    content = args["content"]
    content = content.strip().replace(".", "")
    content = replace_fullwidth_numbers_with_halfwidth(content)
    if content.isdigit():
        idx = int(content)
        next_cmd = SessionManager.get_instance().get_cache(
            args["session_id"], "next_cmd"
        )
        logger.info(f"next_cmd {next_cmd} idx {idx}")
        if next_cmd is None or len(next_cmd) < idx:
            return False, _("no_optional_commands")
        args["content"] = next_cmd[idx - 1][1]  # cmd value
        return CommandManager.get_instance().msg_do_command(args)
    return False, _("not_a_number")


def msg_recv_file(base_path, filename, args):
    """
    Parse the uploaded file and store the data in the database
    """
    logger.debug(f"parse_file: {base_path}")
    SessionManager.get_instance().set_cache(
        args["session_id"], "file", (base_path, filename)
    )
    ret = False
    dic = {}
    if support_file(base_path):
        ret, dic = msg_upload_main(args)
    if ret:
        return True, dic["content"]
    else:
        if "content" in dic:
            return True, dic["content"]
        else:
            return False, _("the_file_type_is_not_valid_or_not_supported")


def msg_add_url(url, args, status):
    ret, base_path, info = add_url(url, args, status)
    if ret and info == "pdf":
        return msg_recv_file(base_path, None, args)
    else:
        return ret, info


def search_data(args, dic={}):
    condition = {"user_id": args["user_id"]}
    condition.update(dic)
    if "content" in args and len(args["content"]) > 0:
        keyword = args["content"]
    else:
        keyword = None
    logger.info(f"condition {condition}")
    queryset = get_entry_list(keyword, condition, 5)
    df = pd.DataFrame(queryset.values())
    arr = []
    for idx, item in df.iterrows():
        label = regular_str(item["title"], del_enter=True, max_length=25)
        value = CMD_INNER_GET + " " + str(item["idx"])
        arr.append((label, value))

    if len(arr) == 0:
        return True, {"type": "text", "content": _("no_content_found_1727252424")}
    elif len(arr) == 1:
        args["content"] = arr[0][1]
        return CommandManager.get_instance().msg_do_command(args)
    else:
        return msg_common_select(args["session_id"], arr)


CommandManager.get_instance().check_conflict()
