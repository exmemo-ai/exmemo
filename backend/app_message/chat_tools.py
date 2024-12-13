import time
import traceback
from loguru import logger
from django.utils.translation import gettext as _

from backend.common.llm.llm_tools import select_llm_model, DEFAULT_CHAT_LLM
from backend.common.user.resource import ResourceManager 
from backend.common.user.user import UserManager

class ChatEngine:
    def __init__(self, engine_type, sdata, debug=False):
        self.engine_type = engine_type
        self.api_method, api_key, url, model_name = select_llm_model(engine_type)
        self.model_name = model_name
        self.sdata = sdata
        
        if debug:
            logger.info(
                f"ChatEngine init: {engine_type} {self.api_method}, {api_key}, {url}, {model_name}"
            )
        else:
            logger.info(f"ChatEngine init: {engine_type}")
            
        if self.api_method == "gemini":
            from google import generativeai
            generativeai.configure(api_key=api_key)
            self.llm = generativeai.GenerativeModel(model_name=model_name)
        else:
            from openai import OpenAI
            self.llm = OpenAI(api_key=api_key, base_url=url)

    def predict(self, input):
        ret = True
        try:
            #self.sdata.add_message("user", input)
            messages = [{"role": "user", "content": input}]
            formatted_msgs = [{"role": m.sender, "content": m.content} for m in self.sdata.messages]
            messages = messages + formatted_msgs
            answer = self.get_llm_response(messages) 
            #self.sdata.add_message("assistant", answer)
            count = len(input + answer) // 4 # Rough token estimate
            return ret, answer, count
        except Exception as e:
            traceback.print_exc()
            logger.error(f"ChatEngine predict error: {e}")
            return False, str(e), 0

    def get_llm_response(self, messages) -> str:
        if self.api_method == "gemini":
            response = self.llm.generate_content(messages)
            return response.text
        else:
            response = self.llm.chat.completions.create(
                messages=messages,
                model=self.model_name
            )
            return response.choices[0].message.content

def do_chat(sdata, engine_type=None, debug=False):
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
    if prompt != "" and content != "":
        content = prompt + "\n" + content
    if debug:
        logger.debug(f"chat {content}")
    #
    privilege = user.privilege
    if engine_type is None:
        engine_type = user.get("llm_chat_model", DEFAULT_CHAT_LLM)
    limit_llm_day = privilege.get("limit_llm_day", -1)
    used_llm_count = ResourceManager.get_instance().get_usage(
        sdata.user_id, dtype="day", rtype="llm"
    )
    if debug:
        logger.info(
            "Usage limit: {limit_llm_day}, Used: {used_llm_count}".format(
                limit_llm_day=limit_llm_day, used_llm_count=used_llm_count
            )
        )
    if limit_llm_day > 0:
        if used_llm_count >= limit_llm_day:
            return False, _("the_maximum_number_of_words_called_today_has_been_reached")
    try:
        if engine_type.startswith("gpt3.5"):
            pre = ""
        else:
            pre = f"[{engine_type}] "
        ret, answer, token_count = (
            ChatEngine(engine_type, sdata).predict(content)
        )
        if debug:
            logger.info(
                f"chat sid {sdata.sid} content {content} answer {answer} count {token_count}"
            )
        if ret:
            end_time = time.time()
            duration = end_time - start_time
            dic = {"token_count": token_count}
            ResourceManager.get_instance().add(
                sdata.user_id, "chat", "llm", engine_type, token_count, duration, "success", dic
            )
        return ret, pre + answer
    except Exception as e:
        logger.warning(f"failed {e}")
        traceback.print_exc()
        return False, _("chat_call_failed")