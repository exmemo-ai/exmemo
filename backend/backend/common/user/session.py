from collections import deque


class Session:
    def __init__(self):
        self.cache = {}

    def set_cache(self, key, value):
        self.cache[key] = value

    def get_cache(self, key, default_value=None):
        if key in self.cache:
            return self.cache[key]
        return default_value


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

    def get_session(self, sid):
        if sid not in self.session_map:
            if len(self.session_list) == SessionManager.MAX_SESSIONS:
                oldest_sid = self.session_list.popleft()
                del self.session_map[oldest_sid]
            new_session = Session()
            self.session_list.append(sid)
            self.session_map[sid] = new_session
        return self.session_map[sid]

    def set_cache(self, sid, key, value):
        self.get_session(sid).set_cache(key, value)

    def get_cache(self, sid, key):
        return self.get_session(sid).get_cache(key)
