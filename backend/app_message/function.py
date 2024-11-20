import re
import time
from django.utils.translation import gettext as _
from .command import *
from app_message.session import SessionManager
from backend.common.user.resource import ResourceManager

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


def do_chat(args):
    """
    Call the model for a chat
    """
    content = args["content"]
    if content is not None:
        content = content.strip()
    ret, answer = chat(args["user_id"], args["session_id"], content)
    if ret:
        return True, {"type": "text", "content": answer}
    else:
        return True, {"type": "text", "content": _("chat_call_failed")}

def chat(uid, sid, content, engine_type=None, debug=False): # later move to app_manager
    """
    Provides chat, internal saving chat records.
    """
    start_time = time.time()
    user = UserManager.get_instance().get_user(uid)
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
        uid, dtype="day", rtype="llm"
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
            SessionManager.get_instance()
            .get_chat(sid, model=engine_type)
            .predict(content)
        )
        if debug:
            logger.info(
                f"chat sid {sid} content {content} answer {answer} count {token_count}"
            )
        if ret:
            end_time = time.time()
            duration = end_time - start_time
            dic = {"token_count": token_count}
            ResourceManager.get_instance().add(
                uid, "chat", "llm", engine_type, token_count, duration, "success", dic
            )
        return ret, pre + answer
    except Exception as e:
        logger.warning(f"failed {e}")
        import traceback

        traceback.print_exc()
        return False, _("call_failed")