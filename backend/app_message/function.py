import re
from django.utils.translation import gettext as _
from backend.common.llm.llm_hub import chat
from .command import *

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
