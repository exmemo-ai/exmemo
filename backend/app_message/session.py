import os
from collections import deque, OrderedDict
from loguru import logger
import pytz

from django.db.models import Q, F
from django.utils import timezone
import backend.common.llm.chat_tools as chat_tools
from backend.common.utils.net_tools import do_result
from backend.common.llm.llm_hub import llm_query
from backend.common.utils.text_tools import get_language_name
from backend.common.user.user import UserManager, DEFAULT_CHAT_LLM_SHOW_COUNT
from backend.settings import LANGUAGE_CODE
from .message import MSG_ROLE
from .models import StoreMessage
from app_dataforge.prompt import PROMPT_TITLE

class Session:
    """
    The current session is dynamic and not stored in a database. maybe store it later.
    """
    def __init__(self, sid, sname, user_id, is_group, source):
        self.cache = {}
        self.messages = []
        self.chat = None
        self.user_id = user_id
        self.sid = sid
        self.sname = sname
        self.is_group = is_group
        self.source = source
        self.current_content = ""
        self.args = {}

    def set_cache(self, key, value):
        self.cache[key] = value

    def get_cache(self, key, default_value=None):
        if key in self.cache:
            return self.cache[key]
        return default_value

    def get_chat_engine(self, model=None, debug=False):
        if model is None:
            model = os.getenv("DEFAULT_CHAT_LLM", chat_tools.DEFAULT_CHAT_LLM)
        if self.chat is None:
            self.chat = {"engine": chat_tools.ChatEngine(model), "model": model}
        elif self.chat["model"] != model:
            if debug:
                logger.info(
                    f"Session {self.sid} model changed from {self.chat['model']} to {model}"
                )
            self.clear_chat()
            self.chat = {"engine": chat_tools.ChatEngine(model), "model": model}
        return self.chat["engine"]


    def clear_chat(self):
        if self.chat is not None:
            self.chat["engine"].clear_memory()


    def clear_session(self):
        """
        Clear this session
        """
        StoreMessage.objects.filter(
            user_id=self.user_id, sid=self.sid
        ).delete()
        self.clear_chat()
        self.messages = []
        detail = {"type": "text", "content": 'session cleared'}
        return do_result(True, detail)
    

    def get_messages(self, force = False):
        """
        load messages for this session
        """
        user = UserManager.get_instance().get_user(self.user_id)
        show_count = user.get("llm_chat_show_count", DEFAULT_CHAT_LLM_SHOW_COUNT)
        if isinstance(show_count, str):
            show_count = int(show_count)
        logger.debug(f'load_messages {show_count}')

        if len(self.messages) == 0 or force:
            messages = []
            items = StoreMessage.objects.filter(
                user_id=self.user_id, sid=self.sid
            ).order_by("-created_time")[:show_count]
            for message in items:
                messages.append(
                    {
                        "sender": message.sender,
                        "content": message.content,
                        "created_time": message.created_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            messages.reverse()
            self.messages = messages
        self.messages = self.messages[-show_count:]
        detail = {"type": "text", "content": self.messages}
        return do_result(True, detail)


    def add_message(self, content, detail):
        """
        Save the chat message
        """
        created_time = timezone.now().astimezone(pytz.UTC)
        StoreMessage.objects.create(
            user_id=self.user_id,
            sender="user",
            receiver="assistant",
            rtype="text",
            sid=self.sid,
            sname=self.sname,
            is_group=self.is_group,
            content=content,
            meta={},
            source=self.source,
            created_time=created_time,
        )
        StoreMessage.objects.create(
            user_id=self.user_id,
            sender="assistant",
            receiver="user",
            rtype=detail["type"],
            sid=self.sid,
            sname=self.sname,
            is_group=self.is_group,
            content=detail["content"],
            meta={},
            source=self.source,
            created_time=created_time,
        )
        self.messages.append(
            {
                "sender": "user",
                "content": content,
                "created_time": created_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        self.messages.append(
            {
                "sender": "assistant",
                "content": detail["content"],
                "created_time": created_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )


    @staticmethod
    def calc_session_name(user_id, items):
        string = ""
        if len(items) == 0:
            return ""
        sid = ""
        for item in items:
            sid = item.sid
            if item.sender != "assistant":
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
                user_id, MSG_ROLE, query, "chat", debug=False
            )
            if ret:
                if sid.startswith("20"):
                    sname = sid[2:10].replace("-", "") + "_" + answer
                else:
                    sname = answer
                return sname
        return ""

    @staticmethod
    def update_session_name(user_id, sid):
        items = StoreMessage.objects.filter(
            user_id=user_id, sid=sid
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
            sname = Session.calc_session_name(user_id, items)
        if sname != "":
            StoreMessage.objects.filter(user_id=user_id, sid=sid).update(
                sname=sname
            );
            return True
        return False

class SessionManager:
    __instance = None
    MAX_SESSIONS = 1000

    @staticmethod
    def get_instance():
        if SessionManager.__instance is None:
            SessionManager.__instance = SessionManager()
        return SessionManager.__instance

    def __init__(self):
        self.session_list = deque(maxlen=SessionManager.MAX_SESSIONS)
        self.session_map = {}
        self.sessions = {}

    def get_session(self, sid, sname, user_id, is_group, source):
        if sid not in self.session_map:
            if len(self.session_list) == SessionManager.MAX_SESSIONS:
                oldest_sid = self.session_list.popleft()
                self.session_map[oldest_sid].clear_chat()
                del self.session_map[oldest_sid]
            new_session = Session(sid, sname, user_id, is_group, source)
            self.session_list.append(sid)
            self.session_map[sid] = new_session
        return self.session_map[sid]

    @staticmethod
    def update_sessions_name(user_id):
        """
        Check user's all session, if sname is empty or sname equals sid, set sname
        """
        ret = True
        items = StoreMessage.objects.filter(
            Q(user_id=user_id) & (Q(sname__isnull=True) | Q(sname=F('sid')))
        ).values("sid").distinct()

        slist = []
        for item in items:
            if item["sid"] not in slist:
                slist.append(item["sid"])
            if not Session.update_session_name(user_id, item["sid"]):
                ret = False
        if ret:
            detail = {"type": "text", "content": 'already saved'}
            return do_result(True, detail)
        else:
            detail = {"type": "text", "content": 'session save failed'}
            return do_result(False, detail)

    @staticmethod
    def get_sessions(user_id):
        """
        Get sessions from a user
        """
        slist = []
        items = (
            StoreMessage.objects.filter(user_id=user_id)
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


def test_chat_manager():
    chat_manager = SessionManager.get_instance()
    x = chat_manager.get_chat_engine("test", "gemini")
    print(x.predict("Hello"))
    x = chat_manager.get_chat_engine("test", chat_tools.DEFAULT_CHAT_LLM)
    print(x.predict("Hello"))


