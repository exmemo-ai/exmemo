import os
import json
from loguru import logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import gettext as _
from knox.auth import TokenAuthentication
import shutil

from backend.common.speech.tts import start_tts
from backend.settings import MEDIA_ROOT, MEDIA_FILE_DIR
from backend.common.user.utils import parse_common_args
from backend.common.utils.net_tools import do_result
from backend.common.files import filecache
from . import ptools


class PaperAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Provide interfaces to support the paper analysis page
        """
        args = parse_common_args(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", None))
        content = request.GET.get("content", request.POST.get("content", None))
        logger.debug(f"rtype *{rtype}*")

        if rtype == "tts":
            return self.handle_tts_request(content, args)
        elif rtype == "search":
            return self.handle_search_request(content, args)
        elif rtype == "gpt":
            return self.handle_gpt_request(content, args)
        elif rtype == "polish":
            return self.handle_polish_request(content, args)
        elif rtype == "translate":
            return self.handle_translate_request(content, args)
        return do_result(False, _("method_not_supported_colon_") + rtype)

    def handle_tts_request(self, content, args):
        logger.debug(f"args {args}")
        logger.debug(f"content {content[:20]}")

        static_path = settings.STATICFILES_DIRS
        sub_path = os.path.join("audio", f"{args['user_id']}.mp3")
        rel_path = os.path.join("static", sub_path)
        mp3_path = os.path.join(static_path[0], sub_path)
        logger.debug(f"rel_path {rel_path}")
        logger.debug(f"mp3_path {mp3_path}")

        ret, _, detail = start_tts(
            "tmp",
            content,
            args["user_id"],
            args["session_id"],
            force_fg=True,
            debug=True,
        )

        if ret:
            mp3_dir = os.path.dirname(mp3_path)
            if not os.path.exists(mp3_dir):
                os.makedirs(mp3_dir)
            shutil.copy(detail["content"], mp3_path)
            filecache.TmpFileManager.get_instance().add_file(mp3_path)
            return HttpResponse(
                json.dumps({"status": "success", "audio_url": "/" + rel_path})
            )
        else:
            return do_result(False, str(detail))

    def handle_search_request(self, content, args):
        logger.debug(f"content {content}")
        info = ptools.parse_paper(
            args["user_id"], content, use_llm=True, use_google=True
        )  # for test
        return do_result(True, info)

    def handle_gpt_request(self, content, args):
        if content is not None:
            logger.debug(f"content {content[:20]}")
        ret, info = ptools.gpt(args["user_id"], content)
        if ret:
            return do_result(True, str(info))
        else:
            return do_result(False, str(info))

    def handle_polish_request(self, content, args):
        if content is not None:
            logger.debug(f"content {content[:20]}")
        ret, info = ptools.polish(args["user_id"], content)
        if ret:
            return do_result(True, str(info))
        else:
            return do_result(False, str(info))

    def handle_translate_request(self, content, args):
        if content is not None:
            logger.debug(f"content {content[:20]}")
        ret, info = ptools.translate(args["user_id"], content)
        if ret:
            return do_result(True, str(info))
        else:
            return do_result(False, str(info))
