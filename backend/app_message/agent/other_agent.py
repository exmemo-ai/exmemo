import os
from loguru import logger
from django.utils.translation import gettext as _
from app_message.command import CommandManager, LEVEL_TOP, msg_common_select
from backend.common.speech.tts import (
    stop_tts,
    get_tts_result,
    run_tts
)
from app_diet.diet import calc_diet, edit_diet, del_diet
from app_message.agent.base_agent import BaseAgent, agent_function, DEFAULT_INSTRUCTIONS

class DietAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("diet_management")
        self.instructions = "Handle diet records, diet deletion, and diet statistics. " + DEFAULT_INSTRUCTIONS

    @agent_function(_("diet_statistics"))
    def _afunc_diet_analysis(context_variables: dict, content: str = None):
        """Diet analysis"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        return True, {
            "type": "text",
            "content": calc_diet(content, sdata.user_id),
        }

    @agent_function(_("delete_diet"))
    def _afunc_diet_del(context_variables: dict, content: str = None):
        """Delete diet"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        if content == "":
            sdata.set_cache("prev_cmd", _("delete_diet"))
            return True, {"type": "text", "content": _("please_enter_diet_name")}
        else:
            ret, detail = del_diet(content, sdata.user_id)
            return True, {"type": "text", "content": detail}


    @agent_function(_("record_diet"))
    def _afunc_diet_edit(context_variables: dict, content: str = None):
        """Record diet"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        logger.debug(f"msg_diet_edit '{content}'")
        if content == "":
            sdata.set_cache("prev_cmd", _("record_diet"))
            return True, {"type": "text", "content": _("please_enter_diet_content")}
        else:
            ret, detail = edit_diet(content, sdata.user_id)
            return True, {"type": "text", "content": detail}

import re
from backend.common.files import filecache
from backend.common.speech.asr_tools import do_asr

class AudioAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("voice_assistant")
        self.instructions = "Audio recognition and text-to-speech conversion. " + DEFAULT_INSTRUCTIONS

    @agent_function(_("text_to_audio"))
    def _afunc_tts_convert(context_variables: dict, content: str = None):
        """Text to speech"""
        sdata = context_variables["sdata"]
        if content is not None:
            sdata.current_content = content
        if sdata.current_content == "":
            sdata.set_cache("prev_cmd", _("text_to_audio"))
            return True, {"type": "text", "content": _("please_enter_conversion_content")}
        else:
            content = sdata.current_content.strip()
            if len(content) > 0:
                title = _("text_{}").format(content[:5])
                sdata.set_cache("tts_file_title", title)
                return run_tts(title, content, sdata.user_id)
            else:
                return True, {"type": "text", "content": _("no_content_found")}

    @agent_function(_("stop_speech_synthesis"))
    def _afunc_tts_stop(context_variables: dict):
        """Stop text to speech"""
        sdata = context_variables["sdata"]
        ret, info = stop_tts(sdata.user_id)
        return True, {"type": "text", "request_delay": -1, "content": info}

    @agent_function(_("get_audio"))
    def _afunc_tts_result(context_variables: dict):
        """Get audio"""
        sdata = context_variables["sdata"]
        ret, delay, info = get_tts_result(sdata.user_id)

        if ret:
            title = sdata.get_cache("tts_file_title", _("converted_audio"))
            return True, {"type": "audio", "content": info, "filename": f"{title}.mp3"}
        else:
            if delay != -1:
                return True, {"type": "text", "request_delay": delay, "content": info}
            else:
                return True, {"type": "text", "content": info}

    @agent_function(_("speech_recognition"))
    def _afunc_audio_asr(context_variables: dict):
        """Audio recognition"""
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
        self.agent_name = _("translate_assistant")
        self.instructions = "Support translation functions. " + DEFAULT_INSTRUCTIONS
 
    @agent_function(_("translate"))
    def _afunc_translate(context_variables: dict, content: str = None):
        """Translate"""
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

def filter_result(data): # for test
    """
    if isinstance(data, tuple):
        if len(data) == 2:
            if isinstance(data[1], dict):
                if 'content' in data[1]:
                    return data[1]['content']
    """
    return data

class HelpAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("help_assistant")
        self.instructions = "Provide help list and find command functions." + DEFAULT_INSTRUCTIONS

    @agent_function(_("help_list"))
    def _afunc_help(context_variables: dict):
        """Help list"""
        sdata = context_variables["sdata"]
        commands = CommandManager.get_instance().commands
        cmd_list = []
        for cmd in commands:
            if cmd.level == LEVEL_TOP:
                name = cmd.cmd_list[0]
                cmd_list.append((name, name))
        return filter_result(msg_common_select(sdata, cmd_list))


    @agent_function(_("find_command"))
    def _afunc_find_cmd(context_variables: dict, content: str = None): # pass
        """Find command"""
        sdata = context_variables["sdata"]
        if content is None and sdata.current_content == "":
            sdata.set_cache("prev_cmd", _("find_command"))
            return filter_result(True, {"type": "text", "content": _("please_enter_command_keyword")})
        else:
            if content is not None:
                logger.debug(f"find_cmd {content}")
                ret = CommandManager.get_instance().find_cmd(sdata.user_id, content)
            else:
                ret = CommandManager.get_instance().find_cmd(sdata.user_id, sdata.current_content)
            ret = [(x, x) for x in ret]
            if len(ret) == 0:
                return filter_result(True, {"type": "text", "content": _("match_failed")})
            return filter_result(msg_common_select(sdata, ret))

from backend.common.llm.llm_hub import llm_query
MSG_ROLE = "You're a smart assistant"

class LLMAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("intelligent_chat_assistant")
        self.instructions = "Invoke specific language models for conversation. " + DEFAULT_INSTRUCTIONS

    @agent_function(_("kimi_chat"))
    def _afunc_kimi(context_variables: dict, content: str = None):
        """Kimi chat"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="kimi", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[Kimi] {answer}"}
        else:
            return True, {"type": "text", "content": _("kimi_call_failed")}


    @agent_function(_("gpt4_chat"))
    def _afunc_gpt4(context_variables: dict, content: str = None):
        """GPT-4 chat"""
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
            return True, {"type": "text", "content": _("gpt4o_call_failed")}

    @agent_function(_("gemini_chat"))
    def _afunc_gemini(context_variables: dict, content: str = None):
        """Gemini chat"""
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content
        ret, answer, _ = llm_query(
            sdata.user_id, MSG_ROLE, content, "chat", engine_type="gemini", debug=True
        )
        if ret:
            return True, {"type": "text", "content": f"[Gemini] {answer}"}
        else:
            return True, {"type": "text", "content": _("gemini_call_failed")}

