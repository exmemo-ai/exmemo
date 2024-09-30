# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType

# from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *

# from config import conf
from .req import parse_data


@plugins.register(
    name="ExMemo",
    desire_priority=-1,
    hidden=True,
    desc="An assistant bot",
    version="0.9",
    author="xieyan",
)
class ExMemo(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[ExMemo] inited")
        self.config = super().load_config()

    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        cmsg = context["msg"]
        if context.get("isgroup", False):
            user_id = cmsg.actual_user_id
            user_name = cmsg.actual_user_nickname
            group_id = cmsg.from_user_id
            group_name = cmsg.from_user_nickname
        else:
            user_id = cmsg.from_user_id
            user_name = cmsg.from_user_nickname
            group_name = None
            group_id = None

        logger.info(f"[ExMemo] {user_id} {user_name} {group_id} {group_name}")
        ret, detail = func(
            context,
            wechat_user_id=user_id,
            wechat_user_name=user_name,
            group_id=group_id,
            group_name=group_name,
            e_context=e_context,
        )

        if ret and isinstance(detail, dict) and "type" in detail:
            # 回复对话
            reply = Reply()
            if detail["type"] == "file":
                reply.type = ReplyType.FILE
            elif detail["type"] == "text":
                reply.type = ReplyType.TEXT
            reply.content = detail["content"]
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        e_context.action = EventAction.CONTINUE
        return

    def get_help_text(self, **kwargs):
        help_text = "输入ExMemo，我会回复你的名字\n输入End，我会回复你世界的图片\n"
        return help_text


def func(context, **kwargs):
    """
    与后端交互，处理文本、文件、图片
    """
    ret = False
    detail = {"type": "text", "content": "不能识别的命令"}
    if context.type == ContextType.TEXT:
        ret, detail = parse_data(context.content, rtype="text", **kwargs)
    # elif False == context.get("isgroup", False) and context.type == ContextType.SHARING:
    elif context.type == ContextType.SHARING:
        ret, detail = parse_data(context.content, rtype="text", **kwargs)
    elif context.type == ContextType.FILE:
        if not context.get("isgroup", False):
            print("parse FILE", context.content)
            context.get("msg").prepare()
            ret, detail = parse_data(context.content, rtype="file", **kwargs)
    elif context.type == ContextType.IMAGE:
        if not context.get("isgroup", False):
            print("parse IMAGE", context.content)
            context.get("msg").prepare()
            ret, detail = parse_data(context.content, rtype="file", **kwargs)
    print("func ret", ret, detail)
    return ret, detail


def test_func():
    import sys

    SRC_DIR = "/opt/chatgpt-on-wechat"
    if SRC_DIR not in sys.path:
        sys.path.append(SRC_DIR)

    from bridge.context import ContextType, Context
    from plugins import event

    # context = Context(ContextType.TEXT, '收录https://arxiv.org/pdf/2303.11366.pdf') # pass
    context = Context(ContextType.TEXT, "记录：我有一个想法，我想把它记录下来")  # pass
    # context = Context(ContextType.TEXT, 'http://www.baidu.com') # pass
    # context = Context(ContextType.TEXT, '翻译 missing') # pass
    # context = Context(ContextType.FILE, '/exports/git/chatgpt-on-wechat/tmp/风景谈-矛盾.docx') # pass
    # context = Context(ContextType.IMAGE, '/exports/git/chatgpt-on-wechat/tmp/231206-070507.png')
    # from channel.chat_message import ChatMessage
    # msg: ChatMessage = context["msg"]
    func(
        context,
        wechat_user_id="12346788",
        wechat_user_name="xieyan",
        group_id=None,
        group_name=None,
    )
