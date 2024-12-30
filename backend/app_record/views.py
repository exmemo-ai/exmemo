import os
from loguru import logger

from wsgiref.util import FileWrapper
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from backend.common.user.utils import parse_common_args
from backend.common.utils.file_tools import get_content_type
from backend.common.utils.net_tools import do_result

from .record import get_export_file


class RecordAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_record(request)

    def get(self, request):
        return self.do_record(request)

    def do_record(self, request):
        """
        Operation Record
        """

        args = parse_common_args(request)
        logger.info(f"record {args}")
        rtype = request.GET.get("rtype", request.POST.get("rtype", "get"))
        if rtype == "export":  # Export Record Sheet
            return self.export_record(args)
        return do_result(False, _("interface_is_deprecated"))

    def export_record(self, args):
        """
        Export Record Table
        """
        ret, info = get_export_file(args["user_id"])
        if ret:
            file_path = info
            with open(file_path, "rb") as file:
                # Create an HttpResponse object
                ctype = get_content_type(file_path)
                response = HttpResponse(FileWrapper(file), ctype)
                # Set file name
                file_name = os.path.basename(file_path)
                file_name = smart_str(file_name)
                logger.debug(
                    f"download content type {ctype}; smart_str, filename:{file_name}"
                )
                response["Content-Disposition"] = f'attachment; filename="{file_name}"'
                # Add the necessary CORS headers
                response["Access-Control-Allow-Origin"] = "*"
                response["Access-Control-Expose-Headers"] = "Content-Disposition"
                return response
        return do_result(False, info)
