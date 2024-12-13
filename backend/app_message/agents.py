from loguru import logger
from django.utils.translation import gettext as _
import app_message.user_manager as user_manager
from app_message.command import CommandManager, LEVEL_TOP, msg_common_select
from backend.common.speech.tts import (
    stop_tts,
    get_tts_result,
    run_tts,
    tts_get_voice_and_engine,
    tts_set_engine,
)
from backend.common.utils.web_tools import (
    get_url_content,
    get_web_abstract,
)
from backend.common.utils.file_tools import (
    get_file_content,
    get_file_abstract,
)
from app_message.function import regular_title
from app_dataforge.misc_tools import add_url
from app_message.agent_core import BaseAgent, BaseAgentManager

class UserAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "用户功能"
        self.instructions = "This agent can register, login, and change passwords, 如果输入与此无关的内容，则返回请用户先登录再聊天."

    @staticmethod
    def _afunc_register(context_variables: dict, user_id: str, password: str) -> dict:
        """User registration tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password."""
        print('register', user_id, password, context_variables)
        dic = user_manager.register(user_id, password)
        if dic is not None and 'status' in dic and dic['status']:
            if context_variables is not None and 'sdata' in context_variables:
                context_variables['sdata'].set_cache('user_id', user_id)
                context_variables['sdata'].set_cache('password', password)
            return True, "注册成功"
        else:
            if dic is not None and 'info' in dic:
                print('@@@@@@@@@@@@@@@@@@@@', dic['info'])
                return False, dic['info']
            else:
                print("@@@@@@@@@@@@@@@@@@@@@ 2", dic)
                return False, "注册失败"

    @staticmethod
    def _afunc_login(context_variables: dict, user_id: str, password: str) -> dict:
        """User login tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password. """
        print('login', user_id, password, context_variables)
        if context_variables is not None and 'sdata' in context_variables:
            context_variables['sdata'].set_cache('user_id', user_id)
            context_variables['sdata'].set_cache('password', password)
        ret = {"user_id": user_id, "password": password}
        return True, ret

    @staticmethod
    def _afunc_change_password(context_variables: dict, user_id: str, password_old: str, password_new: str) -> dict:
        """User password change tool: if no username, old password, or new password is provided, set them as the string ''; if only one password is provided, set the old password as ''"""
        print('change_password', user_id, password_old, password_new, context_variables)
        dic = user_manager.change_password(user_id, password_old, password_new)
        if dic is not None and 'status' in dic and dic['status']:
            if context_variables is not None and 'sdata' in context_variables:
                context_variables['sdata'].set_cache('user_id', user_id)
                context_variables['sdata'].set_cache('password', password_new)
            return True, "修改成功"
        else:
            if dic is not None and 'info' in dic:
                return False, dic['info']
            else:
                return False, "修改失败"
            

    @staticmethod 
    def _afunc_logout(context_variables: dict):
        """User logout tool"""
        return True, {"type": "text", "content": json.dumps({"logout": True})}


from app_diet.diet import calc_diet, edit_diet, del_diet

class DietAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "饮食功能"
        self.instructions = "处理饮食记录、饮食删除、饮食统计"

    @staticmethod
    def _afunc_diet_analysis(context_variables: dict, content: str = None):
        """饮食统计"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        return True, {
            "type": "text",
            "content": calc_diet(content, sdata.user_id),
        }

    @staticmethod
    def _afunc_diet_del(context_variables: dict, content: str = None):
        """删除饮食"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
            sdata.set_cache("prev_cmd", "饮食删除")
            return True, {"type": "text", "content": "请输入饮食名称"}
        else:
            ret, detail = del_diet(content, sdata.user_id)
            return True, {"type": "text", "content": detail}


    @staticmethod
    def _afunc_diet_edit(context_variables: dict, content: str = None):
        """记录饮食"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        logger.debug(f"msg_diet_edit '{content}'")
        if content == "":
            sdata.set_cache("prev_cmd", "饮食记录")
            return True, {"type": "text", "content": "请输入饮食内容"}
        else:
            ret, detail = edit_diet(content, sdata.user_id)
            return True, {"type": "text", "content": detail}

import os
from app_record.record import get_export_file
from app_message.function import search_data
from app_dataforge.entry import add_data

class RecordAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "RecordAgent"
        self.instructions = "本代理提供：记录、查找记录、导出记录功能，请按需选择工具。"

    @staticmethod
    def _afunc_record_search(context_variables: dict, content: str = None):
        """查找记录"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
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
    def _afunc_record_input(context_variables: dict, content: str = None):
        """记录"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
            sdata.set_cache("prev_cmd", "记录")
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


    @staticmethod
    def _afunc_record_export(context_variables: dict):
        """导出记录"""
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

from backend.common.user.user import *
from backend.common.user.resource import *
from backend.common.llm.llm_tools import DEFAULT_CHAT_LLM, get_llm_list

class SettingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "设置"
        self.instructions = "用户权限、用量统计、语言模型设置、语音合成设置"

    @staticmethod
    def _afunc_user_privilege(context_variables: dict):
        """用户权限"""
        sdata = context_variables["sdata"]
        user = UserManager.get_instance().get_user(sdata.user_id)
        privilege = f"用户级别：{user.get_level_desc()}\n" + user.privilege.get_descript()
        return True, {"type": "text", "content": privilege}

    @staticmethod
    def _afunc_resource_usage(context_variables: dict):
        """用量统计"""
        sdata = context_variables["sdata"]
        return True, {
            "type": "text",
            "content": "\n"
            + ResourceManager.get_instance().get_usage_summary(sdata.user_id),
        }

    @staticmethod
    def _afunc_llm_setting(context_variables: dict, content: str = None):
        """设置语言模型"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content        
        logger.debug(f"msg_llm_setting '{content}'")
        user = UserManager.get_instance().get_user(sdata.user_id)

        if content == "":
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
            name = content
            llm_setting = name.strip()
            user.set("llm_chat_model", llm_setting)
            return True, {"type": "text", "content": "设置成功"}

    @staticmethod
    def _afunc_tts_setting(context_variables: dict, content: str = None):
        """设置语音合成"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content           
        logger.debug(f"msg_tts_setting '{content}'")
        if content == "":
            cmd_list = tts_get_voice_and_engine(sdata.user_id, "设置语音合成")
            return msg_common_select(sdata, cmd_list)
        else:
            name = content
            engine_setting = name.strip()
            ret, detail = tts_set_engine(engine_setting, sdata.user_id)
            return True, {"type": "text", "content": detail}


import pandas as pd

class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "网页处理"
        self.instructions = "本代理提供：收藏网页、设置待看网页、总结网页内容、获取文本内容，网页转音频, 网页功能列表；如果未指定具体操作，则调用网页功能列表。"

    @staticmethod
    def _afunc_web_op(context_variables: dict, web_addr: str = None):
        """网页功能列表"""
        sdata = context_variables["sdata"]
        sdata.current_content = web_addr
        return msg_web_main(sdata)

    @staticmethod
    def _afunc_web_collect(context_variables: dict, content: str = None):
        """收藏网页"""
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

    @staticmethod
    def _afunc_web_todo(context_variables: dict, content: str = None):
        """设置待看网页"""
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

    @staticmethod
    def _afunc_web_extract(context_variables: dict):
        """总结网页内容"""
        sdata = context_variables["sdata"]
        url = sdata.get_cache("url")
        logger.debug(f"msg_web_extract {url}")
        if url is not None:
            # ret, detail = get_url_detail(url)
            detail = get_web_abstract(sdata.user_id, url)
            if detail is not None:
                return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("failed_to_fetch_webpages")}

    @staticmethod
    def _afunc_web_content(context_variables: dict):
        """获取文本内容"""
        sdata = context_variables["sdata"]
        url = sdata.get_cache("url")
        title, content = get_url_content(url)
        if content is not None:
            return True, {"type": "text", "content": content}
        return True, {"type": "text", "content": _("no_content_found")}

    @staticmethod
    def _afunc_web_audio(context_variables: dict):
        """网页转音频"""
        sdata = context_variables["sdata"]
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
    def _afunc_data_search(context_variables: dict, content: str = None):
        """搜索数据"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "找数据")
            return True, {"type": "text", "content": "请输入待查找内容"}
        else:
            return search_data(sdata)

    @staticmethod
    def _afunc_file_search(context_variables: dict, content: str = None):
        """搜索文件"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", "搜索文件")
            return True, {
                "type": "text",
                "content": _("please_enter_what_you're_looking_for"),
            }
        else:
            return search_data(sdata, dic={"etype": "file"})
        
    @staticmethod
    def _afunc_web_my_todo(context_variables: dict, content: str = None):
        """搜索待读的网页"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"status": "todo", "etype": "web"})

    @staticmethod
    def _afunc_web_my_collect(context_variables: dict, content: str = None):
        """搜索收藏的网页"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"status": "collect", "etype": "web"})

    @staticmethod
    def _afunc_web_search(context_variables: dict, content: str = None):
        """搜索网页"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        return search_data(sdata, dic={"etype": "web"})

    @staticmethod
    def _afunc_data_manage(context_variables: dict):
        """管理数据"""
        url = f"{WEB_URL}"
        return True, {"type": "sharing", "content": f"请打开以下链接:\n{url}"}


class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "文件处理"
        self.instructions = "提取文件内容、文本转音频、收藏文件"

    @staticmethod
    def _afunc_file_extract(context_variables: dict):
        """总结文件内容"""
        logger.debug("in msg_extract_file")
        sdata = context_variables["sdata"]
        data = sdata.get_cache("file")
        ret, detail = get_file_abstract(data, sdata.user_id)
        if ret:
            return True, {"type": "text", "content": detail}
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}

    @staticmethod
    def _afunc_file_tts(context_variables: dict):
        """文本转音频"""
        sdata = context_variables["sdata"]
        data = sdata.get_cache("file")
        ret, path, title, content = get_file_content(data)
        if ret:
            return msg_run_tts(title, content, sdata)
        return True, {"type": "text", "content": _("please_upload_or_share_a_file_first")}


    @staticmethod
    def _afunc_file_save(context_variables: dict):
        """收藏文件"""
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

import re
from backend.common.files import filecache
from backend.common.speech.asr_tools import do_asr

class AudioAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = "语音功能"
        self.instructions = "音频识别、音频转文本"

    @staticmethod
    def _afunc_tts_convert(context_variables: dict, content: str = None):
        """文本转音频"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
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
    def _afunc_tts_stop(context_variables: dict):
        """停止语音合成"""
        sdata = context_variables["sdata"]
        ret, info = stop_tts(sdata.user_id)
        return True, {"type": "text", "request_delay": -1, "content": info}

    @staticmethod
    def _afunc_tts_result(context_variables: dict):
        """获取音频"""
        sdata = context_variables["sdata"]
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
    def _afunc_audio_asr(context_variables: dict):
        """音频识别"""
        sdata = context_variables["sdata"]
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
        self.instructions = "支持翻译等功能"
 
    @staticmethod
    def _afunc_translate(context_variables: dict, content: str = None):
        """翻译"""
        sdata = context_variables["sdata"]
        if content is not None:
            ret, en_regular, tranlation = translate_word(content, sdata.user_id)
        else:
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
        self.instructions = "本代理提供：显示帮助列表、找命令功能。请按需选择工具"

    @staticmethod
    def _afunc_help(context_variables: dict):
        """帮助列表"""
        sdata = context_variables["sdata"]
        commands = CommandManager.get_instance().commands
        cmd_list = []
        for cmd in commands:
            if cmd.level == LEVEL_TOP:
                name = cmd.cmd_list[0]
                cmd_list.append((name, name))
        return msg_common_select(sdata, cmd_list)


    @staticmethod
    def _afunc_find_cmd(context_variables: dict, content: str = None): # pass
        """找命令"""
        sdata = context_variables["sdata"]
        if content is None and sdata.current_content == "":
            sdata.set_cache("prev_cmd", "找命令")
            return True, {"type": "text", "content": "请输入命令关键字"}
        else:
            if content is not None:
                logger.debug(f"find_cmd {content}")
                ret = CommandManager.get_instance().find_cmd(sdata.user_id, content)
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
    def _afunc_kimi(context_variables: dict, content: str = None):
        """Kimi"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="kimi", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[Kimi] {answer}"}
        else:
            return True, {"type": "text", "content": f"Kimi调用失败"}


    @staticmethod
    def _afunc_gpt4(context_variables: dict, content: str = None):
        """GPT-4"""
        sdata = context_variables["sdata"]
        if content is None:
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
    def _afunc_gemini(context_variables: dict, content: str = None):
        """Gemini"""
        sdata = context_variables["sdata"]
        if content is None:
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

from backend.common.utils.sys_tools import is_app_installed

class AllAgentManager(BaseAgentManager):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AllAgentManager()
        return cls._instance
    
    def __init__(self):
        super().__init__()
        self.add_agent(WebAgent())
        self.add_agent(DataAgent())  
        self.add_agent(AudioAgent())
        self.add_agent(SettingAgent())
        self.add_agent(FileAgent())
        self.add_agent(HelpAgent())
        self.add_agent(UserAgent())
        self.add_agent(LLMAgent()) # tmp
        
        if is_app_installed("app_record"):
            self.add_agent(RecordAgent())
            
        if is_app_installed("app_diet"):
            self.add_agent(DietAgent())
            
        if is_app_installed("app_translate"):
            self.add_agent(TranslateAgent())


class UserAgentManager(BaseAgentManager):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UserAgentManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.add_agent(UserAgent())

from backend.common.utils.web_tools import (
    regular_url,
    get_url_content,
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
            for func in WebAgent().get_functions():
                cmd_list.append((func.__doc__, func.__doc__))
            return msg_common_select(
                sdata,
                cmd_list=cmd_list,
                detail=f"收到网页，正文共{length}字",
            )
    return True, {"type": "text", "content": _("please_enter_the_url_or_share_the_page_with_me")}
