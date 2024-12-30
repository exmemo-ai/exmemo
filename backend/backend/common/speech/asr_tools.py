import os
import requests
import librosa
from openai import OpenAI
from loguru import logger
from backend.common.speech.tts_base import get_my_speech_url
from django.utils.translation import gettext as _


def get_audio_duration(path):
    """
    Calculate the duration of an audio file
    """
    try:
        y, sr = librosa.load(path)
        duration = librosa.get_duration(y=y, sr=sr)
        return duration
    except Exception as e:
        logger.warning(f"get_audio_duration failed {e}")
    return -1


def asr_whisper(path_in):
    """
    $0.006 / minute
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        audio_file = open(path_in, "rb")
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        return True, transcript.text
    except Exception as e:
        return False, str(e)


def asr_mine(path_in):
    my_url = get_my_speech_url()
    if my_url is None:
        return False, _("recognition_failure")
    try:
        with open(path_in, "rb") as f:
            files = {"file": f}
            url = f"{my_url}/asr"
            # url = 'http://192.168.10.168:9880/asr' # local test
            print("c", url)
            r = requests.post(url, files=files)
            if r.status_code == 200:
                # logger.info(r.json())
                if "code" in r.json() and r.json()["code"] == 0:
                    return True, r.json()["text"]
    except Exception as e:
        logger.warning(f"failed {e}")
    return False, _("recognition_failure")


def do_asr(path_in, path_out, engine="auto", debug=True):
    """
    For speech recognition, use the whisper-1 model for audio shorter than 20 seconds, otherwise use our own model.
    """
    if engine == "auto":
        duration = get_audio_duration(path_in)
        logger.info(f"duration {duration}")
        if duration <= 30 and duration != -1:
            engine = "whisper"
        else:
            engine = "mine"
    if engine == "whisper":
        logger.info("asr by whisper-1")
        ret, text = asr_whisper(path_in)
    else:
        logger.info("asr by mine")
        ret, text = asr_mine(path_in)
    if ret:
        with open(path_out, "w") as f:
            f.write(text)
        return True, _("asr_successful")
    else:
        return False, text
