import re
import json
from django.http import HttpResponse, FileResponse


def do_result(ret, detail):
    if ret:
        if isinstance(detail, dict):
            if (
                "type" in detail
                and detail["type"] in ["file", "audio"]
                and "content" in detail
            ):
                file = open(detail["content"], "rb")
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
            elif ("type" in detail and detail["type"] == "json"):
                if 'status' not in detail:
                    detail['status'] = 'success'
                return HttpResponse(json.dumps(detail))
            else:
                ret_dic = {"status": "success", "info": detail["content"]}
                if "type" in detail:
                    ret_dic["type"] = detail["type"]
                if "request_delay" in detail:
                    ret_dic["request_delay"] = detail["request_delay"]
                return HttpResponse(json.dumps(ret_dic))
        if isinstance(detail, str):
            return HttpResponse(json.dumps({"status": "success", "info": detail}))
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
