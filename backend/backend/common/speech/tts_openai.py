from .tts_base import TtsEngine
from openai import OpenAI
from pathlib import Path
from loguru import logger


class TtsOpenai(TtsEngine):
    def __init__(self):
        super().__init__()
        self.client = OpenAI()

    def estimate_time(self, text, speed=1.0, wps_dic: dict = None):
        convert_time = (
            len(text) / 100
        )  # Not tested, but it won't be faster than iFlytek
        audio_time = len(text) / 5
        return convert_time, audio_time

    def synthesize(
        self, text, output_path, speed=1.0, language=None, voice=None, debug=False
    ):
        try:
            model = "tts-1"  # tts-1、tts-1-hd
            if voice is None or voice not in [
                "alloy",
                "echo",
                "fable",
                "onyx",
                "nova",
                "shimmer",
            ]:
                voice = "onyx"  # alloy、echo、fable、onyx、nova、shimmer
            response = self.client.audio.speech.create(
                model=model, voice=voice, speed=speed, input=text
            )
            path = Path(output_path)
            with open(path, "wb") as file:
                file.write(response.content)
                return True, _("synthesis_complete")
        except Exception as e:
            logger.warning(f"failed {e}")
            return False, e
