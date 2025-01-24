import os
from loguru import logger
from django.utils.translation import gettext as _
from app_dataforge.entry import add_data
from backend.common.utils.web_tools import download_file
from backend.common.user.user import UserManager
from backend.common.utils.web_tools import test_url_valid

def get_web_type(url):
    ret, desc = download_file(url)
    if ret:
        ext = os.path.splitext(desc)[1][1:]
        if ext == "html":
            return "html", desc
        if ext == "pdf":
            return "pdf", desc
    else:
        if desc.startswith("error "):
            desc = desc[len("error ") :]
            return "error", desc
    return None, desc


def create_dic(url, args, status):
    dic = {
        "user_id": args["user_id"],
        "addr": url,
        "status": status,
        "etype": "web",
        "source": args.get("source", "wechat"),
    }
    
    if args.get("resource_path"):
        dic["title"] = args.get("title")
        dic["path"] = args.get("resource_path")  # path outer, use edit
        dic["source"] = args.get("source")

        meta = {"error": args.get("error"), "detail": args.get("detail")}
        meta.update({
            "is_batch": args.get("is_batch"), # wanglei 0124,is_batch 放在了 meta 里
            # path inner
            "update_path": args.get("resource_path"),
            "resource_path": args.get("resource_path"),
            #
            "add_date": args.get("add_date"),
            "visit_history": args.get("visit_history", [args.get("add_date")]),
            # from bm navigate
            "clicks": dic.pop("clicks", 1),
            "weight": dic.pop("weight", 0.0),
            "custom_order": dic.pop("custom_order", 0),
        })
        dic["meta"] = meta
    return dic


def add_url(url, args, status):
    user = UserManager.get_instance().get_user(args["user_id"])
    # wanglei 0124 error内容测试url连接是否有效
    if args["source"] == "bookmark" and user.get("bookmark_download_web") == False:
        wtype, detail = test_url_valid(url)
    else:
        wtype, detail = get_web_type(url)

    # logger.info(f"test_url_valid: {wtype}, {detail}")

    """
    user = UserManager.get_instance().get_user(args["user_id"])
    if args["source"] == "bookmark" and user.get("bookmark_download_web") == False:
        wtype = "error"
        detail = _("download_web_not_allowed")
    else:
        wtype, detail = get_web_type(url)
    """
    

    if wtype in ["html", "error"]:
        dic = create_dic(url, args, status)
        if wtype == "error":
            dic['meta']["error"] = detail
        ret, ret_emb, info = add_data(dic)
        return ret, detail, info
    if wtype == "pdf":
        return ret, detail, "pdf"
    return False, detail, _("unsupported_document_type")


