import re
import pandas as pd
from django.utils.translation import gettext as _
from .command import *
from backend.common.utils.regular_tools import regular_str
from app_dataforge.entry import get_entry_list

CMD_INNER_GET = "CMD_INNER_GET"

def regular_title(title):
    """
    Limit title length, remove special characters
    """
    if title is not None:
        title = title.strip()
        title = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]+", "", title)
        title = title[:20]
    return title

    
def search_data(sdata, dic={}):
    """
    Search for data
    """
    condition = {"user_id": sdata.user_id}
    condition.update(dic)
    if len(sdata.current_content) > 0:
        keyword = sdata.current_content
    else:
        keyword = None
    logger.info(f"condition {condition}")
    queryset = get_entry_list(keyword, condition, 5)
    df = pd.DataFrame(queryset.values())
    arr = []
    for idx, item in df.iterrows():
        label = regular_str(item["title"], del_enter=True, max_length=25)
        value = CMD_INNER_GET + " " + str(item["idx"])
        arr.append((label, value))

    if len(arr) == 0:
        return _("no_content_found_1727252424")
    elif len(arr) == 1:
        sdata.current_content = arr[0][1]
        ret, detail = CommandManager.get_instance().msg_do_command(sdata)
        logger.error(f'detail {detail}')
        return detail
    else:
        return msg_common_select(sdata, arr)


