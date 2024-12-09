from typing import List, Callable
from loguru import logger
from django.utils.translation import gettext as _
import app_message.user_manager as user_manager
from app_message.command import CommandManager, Command, LEVEL_NORMAL, LEVEL_TOP, msg_common_select
from backend.common.speech.tts import (
    stop_tts,
    get_tts_result,
    run_tts,
    tts_get_voice_and_engine,
    tts_set_engine,
)
from backend.common.utils.web_tools import (
    regular_url,
    get_url_content,
    get_web_abstract,
)
from backend.common.utils.file_tools import (
    support_file,
    is_audio_file,
    is_doc_file,
    get_file_content,
    get_file_abstract,
    get_ext,
)
from app_message.function import regular_title
from app_dataforge.misc_tools import add_url

class BaseAgent:
    def __init__(self):
        self.agent_name = "BaseAgent"
        self.instructions = "Determine which function to call based on the user's input."

    def get_functions(self) -> List[Callable]:
        ret = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            #print("attr_name", attr_name)
            if callable(attr) and attr_name.startswith('_afunc_'):
                print('agent func:', attr_name)
                ret.append(attr)
        return ret
    
    def add_commands(self): # later remove
        funcs = self.get_functions()
        cmd_list = []
        for func in funcs:
            print(func.__doc__)
            CommandManager.get_instance().register(
                Command(func, [func.__doc__], level=LEVEL_NORMAL)
            )
            cmd_list.append((func.__doc__, func.__doc__))

        def msg_main(sdata):
            return msg_common_select(sdata, cmd_list)

        CommandManager.get_instance().register(
            Command(msg_main, [self.agent_name], level=LEVEL_TOP)
        )


class UserAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "UserAgent"
        self.instructions = "This agent can register, login, and change passwords."

    @staticmethod
    def _afunc_register(user_id: str, password: str, context_variables: dict) -> dict:
        """User registration tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password."""
        print('register', user_id, password, context_variables)
        dic = user_manager.register(user_id, password)
        if dic is not None and 'status' in dic and dic['status']:
            if context_variables is not None:
                context_variables['user_id'] = user_id
                context_variables['password'] = password
                context_variables['status'] = 'wait_login'
            return True, "注册成功"
        else:
            if dic is not None and 'info' in dic:
                print('@@@@@@@@@@@@@@@@@@@@', dic['info'])
                return False, dic['info']
            else:
                print("@@@@@@@@@@@@@@@@@@@@@ 2", dic)
                return False, "注册失败"

    @staticmethod
    def _afunc_login(user_id: str, password: str, context_variables: dict) -> dict:
        """User login tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password. """
        print('login', user_id, password, context_variables)
        if context_variables is not None:
            context_variables['user_id'] = user_id
            context_variables['password'] = password
            context_variables['status'] = 'wait_login'
        ret = {"user_id": user_id, "password": password}
        return True, ret

    @staticmethod
    def _afunc_change_password(user_id: str, password_old: str, password_new: str, context_variables: dict) -> dict:
        """User password change tool: if no username, old password, or new password is provided, set them as the string ''; if only one password is provided, set the old password as ''"""
        print('change_password', user_id, password_old, password_new, context_variables)
        dic = user_manager.change_password(user_id, password_old, password_new)
        if dic is not None and 'status' in dic and dic['status']:
            if context_variables is not None:
                context_variables['user_id'] = user_id
                context_variables['password'] = password_new
            return True, "修改成功"
        else:
            if dic is not None and 'info' in dic:
                return False, dic['info']
            else:
                return False, "修改失败"
    

class OthersAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "OthersAgent"
        self.instructions = "请调用默认处理函数"

    @staticmethod
    def _afunc_chat(string: str, context_variables: dict) -> dict:
        """默认处理函数"""
        print("@@@@@ chat", context_variables)
        if 'isLoggedIn' in context_variables and context_variables['isLoggedIn']:
            return {"response": "继续与用户对话: " + string}
        if context_variables is not None:
            context_variables['status'] = 'need_login'
        return {"response": "请先登录"}
    

from app_diet.diet import calc_diet, edit_diet, del_diet

class DietAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "饮食功能"
        self.instructions = "处理饮食记录、饮食删除、饮食统计"

    @staticmethod
    def _afunc_diet_analysis(sdata):
        """饮食统计"""
        return True, {
            "type": "text",
            "content": calc_diet(sdata.current_content, sdata.user_id),
        }

    @staticmethod
    def _afunc_diet_del(sdata):
        """删除饮食"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "饮食删除")
            return True, {"type": "text", "content": "请输入饮食名称"}
        else:
            ret, detail = del_diet(sdata.current_content, sdata.user_id)
            return True, {"type": "text", "content": detail}


    @staticmethod
    def _afunc_diet_edit(sdata):
        """记录饮食"""
        logger.debug(f"msg_diet_edit '{sdata.current_content}'")
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "饮食记录")
            return True, {"type": "text", "content": "请输入饮食内容"}
        else:
            ret, detail = edit_diet(sdata.current_content, sdata.user_id)
            return True, {"type": "text", "content": detail}

import os
from app_record.record import get_export_file
from app_message.function import search_data
from app_dataforge.entry import add_data

class RecordAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "随手记"
        self.instructions = "记录、查找记录、导出记录"

    @staticmethod
    def _afunc_record_search(sdata):
        """查找记录"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "查找记录")
            return True, {
                "type": "text",
                "content": "请输入待查找内容",
                "user_id": sdata.user_id,
                "etype": "record",
            }
        else:
            return search_data(sdata, dic={"etype": "record"})

    @staticmethod
    def _afunc_record_input(sdata):
        """记录"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "记录")
            return True, {"type": "text", "content": _("please_enter_the_record_content")}
        else:
            dic = {
                "user_id": sdata.user_id,
                "etype": "record",
                "raw": sdata.current_content,
                "source": "wechat",
            }
            ret, ret_emb, info = add_data(dic)
            return True, {"type": "text", "content": info}


    @staticmethod
    def _afunc_record_export(sdata):
        """导出记录"""
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

from backend.common.user.user import *
from backend.common.user.resource import *
from backend.common.llm.llm_tools import DEFAULT_CHAT_LLM, get_llm_list

class SettingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "设置"
        self.instructions = "用户权限、用量统计、语言模型设置、语音合成设置、用户登出"

    @staticmethod
    def _afunc_user_privilege(sdata):
        """用户权限"""
        user = UserManager.get_instance().get_user(sdata.user_id)
        privilege = f"用户级别：{user.get_level_desc()}\n" + user.privilege.get_descript()
        return True, {"type": "text", "content": privilege}

    @staticmethod
    def _afunc_resource_usage(sdata):
        """用量统计"""
        return True, {
            "type": "text",
            "content": "\n"
            + ResourceManager.get_instance().get_usage_summary(sdata.user_id),
        }

    @staticmethod
    def _afunc_llm_setting(sdata):
        """设置语言模型"""
        logger.debug(f"msg_llm_setting '{sdata.current_content}'")
        user = UserManager.get_instance().get_user(sdata.user_id)

        if sdata.current_content == "":
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
            return msg_common_select(sdata, cmd_list)
        else:
            name = sdata.current_content
            llm_setting = name.strip()
            user.set("llm_chat_model", llm_setting)
            return True, {"type": "text", "content": "设置成功"}

    @staticmethod
    def _afunc_tts_setting(sdata):
        """设置语音合成"""
        logger.debug(f"msg_tts_setting '{sdata.current_content}'")
        if sdata.current_content == "":
            cmd_list = tts_get_voice_and_engine(sdata.user_id, "设置语音合成")
            return msg_common_select(sdata, cmd_list)
        else:
            name = sdata.current_content
            engine_setting = name.strip()
            ret, detail = tts_set_engine(engine_setting, sdata.user_id)
            return True, {"type": "text", "content": detail}

    @staticmethod
    def _afunc_logout(args):
        """用户登出"""
        return True, {"type": "text", "content": json.dumps({"logout": True})}

import pandas as pd

class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "网页处理"
        self.instructions = "收藏网页、设置待看网页、总结网页内容、获取文本内容"

    @staticmethod
    def _afunc_web_collect(sdata):
        """收藏网页"""
        url = sdata.get_cache("url")
        if url is not None:
            ret, info = msg_add_url(url, sdata, "collect")
            return ret, {"type": "text", "content": info}
        if pd.notna(sdata.current_content):
            ret, info = msg_add_url(sdata.current_content, sdata, "collect")
            return ret, {"type": "text", "content": info}
        return True, {"type": "text", "content": _("no_urls_dot_")}

    @staticmethod
    def _afunc_web_todo(sdata):
        """设置待看网页"""
        url = sdata.get_cache("url")
        if url is not None:
            ret, info = msg_add_url(url, sdata, "todo")
            return ret, {"type": "text", "content": info}
        if pd.notna(sdata.current_content):
            ret, info = msg_add_url(sdata.current_content, sdata, "todo")
            return ret, {"type": "text", "content": info}
        return True, {"type": "text", "content": _("no_urls_dot_")}

    @staticmethod
    def _afunc_web_extract(sdata):
        """总结网页内容"""
        url = sdata.get_cache("url")
        logger.debug(f"msg_web_extract {url}")
        if url is not None:
            # ret, detail = get_url_detail(url)
            detail = get_web_abstract(sdata.user_id, url)
            if detail is not None:
                return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("failed_to_fetch_webpages")}

    @staticmethod
    def _afunc_web_content(sdata):
        """获取文本内容"""
        url = sdata.get_cache("url")
        title, content = get_url_content(url)
        if content is not None:
            return True, {"type": "text", "content": content}
        return True, {"type": "text", "content": _("no_content_found")}

    @staticmethod
    def _afunc_web_audio(sdata):
        """网页转音频"""
        url = sdata.get_cache("url")
        title, content = get_url_content(url)
        title = regular_title(title)
        if title is not None:
            title = f"网页_{title[:10]}"
            return msg_run_tts(title, content, sdata)
        else:
            return True, {"type": "text", "content": _("page_not_found")}

WEB_URL = f"http://{os.getenv('FRONTEND_ADDR_OUTER', '')}:{os.getenv('FRONTEND_PORT_OUTER', '8084')}"

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "数据管理"
        self.instructions = "管理数据、查找数据、搜索文件、搜索待读的网页、搜索收藏的网页、搜索网页"

    @staticmethod
    def _afunc_data_search(sdata):
        """搜索数据"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "找数据")
            return True, {"type": "text", "content": "请输入待查找内容"}
        else:
            return search_data(sdata)

    @staticmethod
    def _afunc_file_search(sdata):
        """搜索文件"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "搜索文件")
            return True, {
                "type": "text",
                "content": _("please_enter_what_you're_looking_for"),
            }
        else:
            return search_data(sdata, dic={"etype": "file"})
        
    @staticmethod
    def _afunc_web_my_todo(sdata):
        """搜索待读的网页"""
        return search_data(sdata, dic={"status": "todo", "etype": "web"})

    @staticmethod
    def _afunc_web_my_collect(sdata):
        """搜索收藏的网页"""
        return search_data(sdata, dic={"status": "collect", "etype": "web"})

    @staticmethod
    def _afunc_web_search(sdata):
        """搜索网页"""
        return search_data(sdata, dic={"etype": "web"})

    @staticmethod
    def _afunc_data_manage(args):
        """管理数据"""
        url = f"{WEB_URL}"
        return True, {"type": "sharing", "content": f"请打开以下链接:\n{url}"}


class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "文件处理"
        self.instructions = "提取文件内容、文本转音频、收藏文件"

    @staticmethod
    def _afunc_file_extract(sdata):
        """总结文件内容"""
        logger.debug("in msg_extract_file")
        data = sdata.get_cache("file")
        ret, detail = get_file_abstract(data, sdata.user_id)
        if ret:
            return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}

    @staticmethod
    def _afunc_file_tts(sdata):
        """文本转音频"""
        data = sdata.get_cache("file")
        ret, path, title, content = get_file_content(data)
        if ret:
            return msg_run_tts(title, content, sdata)
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}


    @staticmethod
    def _afunc_file_save(sdata):
        """收藏文件"""
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

import re
from backend.common.files import utils_filemanager, filecache
from backend.common.speech.asr_tools import do_asr

class AudioAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "语音功能"
        self.instructions = "音频识别、音频转文本"

    @staticmethod
    def _afunc_tts_convert(sdata):
        """文本转音频"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "文本转音频")
            return True, {"type": "text", "content": "请输入转换内容"}
        else:
            content = sdata.current_content.strip()
            if len(content) > 0:
                return msg_run_tts(f"文本_{content[:5]}", content, sdata)
            else:
                return True, {"type": "text", "content": "没有找到相应内容"}

    @staticmethod
    def _afunc_tts_stop(sdata):
        """停止语音合成"""
        ret, info = stop_tts(sdata.user_id)
        return True, {"type": "text", "request_delay": -1, "content": info}

    @staticmethod
    def _afunc_tts_result(sdata):
        """获取音频"""
        ret, delay, info = get_tts_result(sdata.user_id)

        if ret:
            title = sdata.get_cache("tts_file_title", "转换音频")
            return True, {"type": "audio", "content": info, "filename": f"{title}.mp3"}
        else:
            if delay != -1:
                return True, {"type": "text", "request_delay": delay, "content": info}
            else:
                return True, {"type": "text", "content": info}

    @staticmethod
    def _afunc_audio_asr(sdata):
        """音频识别"""
        ret = sdata.get_cache("file")
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

from app_translate.translate import translate_word

class TranslateAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "英语学习"
        self.instructions = "翻译"
 
    @staticmethod
    def _afunc_translate(sdata):
        """翻译"""
        ret, en_regular, tranlation = translate_word(sdata.current_content, sdata.user_id)
        if ret:
            return True, {"type": "text", "content": tranlation}
        else:
            return True, {"type": "text", "content": _("translation_failed")}


from app_message.command import CommandManager, LEVEL_TOP

class HelpAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "帮助功能"
        self.instructions = ""

    @staticmethod
    def _afunc_help(sdata):
        """帮助"""
        commands = CommandManager.get_instance().commands
        cmd_list = []
        for cmd in commands:
            if cmd.level == LEVEL_TOP:
                name = cmd.cmd_list[0]
                cmd_list.append((name, name))
        return msg_common_select(sdata, cmd_list)


    @staticmethod
    def _afunc_find_cmd(sdata):
        """找命令"""
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "找命令")
            return True, {"type": "text", "content": "请输入命令关键字"}
        else:
            ret = CommandManager.get_instance().find_cmd(sdata.user_id, sdata.current_content)
            ret = [(x, x) for x in ret]
            return msg_common_select(sdata, ret)
            if len(ret) == 0:
                return True, {"type": "text", "content": "匹配失败"}

from backend.common.llm.llm_hub import llm_query
MSG_ROLE = "You're a smart assistant"

class LLMAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "LLM"
        self.instructions = "调用特定语言模型"

    @staticmethod
    def _afunc_kimi(sdata):
        """Kimi"""
        content = sdata.current_content
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="kimi", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[Kimi] {answer}"}
        else:
            return True, {"type": "text", "content": f"Kimi调用失败"}


    @staticmethod
    def _afunc_gpt4(sdata):
        """GPT-4"""
        content = sdata.current_content
        if content is not None:
            content = content  # Miswriting possible
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="gpt-4o", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[gpt-4o] {answer}"}
        else:
            return True, {"type": "text", "content": f"gpt-4o调用失败"}



    @staticmethod
    def _afunc_gemini(sdata):
        """Gemini"""
        content = sdata.current_content
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="gemini", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[Gemini] {answer}"}
        else:
            return True, {"type": "text", "content": f"Gemini调用失败"}


def msg_run_tts(title, content, sdata): # later rename
    sdata.set_cache("tts_file_title", title)
    return run_tts(title, content, sdata.user_id)

def msg_add_url(url, sdata, status):
    # 暂时不处理 pdf 的情况, later add file support
    ret, base_path, info = add_url(url, sdata.args, status)
    # if ret and info == "pdf":
    if False:
        return msg_recv_file(base_path, None, sdata)
    else:
        return ret, info
