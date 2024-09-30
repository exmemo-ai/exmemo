import os
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from loguru import logger
from django.utils.translation import gettext as _

STATUS_FIRST_FRAME = 0  # first frame
STATUS_CONTINUE_FRAME = 1  # Intermediate Frame
STATUS_LAST_FRAME = 2  # last frame

wsParam = {}
APPID = os.getenv("IFLYTEK_TTS_APPID", "")
APISecret = os.getenv("IFLYTEK_TTS_APISECRET", "")
APIKey = os.getenv("IFLYTEK_TTS_APIKEY", "")

from .tts_base import TtsEngine


class TtsXunfei(TtsEngine):
    def __init__(self):
        super().__init__()

    def estimate_time(self, text, speed=1.0, wps_dic: dict = None):
        convert_time = (
            len(text) / 100
        )  # About 10,000 words in approximately 400 seconds
        audio_time = len(text) / 5
        return convert_time, audio_time

    def synthesize(
        self, text, output_path, speed=1.0, language=None, voice=None, debug=False
    ):
        try:
            global wsParam
            speed_scale = int(float(speed) * 50)
            wsParam = {
                "save_path": output_path,
                "text": text,
                "speed": speed_scale,
                "voice": voice,
            }
            logger.info(
                f"wsParam is {wsParam['save_path']}, len:{len(wsParam['text'])}"
            )
            wsUrl = create_url()
            ws = websocket.WebSocketApp(
                wsUrl, on_message=on_message, on_error=on_error, on_close=on_close
            )
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            if "error" in wsParam:
                return False, wsParam["error"]
            return True, _("synthesis_complete")
        except Exception as e:
            logger.warning(f"failed {e}")
            return False, str(e)


def create_url():
    url = "ws://tts-api.xfyun.cn/v2/tts"
    # url = 'wss://tts-api.xfyun.cn/v2/tts'
    # Generate RFC1123-formatted timestamp
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    # Stitch Strings
    signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
    # Perform encryption using hmac-sha256
    signature_sha = hmac.new(
        APISecret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

    authorization_origin = (
        'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
        % (APIKey, "hmac-sha256", "host date request-line", signature_sha)
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
        encoding="utf-8"
    )
    #
    v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
    url = url + "?" + urlencode(v)
    return url


def on_message(ws, message):
    """
    Messages actively sent by the server via websocket
    """
    global wsParam
    try:
        message = json.loads(message)
        code = message["code"]
        sid = message["sid"]
        # logger.debug(f"sid:{sid}, code:{code}")
        # logger.debug(f"data:{message}")
        if "data" not in message:
            logger.debug(f"data:{message}")
            return
        audio = message["data"]["audio"]
        audio = base64.b64decode(audio)
        status = message["data"]["status"]
        if status == 2:
            print("ws is closed")
            ws.close()
        if code != 0:
            errMsg = message["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            print("write to file")
            with open(wsParam["save_path"], "ab") as f:
                f.write(audio)
                f.flush()

    except Exception as e:
        print("failed", e)
        print(message)
        import traceback

        traceback.print_exc()


def on_error(ws, error):
    global wsParam
    print("### error:", error)
    if str(error) != "'NoneType' object has no attribute 'connected'":
        # wsParam['error'] = str(error)
        print("error, but ok")


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    """
    This method will be called after the connection is established
    """
    global wsParam
    if wsParam["voice"] is not None:
        voice = wsParam["voice"]
    else:
        voice = "aisxping"  # "vcn": "xiaoyan",
    logger.debug(f"voice is {voice}")
    d = {
        "common": {"app_id": APPID},
        "business": {
            "aue": "lame",
            "auf": "audio/L16;rate=16000",
            "vcn": voice,
            "tte": "utf8",
            "speed": wsParam["speed"],
        },
        "data": {
            "status": 2,
            "text": str(base64.b64encode(wsParam["text"].encode("utf-8")), "UTF8"),
        },
    }
    d = json.dumps(d)
    print("------>Start sending text data")
    ws.send(d)
    if os.path.exists(wsParam["save_path"]):
        os.remove(wsParam["save_path"])
