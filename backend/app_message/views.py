import json
import traceback
from loguru import logger

from django.http import HttpResponse
from rest_framework.views import APIView
from knox.auth import TokenAuthentication

import backend.common.files.filecache as filecache
from backend.common.utils.net_tools import do_result
from backend.common.user.utils import parse_common_args
from backend.common.user.views import LoginView
from backend.common.user.user import DEFAULT_USER
from backend.common.utils.file_tools import get_ext
import app_message.user_manager as user_manager
from .message import *


class MessageAPIView(APIView):
    def post(self, request):
        """
        Accept and process text messages, including URLs
        """
        auth = TokenAuthentication()
        user_auth_tuple = auth.authenticate(request)
        has_token = False
        logger.info(f"user_auth_tuple {user_auth_tuple}")
        if user_auth_tuple is not None:
            request.user, request.auth = user_auth_tuple
            has_token = True

        args = parse_common_args(request)
        logger.info(
            f'request.data {request.data}, has_token {has_token}, is_group {args["is_group"]}'
        )

        if has_token or args["is_group"]:
            logger.info(f"message recv: args {args}")
            if "user_id" not in args or args["user_id"] is None:
                args["user_id"] = DEFAULT_USER
            if args["user_id"] == DEFAULT_USER:
                LoginView.create_user_default()

            rtype = request.POST.get("rtype", "text")
            try:
                if rtype == "text":
                    ret, detail = do_message(args)
                    logger.debug(f"{ret}, {detail}")
                    return do_result(ret, detail)
                elif rtype == "file":
                    return self.upload_file(request)
            except Exception as e:
                logger.warning(f"message failed {e}")
                traceback.print_exc()
            return HttpResponse(
                json.dumps(
                    {"status": "failed", "info": _("f'Backend processing failed'")}
                )
            )
        else:
            content = request.POST.get("content", None)
            user_name = request.POST.get("user_name", DEFAULT_USER)
            if content is None:
                return HttpResponse(
                    json.dumps(
                        {
                            "status": "failed",
                            "info": _("please_sign_up_or_log_in_first"),
                        }
                    )
                )
            ret = user_manager.UserTools.get_instance().chat(user_name, content)
            return HttpResponse(json.dumps({"status": "success", "info": ret}))

    def upload_file(self, request):
        args = parse_common_args(request)
        ret, path, filename = real_upload_file(request)
        if ret:
            ret, detail = msg_recv_file(
                path, filename, args
            )  # May return files or text
            return do_result(True, detail)  # return True to show info
        return HttpResponse(
            json.dumps({"status": "failed", "info": _("f'Backend processing failed'")})
        )


def real_upload_file(request):
    logger.debug(f"real_upload_file {request.FILES}")
    files = request.FILES
    for file in files.values():  # only one file
        filename = file.name
        tmp_path = filecache.get_tmpfile(get_ext(filename))
        logger.debug(f"file save to {tmp_path}")
        with open(tmp_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        return True, tmp_path, filename
    return False, None, None
