import os
import numpy as np
import librosa
import requests
import soundfile as sf
from loguru import logger


def get_url():
    serv_addr = os.environ.get("MY_TTS_SERV_ADDR")
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
    调整音频速度
    demo: adj_speed("/tmp/谢彦_new_fast.mp3", '/tmp/ooo.mp3')
    """
    try:
        with open(path_in, "rb") as f:
            files = {"file": f}
            url = get_url() + "/adj_speed"
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
    调整音频速度，使得合成的音频长度与文本长度相匹配
    pangbai: 23.9s
    shenlei2: 18.5s
    xunfei较快：18.9s，效果好
    xunfei正常: 22.9s
    正常语速 160-200字/分钟，约3字/秒
    这里认为正常语速是4.75字/句
    """
    speed = float(speed)
    if speed == 1.0:
        return
    if speed > 1.0:
        logger.warning(f"adjust speed {speed} by tts service")
        adj_speed(in_path, out_path, speed)
    return  # 转换后太难听，先去掉
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
    """
    合并多个音频文件
    """

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
