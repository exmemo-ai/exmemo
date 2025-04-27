import datetime
import pandas as pd
from loguru import logger
from django.utils.translation import gettext as _

from backend.common.user.user import UserManager
from backend.common.utils.regular_tools import regular_str
from app_dataforge.models import StoreEntry


def get_detail(item):
    """
    Get the detailed content of the search results
    """
    if item["etype"] == "web":
        content = _("title_colon__enter_{title}_enter__enter_content_enter_{content}").format(
            title=regular_str(item["title"], del_enter=True, max_length=20),
            content=regular_str(item["raw"]),
        )
        content = content + "\n\n" + item["addr"]
    else:
        content = regular_str(item["raw"])
    return content


##########################


def get_export_file(uid):
    """
    Take records for a month and save them as an Excel file
    """
    user = UserManager.get_instance().get_user(uid)
    privilege = user.privilege
    limit_export_record_day = privilege.get("limit_export_record_day", -1)
    if limit_export_record_day == -1:
        return False, _(
            "your_account_currently_does_not_have_export_permissions_dot__please_contact_the_administrator_to_upgrade_your_account_dot_"
        )
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=limit_export_record_day)
    before = now - delta
    objs = StoreEntry.objects.filter(user_id=uid, etype='record', block_id__gt=0, 
                                     created_time__gte=before)
    df = pd.DataFrame(objs.values())
    if len(df) > 0:
        col_dic = {
            "addr": _("website"),
            "title": _("title"),
            "raw": _("content"),
            "atype": _("viewpoint"),
            "ctype": _("content_category_colon_"),
            "etype": _("data_type"),
            "status": _("status"),
            "created_time": _("creation_date"),
        }
        df = df[list(col_dic.keys())]
        df["created_time"] = df["created_time"].dt.strftime("%Y-%m-%d")
        df.rename(columns=col_dic, inplace=True)
        filename = f"/tmp/export.xlsx"
        df.to_excel(filename, index=False)
        return True, filename
    return False, _("no_record_found")
