import re
import time
import pandas as pd
from django.utils.translation import gettext as _
from .command import *
from backend.common.user.resource import ResourceManager
from backend.common.utils.regular_tools import regular_str
from app_dataforge.entry import get_entry_list

CMD_INNER_GET = "CMD_INNER_GET"


def regular_title(title):
    """
    Limit title length, remove special characters
    """
    if title is not None:
        title = title.strip()
        title = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]+", "", title)
        title = title[:20]
    return title


def do_chat(sdata):
    """
    Call the model for a chat
    """
    content = sdata.current_content
    if content is not None:
        content = content.strip()
    ret, answer = chat(sdata, content)
    if ret:
        return True, answer
    else:
        return False, _("chat_call_failed")

def chat(sdata, content, engine_type=None, debug=False):
    """
    Provides chat, internal saving chat records.
    """
    start_time = time.time()
    user = UserManager.get_instance().get_user(sdata.user_id)
    # 241115
    prompt = user.get("llm_chat_prompt", "")
    if prompt != "" and content != "":
        content = prompt + "\n" + content
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
            sdata.get_chat_engine(model=engine_type).predict(content)
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
        import traceback

        traceback.print_exc()
        return False, _("call_failed")
    
def search_data(sdata, dic={}):
    """
    Search for data
    """
    condition = {"user_id": sdata.user_id}
    condition.update(dic)
    if len(sdata.current_content) > 0:
        keyword = sdata.current_content
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
        sdata.current_content = arr[0][1]
        return CommandManager.get_instance().msg_do_command(sdata)
    else:
        return msg_common_select(sdata, arr)
