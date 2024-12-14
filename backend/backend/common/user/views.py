import json
from loguru import logger
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model, login
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.auth import TokenAuthentication
from knox.views import LoginView as KnoxLoginView

from backend.common.utils.net_tools import do_result
from backend.common.speech.tts import tts_get_voice_list, tts_get_engine_list
from backend.common.llm.llm_tools import DEFAULT_CHAT_LLM,  get_llm_list
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
            return JsonResponse({"status": _("method_not_supported_colon_") + rtype})

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
        logger.debug(f"setting {setting}")
        engine_list = tts_get_engine_list(uid)
        llm_list = get_llm_list()
        privilege = (
            _("User Level: {level_desc}\n").format(level_desc=user.get_level_desc())
            + user.privilege.get_descript()
        )
        info = {
            "setting": setting,
            "engine_list": engine_list,
            "llm_list": llm_list,
            "privilege": privilege,
        }
        return HttpResponse(json.dumps({"status": "success", "info": info}))

    def get_voice(self, request, user):
        engine_name = request.GET.get(
            "tts_engine", request.POST.get("tts_engine", "xunfei")
        )
        logger.debug(f"engine_name {engine_name}")
        voice_list = tts_get_voice_list(engine_name)
        info = {"voice_list": voice_list, "voice_settings": user.settings.tts_voice}
        return HttpResponse(json.dumps({"status": "success", "info": info}))

    def save_settings(self, request, user):
        engine_name = request.GET.get(
            "tts_engine", request.POST.get("tts_engine", "xunfei")
        )
        voice_name = request.GET.get(
            "tts_voice", request.POST.get("tts_voice", "default")
        )
        language_name = request.GET.get(
            "tts_language", request.POST.get("tts_language", "mix")
        )
        logger.debug(f"language_name {language_name}")
        speed_name = request.GET.get("tts_speed", request.POST.get("tts_speed", "1.0"))
        llm_chat_model = request.GET.get(
            "llm_chat_model", request.POST.get("llm_chat_model", DEFAULT_CHAT_LLM)
        )
        llm_tool_model = request.GET.get(
            "llm_tool_model", request.POST.get("llm_tool_model", DEFAULT_CHAT_LLM)
        )
        llm_chat_prompt = request.GET.get("llm_chat_prompt", request.POST.get("llm_chat_prompt", DEFAULT_CHAT_LLM_PROMPT))
        llm_chat_show_count = request.GET.get("llm_chat_show_count", request.POST.get("llm_chat_show_count", DEFAULT_CHAT_LLM_SHOW_COUNT))
        llm_chat_memory_count = request.GET.get("llm_chat_memory_count", request.POST.get("llm_chat_memory_count", DEFAULT_CHAT_LLM_MEMORY_COUNT))
        user.set("tts_engine", engine_name, save=False)
        user.set("tts_voice", voice_name, save=False)
        user.set("tts_language", language_name, save=False)
        user.set("tts_speed", speed_name, save=False)
        user.set("llm_chat_model", llm_chat_model, save=False)
        user.set("llm_tool_model", llm_tool_model, save=False)
        user.set("llm_chat_prompt", llm_chat_prompt, save=False)
        user.set("llm_chat_show_count", llm_chat_show_count, save=False)
        user.set("llm_chat_memory_count", llm_chat_memory_count, save=False)
        user.save()
        info = _("settings_were_applied_successfully")
        return do_result(True, info)

    def reset_settings(self, request, user):
        user.reset_setting()
        info = _("settings_were_applied_successfully")
        return do_result(True, info)


class LoginView(KnoxLoginView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, format=None):
        logger.warning("now LoginView")
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
