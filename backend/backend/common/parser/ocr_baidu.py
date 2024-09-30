import os
from aip import AipOcr
from loguru import logger

baidu_client = None


def get_baidu_client(force=False):
    global baidu_client
    if force or baidu_client is None:
        BAIDU_OCR_APPID = os.getenv("BAIDU_OCR_APPID", "")
        BAIDU_OCR_API_KEY = os.getenv("BAIDU_OCR_API_KEY", "")
        BAIDU_OCR_SECRET_KEY = os.getenv("BAIDU_OCR_SECRET_KEY", "")

        if (
            BAIDU_OCR_APPID != ""
            and BAIDU_OCR_API_KEY != ""
            and BAIDU_OCR_SECRET_KEY != ""
        ):
            baidu_config = {
                "appId": BAIDU_OCR_APPID,
                "apiKey": BAIDU_OCR_API_KEY,
                "secretKey": BAIDU_OCR_SECRET_KEY,
            }
            baidu_client = AipOcr(**baidu_config)
    return baidu_client


def img_to_str_baidu(image_path, debug=False):
    """
    Call baidu ocr to convert the image to text
    demo: print(img_to_str_baidu('/tmp/5.png'))
    """
    try:
        with open(image_path, "rb") as fp:
            image = fp.read()
            if debug:
                logger.info(f"baidu ocr parse: {image_path}")
            client = get_baidu_client()
            result = client.basicGeneral(image)
            logger.debug(
                f"baidu ocr {client._appId}, {client._apiKey}, {client._secretKey}"
            )
            if "error_msg" in result:
                logger.info(f"result {result}")
            elif debug:
                logger.debug(f"result {result}")
            if "words_result" in result:
                return "\n".join([w["words"] for w in result["words_result"]])
    except Exception as e:
        print(f"convert img failed {e}")
    return ""
