import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from backend.common.user.utils import parse_common_args
from rest_framework.response import Response
from app_dataforge.entry import check_entry_exist
from app_dataforge.misc_tools import add_url

SOURCE = "web_chrome_bm"  # Where the annotation comes from
PARSE_CONTENT = False  # Whether to parse the content


class BookmarkAPIView(APIView):
    """
    Google Chrome Bookmark Synchronization API
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_web_bm(request)

    def do_web_bm(self, request):
        """
        Provide interfaces to support webpage parsing
        """
        debug = True
        args = parse_common_args(request)
        post_data_lis = request.data
        results = []

        for item in post_data_lis:
            try:
                args["resource_path"] = f"chrome/{item.get('path')}"
                args["add_date"] = item.get("add_date")
                args["title"] = item.get("title")
                args["source"] = SOURCE
                args["parse_content"] = PARSE_CONTENT
                args["error"] = None
                if item.get("url") is not None:
                    # Check if the URL is in the database, return directly if it exists
                    if check_entry_exist(args["user_id"], item.get("url")):
                        results.append(
                            {
                                "url": item.get("url"),
                                "status": "success",
                                "info": _("data_already_exists"),
                            }
                        )
                    else:
                        ret, info = add_url(item.get("url"), args, "collect")
                        results.append(
                            {"url": item.get("url"), "status": "success", "info": info}
                        )
            except json.JSONDecodeError as e:
                results.append(
                    {"url": item.get("url"), "status": "failed", "error": str(e)}
                )
            except Exception as e:
                results.append(
                    {"url": item.get("url"), "status": "failed", "error": str(e)}
                )
        return Response({"status": "success", "results": results})
