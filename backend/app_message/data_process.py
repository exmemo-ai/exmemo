from collections import OrderedDict
import pytz

from django.db.models import Q
from django.utils import timezone
from backend.common.utils.net_tools import do_result
from backend.common.llm.llm_hub import llm_query
from backend.common.utils.text_tools import get_language_name
from backend.settings import LANGUAGE_CODE
from .message import MSG_ROLE
from .models import StoreMessage
from app_dataforge.prompt import PROMPT_TITLE

def get_messages(args, request):
    """
    Get messages from a user
    """
    message_list = []
    items = StoreMessage.objects.filter(
        user_id=args["user_id"], sid=args["sid"]
    ).order_by("-created_time")[:50]
    for message in items:
        message_list.append(
            {
                "sender": message.sender,
                "content": message.content,
                "created_time": message.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    message_list.reverse()
    detail = {"type": "text", "content": message_list}
    return do_result(True, detail)


def get_sessions(args, request):
    """
    Get sessions from a user
    """
    slist = []
    items = (
        StoreMessage.objects.filter(user_id=args["user_id"])
        .order_by("created_time")
        .values("sid", "sname")
        .distinct()
    )
    sinfo = OrderedDict()
    for item in items:
        if item["sid"] not in sinfo:
            sinfo[item["sid"]] = item["sname"]
    
    for sid, sname in sinfo.items():
        if sname == "" or sname is None:
            sname = sid
        slist.append({
            "sid": sid,
            "sname": sname
        })
    detail = {"type": "text", "content": slist}
    return do_result(True, detail)

def clear_session(args, request):
    """
    Clear a session
    """
    StoreMessage.objects.filter(
        user_id=args["user_id"], sid=args["sid"]
    ).delete()
    detail = {"type": "text", "content": 'session cleared'}
    return do_result(True, detail)

def get_session_name(args, items):
    string = ""
    if len(items) == 0:
        return ""
    sid = ""
    for item in items:
        sid = item.sid
        if item.sender != "Bot":
            content = item.content
            if len(content) > 100:
                content = content.strip()
                content = content[:100] + "..."
            string += content
            string += "\n"
            if len(string) > 500:
                break
    if len(string) > 0:
        query = PROMPT_TITLE.format(
            content=string, language=get_language_name(LANGUAGE_CODE.lower())
        )
        ret, answer, _ = llm_query(
            args["user_id"], MSG_ROLE, query, "chat", debug=False
        )
        if ret:
            if sid.startswith("20"):
                sname = sid[2:10].replace("-", "") + "_" + answer
            else:
                sname = answer
            return sname
    return ""

def save_session(args, request):
    """
    Save a session
    """
    ret = True
    items = StoreMessage.objects.filter(
        Q(user_id=args["user_id"]) & (Q(sname__isnull=True) | Q(sname=args["sid"]))
    ).values("sid").distinct()

    slist = []
    for item in items:
        if item["sid"] not in slist:
            slist.append(item["sid"])
        if not set_session_name(args, item["sid"]):
            ret = False
    if ret:
        detail = {"type": "text", "content": 'already saved'}
        return do_result(True, detail)
    else:
        detail = {"type": "text", "content": 'session save failed'}
        return do_result(False, detail)        


def set_session_name(args, sid):
    items = StoreMessage.objects.filter(
        user_id=args["user_id"], sid=sid
    ).order_by("created_time")
    sname = ""
    sname_empty = False
    for item in items:
        if item.sname is not None and item.sname != "" and item.sname != sid:
            sname = item.sname
        else:
            sname_empty = True
    if not sname_empty:
        return True
    if sname == "":
        sname = get_session_name(args, items)
    if sname != "":
        StoreMessage.objects.filter(user_id=args["user_id"], sid=sid).update(
            sname=sname
        );
        return True
    return False

def save_message(content, args, detail):
    """
    Save the chat message
    """
    user_id = args["user_id"]
    sender = user_id # later adjust to user_name
    receiver = "Bot"
    rtype = "text"
    if "sid" in args and args["sid"] is not None:
        sid = args["sid"]
    else:
        sid = args['session_id']
    if "sname" in args and args["sname"] is not None:
        sname = args["sname"]
    else:
        sname = sid
    meta = {}
    source = args["source"]
    StoreMessage.objects.create(
        user_id=user_id,
        sender=sender,
        receiver=receiver,
        rtype=rtype,
        sid=sid,
        sname=sname,
        is_group=args["is_group"],
        content=content,
        meta=meta,
        source=source,
        created_time=timezone.now().astimezone(pytz.UTC),
    )
    sender = "Bot"
    receiver = user_id
    rtype = detail["type"]
    content = detail["content"]
    StoreMessage.objects.create(
        user_id=user_id,
        sender=sender,
        receiver=receiver,
        rtype=rtype,
        sid=sid,
        sname=sname,
        is_group=args["is_group"],
        content=content,
        meta=meta,
        source=source,
        created_time=timezone.now().astimezone(pytz.UTC),
    )
