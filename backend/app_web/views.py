from loguru import logger

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication

from backend.common.user.utils import parse_common_args
from backend.common.utils.web_tools import get_url_content, get_web_abstract
from backend.common.utils.net_tools import do_result


class WebAPIView(APIView):
    """
    Web Interface Utility Tools: Web-Related Features
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_web(request)

    def get(self, request):
        return self.do_web(request)

    def do_web(self, request):
        """
        Provide interfaces to support webpage parsing
        """
        args = parse_common_args(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", None))
        content = request.GET.get("content", request.POST.get("content", None))
        logger.debug(f"web_tools, rtype *{rtype}*")

        if not content.startswith("http"):
            url = f"http://{content}"
        else:
            url = content

        if rtype == "content":  # TakeContent
            title, content = get_url_content(url)
            logger.info(f"web_tools, title *{title}*, content *{content}*")
            return do_result(True, str(content))
        elif rtype == "abstract":  # FetchSummary
            detail = get_web_abstract(args["user_id"], url)
            return do_result(True, str(detail))
