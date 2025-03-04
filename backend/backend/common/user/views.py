import json
from loguru import logger
from django.http import JsonResponse
from django.contrib.auth import get_user_model, login
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.auth import TokenAuthentication
from knox.views import LoginView as KnoxLoginView

from backend.common.utils.net_tools import do_result
from backend.common.user.resource import ResourceManager
from backend.common.speech.tts import tts_get_voice_list, tts_get_engine_list
from backend.common.user.user import (
    UserManager,
    USER_LEVEL_GUEST,
    USER_LEVEL_NORMAL,
    DEFAULT_PASSWORD,
    DEFAULT_USER,
    ADMIN_USER,
    ADMIN_PASSWORD,
    DEFAULT_CHAT_LLM_MEMORY_COUNT,
    DEFAULT_CHAT_LLM_PROMPT, 
    DEFAULT_CHAT_LLM_SHOW_COUNT,
    DEFAULT_CHAT_MAX_CONTEXT_COUNT,
)
from .utils import parse_common_args


class UserAPIView(APIView):

    def post(self, request):
        return self.do_user(request)

    def get(self, request):
        return self.do_user(request)

    def do_user(self, request):
        logger.debug(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", "unknown"))
        logger.debug(f"user, rtype: {rtype}")
        if rtype == "check_password":
            return self.password_check(request)
        elif rtype == "set_password":
            return self.password_set(request)
        elif rtype == "register":
            return self.register_user(request)
        else:
            return do_result(False, _("method_not_supported_colon_") + rtype)

    def register_user(self, request):
        user_id = request.GET.get("user_id", request.POST.get("user_id", None))
        password = request.GET.get("password", request.POST.get("password", None))
        if user_id is not None and password is not None:
            if UserManager.get_instance().check_user_exist(user_id):
                return do_result(False, _("username_already_exists"))
            if UserManager.get_instance().create_user(user_id, password):
                return do_result(True, _("account_created__excl_"))
            else:
                return do_result(False, _("registration_failed"))
        else:
            return do_result(False, _("user_or_password_are_empty_dot_"))

    def password_set(self, request):
        uid = request.GET.get("user_id", request.POST.get("user_id", None))
        logger.warning(f"password_set {request.data}  args {uid}")
        if not UserManager.get_instance().check_user_exist(uid):
            return do_result(False, _("user_does_not_exist"))
        password_new = request.GET.get(
            "password_new", request.POST.get("password_new", None)
        )
        password_old = request.GET.get(
            "password_old", request.POST.get("password_old", DEFAULT_PASSWORD)
        )
        if not UserManager.get_instance().check_user_password(uid, password_old):
            return do_result(False, _("original_password_error"))
        if password_new is not None:
            if UserManager.get_instance().change_user_password(uid, password_new):
                return do_result(True, _("successfully_set"))
            else:
                return do_result(False, _("setup_failed"))
        else:
            return do_result(False, _("the_new_password_is_blank"))

    def password_check(self, request):
        uid = request.GET.get("user_id", request.POST.get("user_id", None))
        if not UserManager.get_instance().check_user_exist(uid):
            return JsonResponse({"user_status": "not_exist"})
        if UserManager.get_instance().check_user_password(uid, DEFAULT_PASSWORD):
            return JsonResponse({"user_status": "init"})
        else:
            return JsonResponse({"user_status": "set"})


class SettingAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        args = parse_common_args(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", "get_setting"))
        user = UserManager.get_instance().get_user(args["user_id"])
        if rtype == "get_setting":
            return self.get_setting(args["user_id"], user)
        elif rtype == "get_voice":
            return self.get_voice(request, user)
        elif rtype == "save":
            return self.save_settings(request, user)
        elif rtype == "reset":
            return self.reset_settings(request, user)
        return do_result(False, _("method_not_supported_colon_") + rtype)

    def get_setting(self, uid, user):
        setting = user.settings.get_json()
        engine_list = tts_get_engine_list(uid)
        usage = ResourceManager.get_instance().get_usage_summary(uid)
        privilege = (
            _("user_level: {level}").format(level=user.get_level_desc())
            + "\n" + user.privilege.get_descript()
        )
        detail = {
            "setting": setting,
            "engine_list": engine_list,
            "privilege": privilege,
            "usage": usage,
        }
        logger.debug(f"setting {detail}")
        return do_result(True, detail)

    def get_voice(self, request, user):
        engine_name = request.GET.get(
            "tts_engine", request.POST.get("tts_engine", "xunfei")
        )
        logger.debug(f"engine_name {engine_name}")
        voice_list = tts_get_voice_list(engine_name)
        info = {"voice_list": voice_list}
        return do_result(True, info)

    def save_settings(self, request, user):
        settings = {}
        req_params = {**request.GET.dict(), **request.POST.dict()}
        
        logger.info(f"params {req_params}")
        basic_settings = [
            'tts_engine', 'tts_voice', 'tts_language', 'tts_speed',
            'llm_chat_prompt', 'llm_chat_show_count',
            'llm_chat_max_context_count', 'llm_chat_memory_count',
            'truncate_max_length', 'truncate_mode',
            'learn_word_voc', 'default_vault'
        ]
        
        boolean_settings = [
            'batch_use_llm', 'bookmark_download_web', 
            'web_save_content', 'web_get_category', 'web_get_abstract',
            'file_save_content', 'file_get_category', 'file_get_abstract',
            'note_save_content', 'note_get_category', 'note_get_abstract',
            'truncate_content'
        ]

        # basic format
        for key in basic_settings:
            if key in req_params:
                settings[key] = req_params[key]
        
        # boolean format
        for key in boolean_settings:
            if key in req_params:
                value = req_params[key]
                if isinstance(value, str):
                    settings[key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    settings[key] = bool(value)
                
        # json format
        for model_key in ['llm_chat_model', 'llm_tool_model']:
            if model_key in req_params:
                value = req_params[model_key]
                if value.startswith('{') and value.endswith('}'):
                    try:
                        settings[model_key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON for {model_key}")

        if settings:
            user.set_multiple(settings)
        return do_result(True, _("settings_were_applied_successfully"))

    def reset_settings(self, request, user):
        user.reset_setting()
        info = _("settings_were_applied_successfully")
        return do_result(True, info)


class LoginView(KnoxLoginView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, format=None):
        LoginView.create_user_default()
        LoginView.create_user_admin()
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(LoginView, self).post(request, format=None)

    @staticmethod
    def create_user(user_id, password, level=USER_LEVEL_NORMAL):
        if not UserManager.get_instance().check_user_exist(user_id):
            logger.info(f"Creating user {user_id}")
            UserManager.get_instance().create_user(
                user_id, level=level, password=password
            )

    @staticmethod
    def create_user_default():
        LoginView.create_user(DEFAULT_USER, DEFAULT_PASSWORD, level=USER_LEVEL_GUEST)

    @staticmethod
    def create_user_admin():
        # django user, not our user
        user = get_user_model()
        if not user.objects.filter(username=ADMIN_USER).exists():
            user.objects.create_superuser(ADMIN_USER, password=ADMIN_PASSWORD)
            print("Superuser created successfully.")
