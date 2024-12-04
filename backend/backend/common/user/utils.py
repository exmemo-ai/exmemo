from .user import DEFAULT_SESSION
from loguru import logger


def get_user_id(request):
    try:
        return request.user.username
    except Exception as e:
        logger.error(f"get_user_id failed {e}")
    return None


def parse_common_args(request):
    """
    Parse public parameters
    """
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
    }
    return args
