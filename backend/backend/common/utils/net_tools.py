import re
import json
from loguru import logger
from django.http import HttpResponse, FileResponse


def do_result(ret, detail):
    if ret:
        dic = {"status": "success"}
        if isinstance(detail, str):
            dic["info"] = detail
        elif isinstance(detail, dict):
            if ("type" in detail
                and detail["type"] in ["file", "audio"]
                and "path" in detail
            ):
                file = open(detail["path"], "rb")
                if detail["type"] == "audio":
                    response = FileResponse(file, content_type="audio/mpeg")
                else:
                    response = FileResponse(
                        file, content_type="application/octet-stream"
                    )
                response["Content-Disposition"] = (
                    f'attachment; filename="{detail["filename"]}"'
                )
                return response
            else:
                for key in detail:
                    dic[key] = detail[key]
        elif detail is not None:
            logger.warning(f"do_result: unknown type {type(detail)}, detail: {detail}")
        return HttpResponse(json.dumps(dic))
    else:
        if isinstance(detail, str):
            return HttpResponse(json.dumps({"status": "failed", "info": detail}))
        else:
            return HttpResponse(json.dumps({"status": "failed"}))


def is_valid_url(s):
    # Use regular expressions to check if the string is a valid URL
    url_pattern = re.compile(
        r"^(http|https):\/\/"  # Protocol section, can be either http or https
        r"([a-zA-Z0-9.-]+)"  # Domain part, including letters, numbers, dots, and hyphens
        r"(\.[a-zA-Z]{2,})"  # Top-level domain, at least two letters
        r"(:\d{1,5})?"  # Port section, optional
        r"(\/[^\s]*)?$"  # Path part, optional
    )
    return bool(url_pattern.match(s))


def test_valid_url():
    url1 = "https://www.example.com"
    url2 = "ftp://invalid-url"
    url3 = "not a url"

    print(is_valid_url(url1))  # True
    print(is_valid_url(url2))  # False
    print(is_valid_url(url3))  # False
