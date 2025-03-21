import time
import traceback
from loguru import logger
from django.utils.translation import gettext as _

from backend.common.llm.llm_tools import LLMInfo, LLM_CUSTOM
from backend.common.user.user import UserManager
from backend.common.llm import llm_tools

class ChatEngine:
    def __init__(self, llm_info, sdata, debug=False):
        self.llm_info = llm_info
        self.sdata = sdata
        
        if debug:
            logger.info(f"ChatEngine init: {llm_info}")
            
        if llm_info.api_method == "gemini":
            from google import generativeai
            generativeai.configure(api_key=self.llm_info.api_key)
            self.llm = generativeai.GenerativeModel(model_name=self.llm_info.model_name)
        else:
            from openai import OpenAI
            self.llm = OpenAI(api_key=self.llm_info.api_key, base_url=self.llm_info.url)
            logger.info(f"ChatEngine init: url {self.llm_info.url}")

    def predict(self, input, prompt = None, debug=False):
        debug = True
        ret = True
        try:
            messages = []
            if prompt:
                messages.append({"role": "system", "content": prompt})
            
            formatted_msgs = [{"role": m.sender, "content": m.content} for m in self.sdata.get_context_messages()]
            messages.extend(formatted_msgs)
            
            messages.append({"role": "user", "content": input})
            
            if debug:
                logger.debug(f'messages {messages}')
            answer, count = self.get_llm_response(messages) 
            return ret, answer, count
        except Exception as e:
            traceback.print_exc()
            logger.warning(f"ChatEngine predict error: {e}")
            error_str = str(e)
            if len(error_str) > 100:
                error_str = error_str[:100] + "..."
            return False, "Error:\n" + error_str, 0

    def get_llm_response(self, messages) -> tuple[str, int]:
        if self.llm_info.api_method == "gemini":
            response = self.llm.generate_content(messages)
            question = "\n".join([m["content"] for m in messages])
            token_count = self.llm.count_tokens(response.text + question).total_tokens
            return response.text, token_count
        else:
            response = self.llm.chat.completions.create(
                messages=messages,
                model=self.llm_info.model_name
            )
            logger.info(f"chat by model: {self.llm_info.model_name}")
            return response.choices[0].message.content, response.usage.total_tokens

def do_chat(sdata, debug=False):
    """
    Provides chat services for users.
    """
    content = sdata.current_content
    if content is not None:
        content = content.strip()
    start_time = time.time()
    user = UserManager.get_instance().get_user(sdata.user_id)
    # 241115
    prompt = user.get("llm_chat_prompt", "")
    if debug:
        logger.debug(f"chat {content}")

    ret, desc = llm_tools.check_llm_limit(user, debug)
    if not ret:
        return ret, desc        

    try:
        engine_type = user.get("llm_chat_model", None)
        llm_info = LLMInfo.get_info(engine_type, "llm_chat_model")
        if llm_info.engine_type == LLM_CUSTOM:
            pre = "[" + _('custom') + "] "
        else:
            pre = ""
        ret, answer, token_count = (
            ChatEngine(llm_info, sdata).predict(content, prompt)
        )
        if debug:
            logger.info(
                f"chat sid {sdata.sid} content {content} answer {answer} count {token_count}"
            )
        if ret:
            duration = time.time() - start_time
            llm_tools.save_llm_usage(user, "chat", llm_info.get_desc(), duration, token_count)
        return ret, pre + str(answer)
    except Exception as e:
        logger.warning(f"failed: {e}")
        traceback.print_exc()
        return False, _("chat_call_failed")