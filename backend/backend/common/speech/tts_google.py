import os
from gtts import gTTS
from .tts_base import *
from loguru import logger


class TtsGoogle(TtsEngine):
    def __init__(self):
        super().__init__()

    def estimate_time(self, text, speed=1.0, wps_dic: dict = None):
        convert_time = 2
        audio_time = len(text) / 5
        return convert_time, audio_time

    def synthesize(
        self, text, output_path, speed=1.0, language=None, voice=None, debug=False
    ):
        try:
            if language == "zh" or language == "mix":
                language = "zh-CN"
            if os.path.exists(output_path):
                os.remove(output_path)
            if debug:
                logger.debug(f"text {len(text)}, {text[:20]}, language {language}")
            tts = gTTS(text, lang=language, slow=False)
            tts.save(output_path)
            regular_speed(text, output_path, output_path, speed)
            return True, _("synthesis_complete")
        except Exception as e:
            logger.warning(f"failed {e}")
            return False, e
