import os
from aip import AipOcr
from loguru import logger


class BaiduOcr:
    def __init__(self, app_id=None, api_key=None, secret_key=None):
        self.app_id = app_id or os.getenv("BAIDU_OCR_APPID", "")
        self.api_key = api_key or os.getenv("BAIDU_OCR_API_KEY", "")
        self.secret_key = secret_key or os.getenv("BAIDU_OCR_SECRET_KEY", "")
        self.client = None
        
    def get_client(self, force=False):
        if force or self.client is None:
            if self.app_id and self.api_key and self.secret_key:
                baidu_config = {
                    "appId": self.app_id,
                    "apiKey": self.api_key,
                    "secretKey": self.secret_key,
                }
                self.client = AipOcr(**baidu_config)
        return self.client
    
    def img_to_str(self, image_path, debug=False):
        """
        Call baidu ocr to convert the image to text
        demo: print(baidu_ocr.img_to_str('/tmp/5.png'))
        """
        try:
            with open(image_path, "rb") as fp:
                image = fp.read()
                if debug:
                    logger.info(f"baidu ocr parse: {image_path}")
                client = self.get_client()
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


# 保持与原有代码的兼容性
baidu_client = None
_default_ocr = BaiduOcr()

def get_baidu_client(force=False):
    global baidu_client
    return _default_ocr.get_client(force)

def img_to_str_baidu(image_path, app_id=None, api_key=None, secret_key=None, debug=False):
    """
    Call baidu ocr to convert the image to text
    demo: print(img_to_str_baidu('/tmp/5.png'))    
    """
    if (app_id and app_id.strip()) or (api_key and api_key.strip()) or (secret_key and secret_key.strip()):
        temp_ocr = BaiduOcr(app_id, api_key, secret_key)
        return temp_ocr.img_to_str(image_path, debug)
    else:
        return _default_ocr.img_to_str(image_path, debug)
