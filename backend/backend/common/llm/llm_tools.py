import os
import traceback
from loguru import logger
from openai import OpenAI
import google.generativeai as genai
from django.utils.translation import gettext as _
from backend.common.user.resource import *
LLM_DEFUALT = 'default'
LLM_CUSTOM = 'custom'

def check_llm_limit(user, debug=False):
    privilege = user.privilege
    limit_llm_day = privilege.get("limit_llm_day", -1)
    used_tts_count = ResourceManager.get_instance().get_usage(
        user.user_id, dtype="day", rtype="llm"
    )
    if debug:
        logger.info(
            "Usage limit: {limit_llm_day}, Used: {used_tts_count}".format(
                limit_llm_day=limit_llm_day, used_tts_count=used_tts_count
            )
        )
    if limit_llm_day > 0:
        if used_tts_count >= limit_llm_day:
            return False, _("the_maximum_number_of_words_called_today_has_been_reached")
    return True, ''

def save_llm_usage(user, app, engine_type, duration, token_count):
    dic = {
        "token_count": token_count,
        "engine_type": engine_type,
        "duration": duration,
    }
    if token_count > 0:
        if len(engine_type) > 30:
            engine_type = engine_type[:30]
        ResourceManager.get_instance().add(
            user.user_id, app, "llm", engine_type, token_count, duration, "success", dic
        )
    return dic

class LLMInfo:
    def __init__(self, engine_type=None, api_method=None, url=None, api_key=None, model_name=None):
        self.engine_type = engine_type
        self.api_method = api_method
        self.url = url
        self.api_key = api_key
        self.model_name = model_name

    @staticmethod
    def get_info(engine_type, rtype='llm_tool_model'):
        api_method = "openai"
        ltype = LLM_DEFUALT
        if isinstance(engine_type, dict):
            ltype = engine_type.get("type")
            url = engine_type.get("url")
            model_name = engine_type.get("model")
            api_key = engine_type.get("apikey")
        if ltype != LLM_CUSTOM:
            if rtype == 'llm_tool_model':
                url = os.getenv('DEFAULT_TOOL_URL')
                api_key = os.getenv('DEFAULT_TOOL_API_KEY')
                model_name = os.getenv('DEFAULT_TOOL_MODEL')
            else:
                url = os.getenv('DEFAULT_CHAT_URL')
                api_key = os.getenv('DEFAULT_CHAT_API_KEY')
                model_name = os.getenv('DEFAULT_CHAT_MODEL')
        if model_name is not None and model_name.find('gemini') >= 0:
            api_method = "gemini"
        """
        api_method = "openai"
        if engine_type.startswith("ollama"):
            api_key = os.getenv("OLLAMA_LLM_API_KEY")
            url = os.getenv("OLLAMA_LLM_URL")
            model_name = os.getenv("OLLAMA_LLM_MODEL")
        elif engine_type.startswith("deepseek"):
            api_key = os.getenv("DEEPSEEK_API_KEY")
            url = os.getenv("DEEPSEEK_URL")
            model_name = os.getenv("DEEPSEEK_MODEL")
        elif engine_type.startswith("xunfei"):
            api_key = os.getenv("XUNFEI_LLM_API_KEY")
            url = os.getenv("XUNFEI_LLM_URL")
            model_name = os.getenv("XUNFEI_LLM_MODEL")
        elif engine_type.startswith("kimi"):
            api_key = os.getenv("KIMI_API_KEY")
            url = os.getenv("KIMI_URL")
            model_name = os.getenv("KIMI_MODEL")
        elif engine_type.startswith("qwen"):
            api_key = os.getenv("QWEN_API_KEY")
            url = os.getenv("QWEN_URL")
            model_name = os.getenv("QWEN_MODEL")
        elif engine_type.startswith("userdefine"):
            api_key = os.getenv("USER_DEFINE_API_KEY")
            url = os.getenv("USER_DEFINE_URL")
            model_name = os.getenv("USER_DEFINE_MODEL")
        elif engine_type.startswith("gemini"):
            api_method = "gemini"
            url = None
            api_key = os.getenv("GEMINI_API_KEY")
            model_name = os.getenv("GEMINI_MODEL")
        elif engine_type == "gpt4o" or engine_type == "gpt-4o":
            url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            api_key = os.getenv("OPENAI_API_KEY")
            model_name = "gpt-4o"
        else:
            url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            api_key = os.getenv("OPENAI_API_KEY")
            model_name = "gpt-3.5-turbo"
        """
        return LLMInfo(ltype, api_method, url, api_key, model_name)
    

    def __str__(self):
        if self.api_key is not None:
            return f"engine_type {self.engine_type}, api_method: {self.api_method}, url: {self.url}, key: {self.api_key[:10]}... model_name: {self.model_name}"
        else:
            return f"engine_type {self.engine_type}, api_method: {self.api_method}, url: {self.url}, key: {self.api_key} model_name: {self.model_name}"
    
    def __repr__(self):
        return self.__str__()
    
    def get_desc(self):
        return f"{self.engine_type}_{self.model_name}"

def get_llm_list():
    llm_list = []
    if os.getenv("OPENAI_API_KEY") is not None and len(os.getenv("OPENAI_API_KEY")) > 3:
        llm_list.append({"label": "gpt-3.5", "value": "gpt3.5-turbo"})
        llm_list.append({"label": "gpt-4o", "value": "gpt-4o"})
    if os.getenv("GEMINI_API_KEY") is not None and len(os.getenv("GEMINI_API_KEY")) > 3:
        llm_list.append({"label": "Gemini", "value": "gemini"})
    if (
        os.getenv("DEEPSEEK_API_KEY") is not None
        and len(os.getenv("DEEPSEEK_API_KEY")) > 3
    ):
        llm_list.append({"label": "DeepSeek", "value": "deepseek"})
    if (
        os.getenv("XUNFEI_LLM_API_KEY") is not None
        and len(os.getenv("XUNFEI_LLM_API_KEY")) > 3
    ):
        llm_list.append({"label": "Xunfei", "value": "xunfei"})
    if os.getenv("KIMI_API_KEY") is not None and len(os.getenv("KIMI_API_KEY")) > 3:
        llm_list.append({"label": "Kimi", "value": "kimi"})
    if os.getenv("QWEN_API_KEY") is not None and len(os.getenv("QWEN_API_KEY")) > 3:
        llm_list.append({"label": "Qwen", "value": "qwen"})
    if os.getenv("OLLAMA_LLM_URL") is not None and len(os.getenv("OLLAMA_LLM_URL")) > 5:
        llm_list.append({"label": "Ollama", "value": "ollama"})
    if (
        os.getenv("USER_DEFINE_URL") is not None
        and len(os.getenv("USER_DEFINE_URL")) > 5
    ):
        llm_list.append({"label": "UserDefine", "value": "userdefine"})
    return llm_list


def query_openai(
    sys_info, text, api_key=None, url=None, model_name="gpt-3.5-turbo", debug=False
):
    """
    Query using OpenAI's API
    """
    if debug:
        logger.debug(f"url {url}")
        logger.debug(f"model_name {model_name}")
        if api_key is not None:
            logger.debug(f"api_key {api_key[:10]}...")
        else:
            logger.debug(f"api_key {api_key}")
    client = OpenAI(base_url=url, api_key=api_key)
    message = [
        {"role": "system", "content": sys_info},
        {"role": "user", "content": text},
    ]
    completion = client.chat.completions.create(model=model_name, messages=message)

    print("completion", completion)
    if completion.choices is None or len(completion.choices) == 0:
        if "result" in completion:
            ret = completion.result
        else:
            return False, "call llm failed", 0
    else:
        ret = completion.choices[0].message.content.strip()
    token_count = completion.usage.total_tokens
    return True, ret, token_count


def query_gemini(sys_info, text, api_key, model_name="gemini-pro", debug=False):
    """
    Query using Google's GenerativeAI API
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    ret = ""

    if debug:
        logger.debug(f"model_name {model_name}")

    if sys_info is not None and len(sys_info) > 0:
        question = f"{sys_info}\n {text}"
    else:
        question = f"{text}"

    try:
        # If the generated length exceeds the set length, an error is raised directly
        # generation_config = genai.GenerationConfig(max_output_tokens=200)
        # response = model.generate_content(question, generation_config=generation_config)
        response = model.generate_content(question)
        ret = response.text
    except Exception as e:
        logger.warning(f"failed {e}")
        traceback.print_exc()

    token_count = model.count_tokens(ret + question).total_tokens
    if len(ret) == 0:
        return False, _("gemini_is_temporarily_unavailable"), token_count
    else:
        return True, ret, token_count


if __name__ == "__main__":
    from dotenv import load_dotenv
    from backend.settings import BASE_DIR

    env_path = os.path.join(BASE_DIR, ".env")
    load_dotenv(env_path)
    block = "testme"
    sys_info = "You have a translation ability, please translate the following text"
    text = "Translate into authentic English: {block}".format(block=block)
    ret = query_openai(sys_info, text)
