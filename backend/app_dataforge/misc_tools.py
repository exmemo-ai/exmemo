import os
from django.utils.translation import gettext as _
from app_dataforge.entry import add_data
from backend.common.utils.web_tools import download_file
from backend.common.user.user import UserManager

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
        "source": "wechat",
    }
    if args.get("resource_path"):
        # xieyan 250122 建议有几项直接写在meta里
        dic["title"] = args["title"]
        dic["resource_path"] = args["resource_path"] # path inner
        dic["path"] = args["resource_path"] # path outer, use edit
        dic["add_date"] = args["add_date"]
        dic["source"] = args["source"]
        dic["error"] = args["error"]
        dic["is_batch"] = args.get("is_batch", False) # xieyan add
        meta = {"error": dic.pop("error", None)}
        meta.update({
            "update_path":dic['resource_path'],
            "resource_path": dic.pop("resource_path"),
            "visit_history": dic.pop("visit_history", [dic["add_date"]]),
            "add_date": dic.pop("add_date"),
            # from bm navigate
            "clicks":dic.pop("clicks", 1),
            "weight": dic.pop("weight", 0.0),
            "custom_order": dic.pop("custom_order", 0),
        })            
        dic["meta"] = meta
    return dic


def add_url(url, args, status):
    user = UserManager.get_instance().get_user(args["user_id"])
    if args["source"] == "bookmark" and user.get("bookmark_download_web") == False:
        wtype = "error"
        detail = _("download_web_not_allowed")
    else:
        wtype, detail = get_web_type(url)
    if wtype in ["html", "error"]:
        dic = create_dic(url, args, status)
        if wtype == "error":
            dic["error"] = detail
        ret, ret_emb, info = add_data(dic)
        return ret, detail, info
    if wtype == "pdf":
        return ret, detail, "pdf"
    return False, detail, _("unsupported_document_type")


