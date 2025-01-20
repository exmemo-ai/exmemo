import os
from django.utils.translation import gettext as _
from app_dataforge.entry import add_data
from backend.common.utils.web_tools import download_file


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
        dic["title"] = args["title"]
        dic["resource_path"] = args["resource_path"] # path inner
        dic["path"] = args["resource_path"] # path outer, use edit
        dic["add_date"] = args["add_date"]
        dic["source"] = args["source"]
        dic["error"] = args["error"]
    return dic


def add_url(url, args, status):
    wtype, base_path = get_web_type(url)
    if wtype in ["html", "error"]:
        dic = create_dic(url, args, status)
        if wtype == "error":
            dic["error"] = base_path
        ret, ret_emb, info = add_data(dic)
        return ret, base_path, info
    if wtype == "pdf":
        return ret, base_path, "pdf"
    return False, base_path, _("unsupported_document_type")
