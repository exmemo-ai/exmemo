import json
import datetime
from collections import deque
from loguru import logger
from django.contrib.auth.models import User as UserSystem
from django.utils.translation import gettext as _
from .models import StoreUser
from dataclasses import dataclass, asdict, field

USER_LEVEL_GUEST = -1
USER_LEVEL_NORMAL = 0
USER_LEVEL_FRIEND = 5
USER_LEVEL_ADMIN = 10
DEFAULT_USER = "guest"
DEFAULT_PASSWORD = "1234567890"
DEFAULT_SESSION = "_unknown"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin123456"
DEFAULT_CHAT_LLM_PROMPT = _("chat_prompt_default")
DEFAULT_CHAT_LLM_SHOW_COUNT = 50
DEFAULT_CHAT_LLM_MEMORY_COUNT = 5
DEFAULT_CHAT_MAX_CONTEXT_COUNT = 1024
TRUNCATE_MODE_FIRST = "first"
TRUNCATE_MODE_TITLE_CONTENT = "title_content"
TRUNCATE_MODE_FIRST_LAST = "first_last"
DEFAULT_TRUNCATE_MODE = TRUNCATE_MODE_FIRST
DEFAULT_TRUNCATE_MAX_LENGTH = 1024

def convert_units(num):
    if num >= 10**6:
        return str(num / 10**6) + "M"
    elif num >= 10**3:
        return str(num / 10**3) + "K"
    else:
        return str(num)


@dataclass
class UserSettings:
    tts_engine: str = "edge"
    tts_language: str = "mix"
    tts_speed: str = "1.0"
    tts_voice: str = "caicai"
    llm_chat_model: dict = field(default_factory=dict)
    llm_tool_model: dict = field(default_factory=dict)
    llm_chat_prompt: str = DEFAULT_CHAT_LLM_PROMPT
    llm_chat_show_count: int = DEFAULT_CHAT_LLM_SHOW_COUNT
    llm_chat_memory_count: int = DEFAULT_CHAT_LLM_MEMORY_COUNT
    llm_chat_max_context_count: int = DEFAULT_CHAT_MAX_CONTEXT_COUNT
    learn_word_voc: str = "BASE"
    batch_use_llm: bool = False
    bookmark_download_web: bool = False
    web_save_content: bool = False
    web_get_category: bool = True
    web_get_abstract: bool = False
    file_save_content: bool = False
    file_get_category: bool = True
    file_get_abstract: bool = False
    note_save_content: bool = True
    note_get_category: bool = True
    note_get_abstract: bool = False
    truncate_content: bool = True
    truncate_max_length: int = DEFAULT_TRUNCATE_MAX_LENGTH
    truncate_mode: str = DEFAULT_TRUNCATE_MODE

    def get_json(self):
        return asdict(self)

    def set_json(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def set(self, name, value):
        if hasattr(self, name):
            setattr(self, name, value)
            return True
        return False

    def get(self, name, default_value=None):
        if hasattr(self, name):
            return getattr(self, name)
        return default_value

    def __repr__(self):
        return f"<UserSettings {self.tts_engine} {self.tts_langugage} {self.tts_speed} {self.llm_chat_model} {self.llm_tool_model}>"


class UserPrivilege:
    def __init__(self, level):
        self.set_level(level)

    @staticmethod
    def get_level_privilege(level):
        p = UserPrivilege(level)

    def set_default(self):
        self.b_ocr = False
        self.b_tts = True
        self.b_tts_mine = False
        self.b_llm = True
        self.b_save_data = False
        self.b_parse_paper = False
        self.b_translate_book = False
        self.limit_llm_day = 1000 * 50
        self.limit_tts_day = 1000 * 20
        self.limit_tts_once = 1000 * 5
        self.limit_export_record_day = 7

    def set_level(self, level):
        """
        Each level has different permission settings, dynamic modification is not supported
        """
        self.set_default()
        if level == USER_LEVEL_GUEST:
            self.limit_llm_day = 1000 * 10
            self.limit_tts_day = 1000 * 10
            self.limit_tts_once = 1000 * 10
            self.limit_export_record_day = 7
            self.b_save_data = True
        elif level == USER_LEVEL_FRIEND:
            self.b_ocr = True
            self.limit_llm_day = 1000 * 100
            self.limit_tts_day = 1000 * 30
            self.limit_tts_once = 1000 * 10
            self.limit_export_record_day = 30
            self.b_save_data = True
        elif level == USER_LEVEL_ADMIN:
            self.b_ocr = True
            self.b_tts_mine = True
            self.limit_llm_day = 1000 * 1000
            self.limit_tts_day = 1000 * 100
            self.limit_tts_once = 1000 * 30
            self.limit_export_record_day = 30
            self.b_save_data = True
            self.b_parse_paper = True

    def get_json(self):
        """
        Only for debugging to view permission settings
        """
        dic = {}
        for k in dir(self):
            if k.startswith("b_") or k.startswith("limit_"):
                dic[k] = getattr(self, k)
        return dic

    """
    def set_json(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            for key,value in data.items():
                setattr(self, key, value)
    """

    def get(self, name, default_value=None):
        if hasattr(self, name):
            return getattr(self, name)
        return default_value

    def get_descript(self):
        arr = []
        arr.append(_("supports_ocr_colon_") + (_("yes") if self.b_ocr else _("denied")))
        arr.append(_("save_data_colon_") + (_("yes") if self.b_save_data else _("denied")))
        arr.append(
            _("parsing_the_paper_colon_") + (_("yes") if self.b_parse_paper else _("denied"))
        )
        arr.append(
            _("translation_book_colon_")
            + (_("yes") if self.b_translate_book else _("denied"))
        )
        arr.append(
            _("model_rate_limit_colon__{limit_llm_day_formatted}_tokens/day").format(
                limit_llm_day_formatted=convert_units(self.limit_llm_day)
            )
        )
        arr.append(
            _("speech_synthesis_rate_limit_colon__{limit_tts_day}_tokens/day").format(
                limit_tts_day=convert_units(self.limit_tts_day)
            )
        )
        arr.append(
            _("speech_synthesis_rate_limit_colon__{tokens}_tokens/attempt").format(
                tokens=convert_units(self.limit_tts_once)
            )
        )
        arr.append(
            _("recording_export_range_colon__{limit_export_record_day}_days").format(
                limit_export_record_day=self.limit_export_record_day
            )
        )
        return "\n".join(arr)


class UserOperate:
    def __init__(
        self, uid, level=USER_LEVEL_NORMAL, password=DEFAULT_PASSWORD, create=True
    ):
        self.user_id = uid
        self.level = level
        self.settings = UserSettings()
        self.privilege = UserPrivilege(level)
        self.load(password=password, create=create)

    def get_level_desc(self):
        if self.level == USER_LEVEL_GUEST:
            return _("te_ac_settings")
        if self.level == USER_LEVEL_NORMAL:
            return _("normal")
        if self.level == USER_LEVEL_FRIEND:
            return _("vip_user")
        if self.level == USER_LEVEL_ADMIN:
            return _("administrator")
        return _("unknown_level")

    def set_level(self, level):
        self.level = level
        self.privilege.set_level(level)
        self.save()

    def reset_setting(self):
        self.settings = UserSettings()
        self.save()

    def set(self, name, value, save=True):
        ret = self.settings.set(name, value)
        if save and ret:
            self.save()

    def set_multiple(self, settings_dict, save=True):
        updated = False
        for name, value in settings_dict.items():
            if self.settings.set(name, value):
                updated = True
                
        if save and updated:
            self.save()
        return updated

    def get(self, name, default_value=None):
        return self.settings.get(name, default_value)

    def __repr__(self):
        return f"<User {self.user_id}> level {self.level}"

    def load(self, password=DEFAULT_PASSWORD, create=True, debug=False):
        """
        Args:
            create: if not exist, create user
        """
        data = None
        if self.user_id is not None:
            data = StoreUser.objects.filter(user_id=self.user_id).first()
        if data is None:
            if self.user_id is not None:
                data = StoreUser.objects.filter(user_id=self.user_id).first()
        if data is not None:
            self.settings.set_json(data.settings)
            self.level = data.level
            self.privilege.set_level(self.level)
            self.user_id = data.user_id
            if debug:
                logger.info(f"load exist user {data}")
        else:
            if create:
                logger.info("create user")
                try:
                    UserSystem.objects.create_user(self.user_id, "", password)
                    self.save()
                except Exception as e:  # Might already exist, such as a test user
                    logger.warning(f"create user error {e}")
                    self.level = USER_LEVEL_NORMAL
                    self.save()

    def save(self):
        try:
            data = StoreUser.objects.filter(user_id=self.user_id).first()
            if not data:
                data = StoreUser(user_id=self.user_id)
                data.created_time = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            data.settings = json.dumps(self.settings.get_json())
            # data.privilege = ''#json.dumps(self.privilege.get_json())
            data.level = self.level
            data.save()
        except Exception as e:
            logger.warning(f"save user error {e}")

    @staticmethod
    def check_user_exist(user_id):
        data = StoreUser.objects.filter(user_id=user_id).first()
        logger.debug(f"check user {user_id} {data}")
        if data is not None:
            return True
        return False

    @staticmethod
    def change_user_password(user_id, password):
        if not UserOperate.check_user_exist(user_id):
            return False
        user = UserSystem.objects.get(username=user_id)
        user.set_password(password)
        user.save()
        return True

    @staticmethod
    def check_user_password(user_id, password):
        if not UserOperate.check_user_exist(user_id):
            return False
        user = UserSystem.objects.get(username=user_id)
        return user.check_password(password)

    @staticmethod
    def create_user(uid, password, level=USER_LEVEL_NORMAL):
        try:
            UserOperate(uid, level=level, password=password, create=True)
            return True
        except Exception as e:
            logger.warning(f"create user error {e}")
            return False


class UserManager:
    __instance = None
    MAX_USERS = 1000

    def __init__(self):
        self.user_list = deque(maxlen=UserManager.MAX_USERS)
        self.user_map = {}

    @staticmethod
    def get_instance():
        if not UserManager.__instance:
            UserManager.__instance = UserManager()
        return UserManager.__instance

    def get_user(self, uid, level=USER_LEVEL_NORMAL):
        if uid not in self.user_map:
            if len(self.user_list) == UserManager.MAX_USERS:
                oldest_uid = self.user_list.popleft()
                del self.user_map[oldest_uid]
            new_user = UserOperate(uid, level)
            self.user_list.append(uid)
            self.user_map[uid] = new_user
        return self.user_map[uid]

    def check_user_exist(self, user_id):
        return UserOperate.check_user_exist(user_id)

    def change_user_password(self, user_id, password):
        return UserOperate.change_user_password(user_id, password)

    def check_user_password(self, user_id, password):
        return UserOperate.check_user_password(user_id, password)

    def create_user(self, user_id, password=DEFAULT_PASSWORD, level=USER_LEVEL_NORMAL):
        return UserOperate.create_user(user_id, password, level=level)

    def get_user_list(self):
        ret = []
        users = StoreUser.objects.all()
        for user in users:
            ret.append(user.user_id)
        return ret

    def delete_user(self, user_id):
        try:
            StoreUser.objects.filter(user_id=user_id).delete()
            UserSystem.objects.filter(username=user_id).delete()
            return True
        except Exception as e:
            logger.warning(f"delete user error {e}")
            return False
