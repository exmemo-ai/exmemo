from collections import OrderedDict
from loguru import logger
import pytz
from threading import Timer

from django.utils import timezone
from backend.common.utils.net_tools import do_result
from backend.common.utils.sys_tools import get_timezone
from backend.common.user.user import UserManager, DEFAULT_CHAT_LLM_SHOW_COUNT, DEFAULT_CHAT_LLM_MEMORY_COUNT, DEFAULT_USER, DEFAULT_CHAT_MAX_CONTEXT_COUNT
from backend.common.user.utils import parse_common_args
from app_dataforge.entry import get_entry_list, add_data
from app_dataforge.models import StoreEntry
from app_dataforge.feature import TITLE_MAX_LENGTH, DEFAULT_CATEGORY, EntryFeatureTool
from backend.common.files.utils_file import count_tokens

MAX_SESSIONS = 1000

class Message:
    def __init__(self, idx, sender, content, created_time):
        self.idx = idx
        self.sender = sender
        self.content = content
        self.created_time = created_time

    def get_raw(self):
        raw = ""
        raw += self.sender + "\n"
        raw += self.content + "\n"
        raw += self.created_time + "\n"
        return raw

    def to_dict(self):
        return {
            "sender": self.sender,
            "content": self.content,
            "created_time": self.created_time
        }


class Session:
    def __init__(self, sid, user_id, is_group, source, sname = None):
        self.cache = {}
        self.messages = []
        self.user_id = user_id
        self.sid = sid
        self.sname = sname
        self.is_group = is_group
        self.source = source
        self.current_content = ""
        self.args = {}
        self.sync_idx = -1
        self.last_chat_time = timezone.now().astimezone(get_timezone())

    def get_name(self):
        if self.sname is not None:
            return self.sname
        else:
            arr = self.sid.split('_')
            if len(arr) > 1:
                return arr[1][:4] + '-' + arr[1][4:6] + '-' + arr[1][6:8] + ' ' + arr[1][8:10] + ':' + arr[1][10:12] + ':' + arr[1][12:14]                
            return self.sid             
    
    def set_cache(self, key, value):
        self.cache[key] = value

    def get_cache(self, key, default_value=None):
        if key in self.cache:
            return self.cache[key]
        return default_value

    def load_from_db(self):
        if self.is_logged_in() == False:
            return
        user = UserManager.get_instance().get_user(self.user_id)
        show_count = user.get("llm_chat_show_count", DEFAULT_CHAT_LLM_SHOW_COUNT)
        if isinstance(show_count, str):
            show_count = int(show_count)
    
        self.messages = []
        obj = self.get_item_from_db()
        if obj is not None:
            self.sid = obj["meta"]["sid"]
            self.sname = obj["title"]
            self.is_group = obj["meta"]["is_group"]
            self.source = obj["source"]
            for idx, item in enumerate(obj["meta"]["messages"]):
                self.messages.append(Message(idx, item["sender"], item["content"], item["created_time"]))
            logger.debug(f"load_from_db success, sid {self.sid}, len {len(self.messages)}")
        else:
            logger.warning(f"load_from_db failed, sid {self.sid}")
        self.messages = self.messages[-show_count:]

    def get_session_desc(self):
        obj = self.get_item_from_db()
        messages = [item.to_dict() for item in self.messages]
        raw = self.get_raw()

        if obj is None:
            dic = {
                "status": "collect",
                "atype": "subjective",
                "user_id": self.user_id,
                "ctype": DEFAULT_CATEGORY,
                "etype": "chat",
                "raw": raw,
                "source": self.source,
                "addr": self.sid,
                "meta": {"sid": self.sid, "is_group": self.is_group, 
                        "messages": messages},
            }
        else:
            dic = obj

        if dic.get("ctype") == DEFAULT_CATEGORY or dic.get("ctype") is None:            
            string = self.reduce_message()
            if len(string) > 0:
                ret, dic = EntryFeatureTool.get_instance().parse(dic, string)
            if 'title' not in dic or dic['title'] is None:
                dic['title'] = self.get_name()
            if len(dic['title']) > TITLE_MAX_LENGTH:
                dic['title'] = dic['title'][:TITLE_MAX_LENGTH] + "..."

        if obj is None:
            return True, dic
        return False, dic

    def save_to_db(self):
        if self.is_logged_in() == False:
            return
        if len(self.messages) == 0:
            return
        is_new, dic = self.get_session_desc()
        if is_new:
            ret, ret_emb, info = add_data(dic)
            logger.info(f"save_to_db add_data ret {ret}, {ret_emb}, {info}")
        else:
            logger.info(f"save_to_db update")
            #logger.info(f"save_to_db update {dic}")
            StoreEntry.objects.filter(
                user_id=self.user_id,
                addr=self.sid
            ).update(title=dic["title"],
                     ctype=dic["ctype"],
                     raw=dic["raw"], 
                     meta=dic["meta"])
            logger.info(f"update entry success")
        self.sync_idx = len(self.messages)
        logger.info(f"sync_idx {self.sync_idx}, len {len(self.messages)}")

    def sync(self):
        if self.sync_idx < len(self.messages):
            self.save_to_db()

    def get_item_from_db(self):
        condition = {"user_id": self.user_id, "etype": "chat", "addr": self.sid}
        fields = [
            "idx",
            "block_id",
            "raw",
            "title",
            "etype",
            "atype",
            "ctype",
            "status",
            "addr",
            "path",
            "source",
            "meta",
            "created_time",
            "updated_time",
        ]
        queryset = get_entry_list(None, condition, 1, fields)
        if queryset is not None and len(queryset) > 0:
            return queryset[0]
        return None

    def get_raw(self):
        arr = []
        for message in self.messages:
            arr.append(message.get_raw())
        return "\n".join(arr)

    @staticmethod
    def create_session(user_id, is_group, source):
        if user_id is None or user_id == "":
            user_id = DEFAULT_USER
        sid = user_id + "_" + timezone.now().astimezone(get_timezone()).strftime("%Y%m%d%H%M%S%f")
        return Session(sid, user_id, is_group, source)
    
    def is_logged_in(self):
        if self.user_id is None or self.user_id == DEFAULT_USER or len(self.user_id) == 0:
            return False
        return True

    def close(self):
        self.sync()

    def delete_session(self, sid):
        """
        Clear this session
        """
        StoreEntry.objects.filter(
            user_id=self.user_id, addr=sid
        ).delete()
        if sid == self.sid:
            self.messages = []

    def get_messages(self, force = False):
        if len(self.messages) == 0 or force:
            self.load_from_db()
        messages = [item.to_dict() for item in self.messages]
        return do_result(True, {"messages": messages})

    def send_message(self, msg1, msg2):
        if msg1 is not None and msg1 != "":
            self.add_message("user", msg1)
        if msg2 is not None and msg2 != "":
            self.add_message("assistant", msg2)

    def add_message(self, sender, content):        
        #created_time = timezone.now().astimezone(pytz.UTC)
        created_time = timezone.now().astimezone(get_timezone())
        self.messages.append(Message(len(self.messages), sender, content, created_time.strftime("%Y-%m-%d %H:%M:%S")))
        self.last_chat_time = created_time
        logger.info(f"after add_messages, len {len(self.messages)}, sid {self.sid}")
        if len(self.messages) - self.sync_idx > 10:
            self.save_to_db()

    def reduce_message(self):
        string = ""
        if len(self.messages) < 4:
            return ""
        for item in self.messages:
            if item.sender != "assistant":
                content = item.content
                if len(content) > 100:
                    content = content.strip()
                    content = content[:100] + "..."
                string += content
                string += ";"
                if len(string) > 500:
                    break
        return string

    def get_context_messages(self):
        user = UserManager.get_instance().get_user(self.user_id)
        count = user.get("llm_chat_memory_count", DEFAULT_CHAT_LLM_MEMORY_COUNT)
        if isinstance(count, str):
            count = int(count)
        if count == 0:
            return []
        
        max_tokens = user.get("llm_chat_max_context_count", DEFAULT_CHAT_MAX_CONTEXT_COUNT)
        if isinstance(max_tokens, str):
            max_tokens = int(max_tokens)

        recent_messages = self.messages[-count:]
        if max_tokens > 0:
            result_messages = []
            total_tokens = 0
            
            for msg in reversed(recent_messages):
                current_tokens = count_tokens(msg.sender + msg.content)
                if total_tokens + current_tokens > max_tokens:
                    break
                total_tokens += current_tokens
                result_messages.insert(0, msg)
        else:
            result_messages = recent_messages
        logger.info(f"max_tokens {max_tokens}, {len(self.messages)} -> {len(recent_messages)} -> {len(result_messages)}")
        return result_messages

class SessionManager:
    __instance = None
    #TIMER_INTERVAL = 5 * 60 # 5 minutes
    TIMER_INTERVAL = 2 * 60 # 2 minutes

    @staticmethod
    def get_instance():
        if SessionManager.__instance is None:
            SessionManager.__instance = SessionManager()
        return SessionManager.__instance

    def __init__(self):
        self.sessions = OrderedDict()
        self.timer = None

    def check_session_cache(self):
        logger.info("Check session cache")
        current_time = timezone.now().astimezone(get_timezone())
        sessions_to_remove = []
        
        for sid, session in self.sessions.items():
            time_diff = current_time - session.last_chat_time
            logger.info(f"sid {sid} time_diff {time_diff.total_seconds()}")
            if time_diff.total_seconds() > 600:  # 600 second
                session.close()
                sessions_to_remove.append(sid)
            else:
                session.sync()
        
        for sid in sessions_to_remove:
            self.sessions.pop(sid)
            logger.info(f"Removed inactive session: {sid}")

        if len(self.sessions) == 0:
            self.stop_timer()

    def start_timer(self):
        logger.info('start_timer', self.timer)
        if self.timer is None:
            self.timer = Timer(self.TIMER_INTERVAL, self._timer_task)
            self.timer.start()
            logger.info("Timer started")

    def _timer_task(self):
        self.stop_timer()
        logger.debug("Timer task triggered")
        self.check_session_cache()
        if len(self.sessions) > 0:
            self.start_timer()
        else:
            logger.debug("No active session, timer stopped")

    def stop_timer(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def __del__(self):
        self.stop_timer()

    def get_session_by_user(self, user_id, is_group, source):
        logger.info(f'get_session_by_user {user_id}, {is_group}, {source}')
        # get last session from db
        items = StoreEntry.objects.filter(is_deleted=False, user_id=user_id, etype="chat", source=source).order_by('-updated_time').values("addr", "title", "meta")[:1]
        if len(items) > 0:
            sid = items[0]["addr"]
            if sid not in self.sessions:
                session = Session(sid, user_id, is_group, source)
                session.load_from_db()
                self.add_session(session)

        # get last session
        current_session = None
        most_recent_time = None
        last_time = timezone.now().astimezone(get_timezone())
        for sid, sess in self.sessions.items():
            try:
                if sess.user_id == user_id and sess.source == source:
                    if len(sess.messages) == 0:
                        logger.info(f'sid {sid}')
                        if sid.find('_') != -1:
                            time_str = sid.split('_')[1]
                            # sid: xx_20241128093936091810
                            last_time = timezone.datetime.strptime(
                                time_str,
                                "%Y%m%d%H%M%S%f"
                            ).replace(tzinfo=timezone.get_current_timezone())                    
                    else:
                        last_time = timezone.datetime.strptime(
                            sess.messages[-1].created_time,
                            "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=timezone.get_current_timezone())
                    if most_recent_time is None or last_time > most_recent_time:
                        most_recent_time = last_time
                        current_session = sess
            except Exception as e:
                logger.warning(f"get_session_by_user error {e}")
        
        # check the session is active in 24 hour
        if current_session is not None and most_recent_time is not None:
            time_diff = timezone.now().astimezone(get_timezone()) - most_recent_time
            if time_diff > timezone.timedelta(hours=24):
                current_session.close()
                self.remove_session(current_session.sid)
                current_session = None
        
        if current_session is not None:
            return current_session
            
        return Session.create_session(user_id, is_group, source)
        
    def get_session(self, sid, user_id, is_group, source, force_create=False):
        if force_create:
            session = Session.create_session(user_id, is_group, source)
        elif sid == "" or sid is None or sid == 'null':
            session = self.get_session_by_user(user_id, is_group, source)
        elif sid in self.sessions:
            session = self.sessions[sid]
        else: # session in db
            session = Session(sid, user_id, is_group, source)
            session.load_from_db()
        self.add_session(session)
        return session
    
    def add_session(self, session):
        if session.sid not in self.sessions:
            if len(self.sessions) >= MAX_SESSIONS:
                oldest_sid, oldest_session = self.sessions.popitem(last=False)
                oldest_session.close()
            self.sessions[session.sid] = session        
        # update visit position
        if session.sid in self.sessions:
            self.sessions.move_to_end(session.sid)

    def rename_session(self, sdata, sid, sname):
        if sname is None or sid is None:
            return do_result(False, 'session not found')
        if sid in self.sessions:
            logger.info(f"sid {sid}, sessions {self.sessions.keys()}")
            self.sessions[sid].sname = sname
            self.sessions[sid].save_to_db()
            return do_result(True, 'session renamed')
        else:
            logger.info(f'cannot get, rename session {sid} {sname}')
            return do_result(False, 'session not found')

    def remove_session(self, sid):
        if sid in self.sessions:
            self.sessions.pop(sid)
        return True

    def get_sessions(self, user_id):
        """
        Get sessions from a user
        """
        
        slist = []
        items = StoreEntry.objects.filter(user_id=user_id, etype="chat").order_by('-updated_time').values("addr", "title", "updated_time")[0:20]
        sinfo = OrderedDict()
        for item in items:
            if item["addr"] not in sinfo:
                try:
                    d = timezone.datetime.strptime(str(item["updated_time"]), "%Y-%m-%d %H:%M:%S.%f%z")
                except ValueError:
                    try:
                        d = timezone.datetime.strptime(str(item["updated_time"]), "%Y-%m-%d %H:%M:%S%z")
                    except ValueError:
                        logger.warning(f"Failed to parse time: {item['updated_time']}")
                        d = timezone.now().astimezone(get_timezone())
                sinfo[item["addr"]] = (item["title"], d)
        
        for session in self.sessions.values():
            if session.user_id == user_id:
                if session.sid not in sinfo:
                    sinfo[session.sid] = (session.get_name(), session.last_chat_time)

        sinfo = dict(sorted(sinfo.items(), key=lambda x: x[1][1], reverse=False))
        for sid, item in sinfo.items():
            sname = item[0]
            if sname == "" or sname is None:
                sname = sid
            slist.append({
                "sid": sid,
                "sname": sname
            })
        detail = {"type": "text", "sessions": slist}
        logger.debug(f'get_sessions {detail}')
        return do_result(True, detail)
    
    def send_message(self, msg1:str, msg2:str, sdata: Session):
        need_create_new = False

        user = UserManager.get_instance().get_user(sdata.user_id)
        show_count = user.get("llm_chat_show_count", DEFAULT_CHAT_LLM_SHOW_COUNT)
        if isinstance(show_count, str):
            show_count = int(show_count)
        logger.info(f'check send_message {len(sdata.messages)} {show_count}')

        if len(sdata.messages) > show_count:
            need_create_new = True
        if need_create_new:
            sdata.close()
            self.remove_session(sdata.sid)
            sdata = Session.create_session(sdata.user_id, sdata.is_group, sdata.source)
            self.add_session(sdata)
        sdata.send_message(msg1, msg2)
        if sdata.sid in self.sessions:
            self.sessions.move_to_end(sdata.sid)

        self.start_timer()

        logger.info(f'add_message ret {sdata.sid}')
        return sdata.sid
    
    def clear_session(self, sdata: Session, sid = None):
        if sid is not None:
            sdata.delete_session(sid)
            self.remove_session(sid)
        else:
            if sdata is not None:
                sdata.delete_session(sdata.sid)
                self.remove_session(sdata.sid)
        return do_result(True, 'session cleared')

def get_session_by_req(request):
    """
    Get the session list of the user
    """
    args = parse_common_args(request)
    sid = request.GET.get("sid", request.POST.get("sid", ''))
    create = request.GET.get("create", request.POST.get("create", False))
    if create == 'true':
        create = True
    else:
        create = False
    sdata = SessionManager.get_instance().get_session(sid, args['user_id'], args['is_group'], 
                                                        args['source'], force_create=create)
    sdata.current_content = args['content']
    sdata.is_group = args['is_group']
    sdata.args = args
    return sdata




