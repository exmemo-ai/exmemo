import os
import re
import json
from loguru import logger
from autogen import ConversableAgent, register_function
from django.utils.translation import gettext as _
from backend.common.llm import llm_tools
from backend.common.user.user import UserManager
from collections import deque

DEFAULT_TEXT = _(
    "please_register_or_log_in_first_comma___enter_formatted_as_colon__register_username_xxx_comma__password_xxx__enter_or_log_in_username_xxx_comma__password_xxx"
)


def register(user_id: str, password: str) -> dict:
    if (
        user_id is not None
        and len(user_id) > 0
        and password is not None
        and len(password) > 0
    ):
        if UserManager.get_instance().check_user_exist(user_id):
            return {"status": False, "info": _("username_already_exists")}
        if UserManager.get_instance().create_user(user_id, password):
            return {"user_id": user_id, "password": password}
        else:
            return {"status": False, "info": _("registration_failed")}
    else:
        return {"status": False, "info": _("user_or_password_are_empty_dot_")}


def login(user_id: str, password: str) -> dict:
    return {"user_id": user_id, "password": password}


def change_password(user_id: str, password_old: str, password_new: str) -> dict:
    if user_id is None or user_id == "":
        return {"status": False, "info": _("empty_username")}
    if password_old is None or password_old == "":
        return {"status": False, "info": _("old_password_is_empty")}
    if password_new is None or password_new == "":
        return {"status": False, "info": _("the_new_password_is_blank")}
    if password_old == password_new:
        return {"status": False, "info": _("old_and_new_passwords_are_identical_dot_")}
    if not UserManager.get_instance().check_user_exist(user_id):
        return {"status": False, "info": _("user_does_not_exist")}
    if not UserManager.get_instance().check_user_password(user_id, password_old):
        return {"status": False, "info": _("original_password_error")}
    if UserManager.get_instance().change_user_password(user_id, password_new):
        return {"status": True, "info": _("successfully_set")}
    else:
        return {"status": False, "info": _("setup_failed")}


def other_func(string: str) -> str:
    return DEFAULT_TEXT


def get_json_content(string):
    match = re.search(r'{.*}', string)
    if match is not None:
        info = match.group()
        dic = json.loads(info)
        return info, dic
    return None, None


class UserManagerBot:
    def __init__(self):
        engine_type = os.getenv("DEFAULT_TOOL_LLM", "gpt-3.5-turbo")
        api_method, api_key, url, model = llm_tools.select_llm_model(engine_type)
        logger.debug(f"api_method {api_method}, {url}, {model}")
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY", None)
        config = {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                    "base_url": url,
                }
            ]
        }

        self.assistant = ConversableAgent(
            name="LLMParser",
            system_message="User administrator, please answer other questions in Chinese. Support registration, login, change password, do not answer other questions;"
            "When the task result is 'TERMINATE'",
            llm_config=config,
            default_auto_reply=DEFAULT_TEXT,
            human_input_mode="NEVER",
            is_termination_msg=UserManagerBot.check_terminal,
            max_consecutive_auto_reply=5,
        )

        self.user_proxy = ConversableAgent(
            name="FuncRunner",
            llm_config=False,
            default_auto_reply=DEFAULT_TEXT,
            human_input_mode="NEVER",
            is_termination_msg=UserManagerBot.check_terminal,
            max_consecutive_auto_reply=5,
        )

        self.register_tools(
            register,
            "register",
            "User registration tool: If the username or password is not entered, it will be set to the string '', and the password cannot be fabricated or guessed.",
        )
        self.register_tools(
            login,
            "login",
            "User login tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password.",
        )
        self.register_tools(
            change_password,
            "change_password",
            "User password change tool: if no username, old password, or new password is provided, set them as the string ''; if only one password is provided, set the old password as ''",
        )
        self.register_tools(
            other_func,
            "other_func",
            "If it is not registration, login, or password change, return the default prompt",
        )

    def register_tools(self, func, name, description):
        register_function(
            func,
            caller=self.assistant,
            executor=self.user_proxy,
            name=name,
            description=description,
        )

    @staticmethod
    def check_terminal(msg):
        if msg.get("content") is not None:
            if "TERMINATE" in msg["content"]:
                return True
            if _("please_sign_up_or_log_in_first") in msg["content"]:
                return True
            try:
                info, dic = get_json_content(msg["content"])
                if dic is not None:
                    if "status" in dic and "info" in dic:
                        return True
                    elif "user_id" in dic and "password" in dic:
                        return True
            except:
                pass
            logger.debug(f"not terminate ------ {msg}")
        return False

    def chat(self, string):
        try:
            ret = self.user_proxy.initiate_chat(
                self.assistant, message=string, clear_history=True
            )
            if len(ret.chat_history) > 0:
                output = "TERMINATE"
                for i in range(len(ret.chat_history) - 1, -1, -1):
                    logger.debug(f"check result: {ret.chat_history[i]}")
                    if ret.chat_history[i]["content"] != "TERMINATE":
                        output = ret.chat_history[-1]["content"]
                        try:
                            info, dic = get_json_content(output)
                            if dic is not None:
                                if "status" in dic and "info" in dic:
                                    return dic["info"]
                                elif "user_id" in dic and "password" in dic:
                                    return info
                        except Exception as e:
                            pass
                if output != "TERMINATE":
                    return output
        except Exception as e:
            logger.error(f"chat {e}")
        return DEFAULT_TEXT


class UserTools:
    _instance = None
    MAX_USER = 100

    @staticmethod
    def get_instance():
        if UserTools._instance is None:
            UserTools._instance = UserTools()
        return UserTools._instance

    def __init__(self):
        self.user_cache = deque(maxlen=UserTools.MAX_USER)
        self.user_manager = {}

    def chat(self, user_name, string):
        if user_name not in self.user_manager:
            if len(self.user_cache) == UserTools.MAX_USER:
                oldest_user = self.user_cache.popleft()
                del self.user_manager[oldest_user]
            self.user_cache.append(user_name)
            self.user_manager[user_name] = UserManagerBot()
        uagent = self.user_manager[user_name]
        return uagent.chat(string)
