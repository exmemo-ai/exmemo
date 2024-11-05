import json
from loguru import logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from backend.common.user.utils import parse_common_args
from rest_framework.response import Response
from app_dataforge.entry import check_entry_exist
from app_dataforge.views import delete_entry
from app_dataforge.misc_tools import add_url
from app_dataforge.models import StoreEntry

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
            # logger.info('item info',item)
            try:
                args["resource_path"] = f"chrome/{item.get('path')}"
                args["add_date"] = item.get("add_date")
                args["title"] = item.get("title")
                args['status'] = item.get('status')
                args["source"] = SOURCE
                args["parse_content"] = PARSE_CONTENT
                args["error"] = None
                action = item.get("action")
                if action == "delete":
                    queryset = StoreEntry.objects.filter(user_id=args["user_id"], addr=item.get('url'), is_deleted='f')
                    if queryset.exists():
                        delete_entry(args["user_id"], list(queryset.values()))
                        results.append(
                            {"url": item.get("url"), "status": "success", "info": "data_removed"}
                        )
                    else:
                        results.append(
                            {"url": item.get("url"), "status": "success", "info": "data_not_exist"}
                        )
                elif action == "move":
                    pass
                else:
                    if item.get("url") is not None:
                        # Check if the URL is in the database, return directly if it exists
                        if check_entry_exist(args["user_id"], item.get("url"), args["resource_path"]):
                            results.append(
                                {
                                    "url": item.get("url"),
                                    "status": "success",
                                    "info": "data_already_exists",
                                }
                            )
                        else:
                            ret, base_path, info = add_url(item.get("url"), args, item.get('status'))
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