import os
import re
import time
import json
import traceback
from loguru import logger
from django.utils.translation import gettext as _

from backend.common.llm import llm_tools
from backend.common.user.user import *
from backend.common.user.resource import *
from backend.common.utils import text_tools 

def llm_query(uid, role, question, app, engine_type=None, llm_type='llm_tool_model', debug=False):
    start_time = time.time()
    user = UserManager.get_instance().get_user(uid)

    ret, desc = llm_tools.check_llm_limit(user, debug)
    if not ret:
        return ret, desc, {}
        
    if engine_type is None:
        engine_type = user.get(llm_type, None)
    try:
        llm_info = llm_tools.LLMInfo.get_info(engine_type, llm_type)
        if debug:
            logger.debug(f"Role {role}")
            logger.debug(f"Question {question}")
            logger.debug(f"Proxy {os.getenv('HTTPS_PROXY')}")
        if llm_info.api_method == "gemini":
            ret, answer, token_count = llm_tools.query_gemini(
                role, question, api_key=llm_info.api_key, model_name=llm_info.model_name, debug=debug
            )
        else:
            ret, answer, token_count = llm_tools.query_openai(
                role,
                question,
                api_key=llm_info.api_key,
                url=llm_info.url,
                model_name=llm_info.model_name,
                debug=debug,
            )
        if ret:
            duration = round(time.time() - start_time, 3)    
            dic = llm_tools.save_llm_usage(user, app, llm_info.get_desc(), duration, token_count)
            if debug:
                logger.debug("---------------------------")
                logger.debug("Answer: {answer}...".format(answer=answer[:50]))
                logger.debug(f"desc: {dic}")
            return ret, answer, dic
    except Exception as e:
        logger.warning(f"{engine_type} failed {e}")
        traceback.print_exc()
    return False, _("call_failed"), {"token_count": 0}


def find_first_json(s):
    json_pattern = re.compile(r"\{.*?\}", re.DOTALL)
    match = json_pattern.search(s)

    while match:
        json_string = match.group(0)
        try:
            json_object = json.loads(json_string.replace("'", '"'))
            return json_object
        except json.JSONDecodeError:
            s = s[match.end() :]
            match = json_pattern.search(s)
    return None


def llm_query_json(uid, role, question, app, engine_type=None, debug=False):
    ret, answer, dic = llm_query(uid, role, question, app, engine_type=engine_type, debug=debug)
    if ret:
        json_object = text_tools.parse_json(answer)
        if json_object is not None:
            return ret, json_object, dic
    return ret, {}, dic

