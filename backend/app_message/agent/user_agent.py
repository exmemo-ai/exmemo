from loguru import logger
from django.utils.translation import gettext as _
from app_message.command import msg_common_select
from backend.common.speech.tts import (
    tts_get_voice_and_engine,
    tts_set_engine,
)
from backend.common.user.user import *
from backend.common.user.resource import *
from app_message.agent.base_agent import BaseAgent, agent_function

class UserAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("user_management")

    @staticmethod
    def register(user_id: str, password: str) -> dict:
        if (
            user_id is not None
            and len(user_id) > 0
            and password is not None
            and len(password) > 0
        ):
            if UserManager.get_instance().check_user_exist(user_id):
                return False, _("username_already_exists")
            if UserManager.get_instance().create_user(user_id, password):
                return True, _("registration_successful")
            else:
                return False, _("registration_failed")
        else:
            return False, _("user_or_password_are_empty_dot_")

    @staticmethod
    def change_password(user_id: str, password_old: str, password_new: str) -> dict:
        if user_id is None or user_id == "":
            return False, _("empty_username")
        if password_old is None or password_old == "":
            return False, _("old_password_is_empty")
        if password_new is None or password_new == "":
            return False, _("the_new_password_is_blank")
        if password_old == password_new:
            return False, _("old_and_new_passwords_are_identical_dot_")
        if not UserManager.get_instance().check_user_exist(user_id):
            return False, _("user_does_not_exist")
        if not UserManager.get_instance().check_user_password(user_id, password_old):
            return False, _("original_password_error")
        if UserManager.get_instance().change_user_password(user_id, password_new):
            return True, _("change_successful")
        else:
            return False, _("setup_failed")


    @agent_function(_("user_registration"), is_command=False)
    def _afunc_register(context_variables: dict = None, user_id: str = None, password: str = None) -> dict:
        """User registration tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password."""
        if context_variables is None or 'sdata' not in context_variables or user_id is None or password is None:
            return _("params_error")
        ret, info = UserAgent.register(user_id, password)
        if ret:
            context_variables['sdata'].set_cache('user_id', user_id)
            context_variables['sdata'].set_cache('password', password)
        return info

    @agent_function(_("user_login"), is_command=False)
    def _afunc_login(context_variables: dict = None, user_id: str = None, password: str = None) -> dict:
        """User login tool: if a username or password is entered, set it to the string '', cannot fabricate or guess the password. """
        if context_variables is None or 'sdata' not in context_variables or user_id is None or password is None:
            return _("params_error")
        context_variables['sdata'].set_cache('user_id', user_id)
        context_variables['sdata'].set_cache('password', password)
        ret = {"user_id": user_id, "password": password}
        return ret

    @agent_function(_("change_password"), is_command=False)
    def _afunc_change_password(context_variables: dict = None, user_id: str = None, password_old: str = None, password_new: str = None) -> dict:
        """User password change tool: if no username, old password, or new password is provided, set them as the string ''; if only one password is provided, set the old password as ''"""
        if context_variables is None or 'sdata' not in context_variables or user_id is None or password_old is None or password_new is None:
            return _("params_error")
        ret, info = UserAgent.change_password(user_id, password_old, password_new)
        if ret:
            context_variables['sdata'].set_cache('user_id', user_id)
            context_variables['sdata'].set_cache('password', password_new)
        return info

    @agent_function(_("user_logout"))
    def _afunc_logout(context_variables: dict = None):
        """User logout tool"""
        return json.dumps({"logout": True})


class SettingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_name = _("system_settings")

    @agent_function(_("query_user_privileges"))
    def _afunc_user_privilege(context_variables: dict = None):
        """Query user privileges"""
        if context_variables is None or 'sdata' not in context_variables:
            return _("params_error")
        sdata = context_variables["sdata"]
        user = UserManager.get_instance().get_user(sdata.user_id)
        privilege = _("user_level: {level}").format(level=user.get_level_desc()) + "\n" + user.privilege.get_descript()
        return privilege
            

    @agent_function(_("query_resource_usage"))
    def _afunc_resource_usage(context_variables: dict = None):
        """Query resource usage"""
        if context_variables is None or 'sdata' not in context_variables:
            return _("params_error")
        sdata = context_variables["sdata"]
        return "\n" + ResourceManager.get_instance().get_usage_summary(sdata.user_id)

    @agent_function(_("set_text_to_speech"))
    def _afunc_tts_setting(context_variables: dict = None, content: str = None):
        """Set text-to-speech"""
        if context_variables is None or 'sdata' not in context_variables:
            return _("params_error")
        sdata = context_variables["sdata"]
        if content is None:
            content = sdata.current_content           
        logger.debug(f"msg_tts_setting '{content}'")
        if content == "":
            cmd_list = tts_get_voice_and_engine(sdata.user_id, _("set_text_to_speech"))
            return msg_common_select(sdata, cmd_list)
        else:
            name = content
            engine_setting = name.strip()
            ret, detail = tts_set_engine(engine_setting, sdata.user_id)
            return detail