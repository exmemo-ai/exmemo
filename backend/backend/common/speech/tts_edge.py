import os
import edge_tts
from loguru import logger
from .tts_base import *


class TtsEdge(TtsEngine):
    def __init__(self):
        super().__init__()

    def estimate_time(self, text, speed=1.0, wps_dic: dict = None):
        convert_time = len(text) / 100  # 100 word per second
        audio_time = len(text) / 5
        return convert_time, audio_time

    def get_segsize(self):
        return 300

    @staticmethod
    def calc_rate(speed=1.0):
        if speed == 1.0:
            return "+0%"
        elif speed > 1.0:
            return f"+{int(speed * 100 - 100)}%"
        else:
            return f"-{int(100 - speed * 100)}%"

    def synthesize(
        self, text, output_path, speed=1.0, language=None, voice=None, debug=False
    ):
        try:
            if language == "zh" or language == "mix":
                language = "zh-CN"
            if os.path.exists(output_path):
                os.remove(output_path)
            speed_delta = self.calc_rate(speed)
            if debug:
                logger.debug(
                    f"text {len(text)}, {text[:20]}, language {language}, speed {speed_delta}"
                )
            if language == "zh-CN":
                VOICE = "zh-CN-YunxiNeural"
            else:
                VOICE = "en-GB-SoniaNeural"
            communicate = edge_tts.Communicate(text, VOICE, rate=speed_delta)
            communicate.save_sync(output_path)
            return True, _("synthesis_complete")
        except Exception as e:
            logger.warning(f"failed {e}")
            return False, e
