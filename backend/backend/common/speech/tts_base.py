import os
import numpy as np
import librosa
import requests
import soundfile as sf
from loguru import logger


def get_my_speech_url():
    serv_addr = os.environ.get("MY_TTS_SERV_ADDR")
    if not serv_addr or serv_addr == "":
        return None
    return f"http://{serv_addr}"


class TtsEngine:
    def __init__(self) -> None:
        self.workers = 1

    def estimate_time(
        self, text: str, speed: float = 1.0, wps_dic: dict = None
    ) -> tuple[float, float]:
        raise NotImplementedError

    def synthesize(
        self,
        text: str,
        output_path: str,
        speed: float,
        language: str = None,
        voice: str = None,
        debug: bool = False,
    ) -> tuple[bool, str]:
        raise NotImplementedError

    def get_segsize(self):
        return 500

    def multi_thread(self):
        return False


def adj_speed(path_in, path_out, speed):
    """
    demo: adj_speed("/tmp/xx_new_fast.mp3", '/tmp/ooo.mp3')
    """
    my_url = get_my_speech_url()
    if my_url is None:
        return False
    try:
        with open(path_in, "rb") as f:
            files = {"file": f}
            url = my_url + "/adj_speed"
            r = requests.post(url, files=files, data={"speed": speed})
            if r.status_code == 200:
                with open(path_out, "wb") as f:
                    f.write(r.content)
                    return True
    except Exception as e:
        logger.warning(f"failed {e}")
    return False


def regular_speed(context, in_path, out_path, speed=1.0):
    """
    Adjust the audio speed so that the length of the synthesized audio matches the length of the text.
    pangbai: 23.9s
    shenlei2: 18.5s
    xunfei faster: 18.9s
    xunfei normal: 22.9s
    Normal speaking rate: 160-200 chars/minute, about 3 chars/second, 4.75 chars/sentence
    """
    speed = float(speed)
    if speed == 1.0:
        return
    if speed > 1.0:
        logger.info(f"adjust speed {speed} by tts service")
        adj_speed(in_path, out_path, speed)
    return
    y, sr = librosa.load(in_path)
    snd_length = len(y) / sr
    str_length = len(context) / 4.75
    dst_length = str_length / speed
    delta = snd_length / dst_length
    logger.debug(f"audio_Length {snd_length} dst_length {dst_length} delta {delta}")
    if delta > 0.95 and delta < 1.05:
        logger.debug("regular_speed: do not need to adjust speed")
        return
    rate = snd_length / dst_length
    logger.info(f"regular_speed: {speed} need to adjust speed, adj rate {rate}")
    y_adj = librosa.effects.time_stretch(y, rate=rate)
    sf.write(out_path, y_adj, sr)


def merge_audio(path_list, dst_path):
    if len(path_list) == 1:
        os.rename(path_list[0], dst_path)
    else:
        y = []
        for path in path_list:
            y1, sr1 = librosa.load(path)
            y = np.concatenate((y, y1))
        print("merge_audio", dst_path)
        sf.write(dst_path, y, sr1, format="mp3")
        for path in path_list:
            os.remove(path)
