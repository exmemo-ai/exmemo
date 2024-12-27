import time
import requests
import librosa
import soundfile as sf
import traceback
from loguru import logger
from django.utils.translation import gettext as _
from .tts_base import *

WAV_FILE = "/tmp/output.wav"


class TtsMine(TtsEngine):
    def __init__(self):
        super().__init__()
        self.last_status_time = 0
        self.models = []
        self.get_tts_status()

    def estimate_time(self, text, speed=1.0, wps_dic: dict = None):
        """
        Estimate Synthesis Time and Audio Time
        """
        self.get_tts_status()
        if wps_dic is None:
            if self.workers == 3:
                scale = 0.6
            elif self.workers == 2:
                scale = 0.8
            else:
                scale = 1
            convert_time = int(len(text) / 10 * scale)
        else:
            if self.workers in wps_dic:
                wps = wps_dic[self.workers]
            else:
                wps = 10
            convert_time = int(len(text) / wps)
            logger.debug(
                f"estimate_time wps is {wps}, workers is {self.workers}, convert_time is {convert_time}"
            )
        audio_time = len(text) / 5
        return convert_time, audio_time

    def get_segsize(self):
        return 50

    def multi_thread(self):
        return True

    def synthesize(
        self, text, output_path, speed=1.0, language=None, voice=None, debug=False
    ):
        my_url = get_my_speech_url()
        if my_url is None:
            return False, _("custom_synthesis_failed")
        if debug:
            logger.debug(f"tts {text} to {output_path} at {my_url}")
        data = {
            "prompt_language": "zh",
            "text": text,
            "text_language": "zh",
            "speed": speed,
        }
        if voice is not None:
            data["model_name"] = voice
        try:
            r = requests.post(my_url, json=data)
            if debug:
                logger.debug(f"code return {r.status_code}")
            if r.status_code != 200:
                logger.warning(f"code return {r.status_code}")
                return False, r.text
            with open(WAV_FILE, "wb") as f:
                f.write(r.content)
                y, sr = librosa.load(WAV_FILE)
                if debug:
                    logger.debug(f"save to {output_path}")
                sf.write(output_path, y, sr)
        except Exception as e:
            traceback.print_exc()
            return False, _("custom_synthesis_failed")
        return True, _("synthesis_complete")

    def get_tts_status(self, force=False):
        """
        Get Synthesis Service Status
        """
        my_url = get_my_speech_url()
        if my_url is None:
            return False
        try:
            if (
                not force and time.time() - self.last_status_time < 60 * 60
            ):  # Updated every hour
                return True
            self.models = []
            self.last_status_time = time.time()
            logger.info("real get_tts_status")
            url = my_url + "/get_status"
            r = requests.post(url)
            if r.status_code != 200:
                logger.warning(f"get_tts_status failed {r.text}")
                return False
            jdata = r.json()
            self.workers = int(jdata["workers"])

            if "model_list" in jdata:
                models = jdata["model_list"]
                if models is not None and len(models) > 0:
                    self.models = models.split(",")
            return True
        except Exception as e:
            logger.warning(f"get_tts_status error {e}, url {url}")
        return False

    def get_model_list(self):
        self.get_tts_status()
        return self.models
