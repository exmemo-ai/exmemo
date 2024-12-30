from .user import DEFAULT_USER
from loguru import logger


def get_user_id(request):
    try:
        return request.user.username
    except Exception as e:
        logger.warning(f"get_user_id failed {e}")
    return DEFAULT_USER


def parse_common_args(request):
    """
    Parse public parameters
    """
    source = request.GET.get("source", request.POST.get("source", "wechat"))
    user_id = get_user_id(request)
    rtype = request.GET.get("rtype", request.POST.get("rtype", "html"))
    content = request.GET.get("content", request.POST.get("content", None))
    raw = request.GET.get("raw", request.POST.get("raw", None))
    is_group = request.GET.get("is_group", request.POST.get("is_group", "false"))
    if isinstance(is_group, str) and is_group.lower() == "true":
        is_group = True
    else:
        is_group = False

    args = {
        "rtype": rtype,
        "content": content,
        "raw": raw,
        "user_id": user_id,
        "is_group": is_group,
        "source": source,
    }
    return args
