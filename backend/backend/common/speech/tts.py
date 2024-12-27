"""
Speech Synthesis and Backend Logic

To-Do:
* Name Mapping
* Read User Settings
* Permission Control
"""

import time
import json
import pandas as pd
import traceback
from loguru import logger
from django.utils.translation import gettext as _

import backend.common.speech.tts_tools as tts_tools
import backend.common.speech.tts_mine as tts_mine
from backend.common.user.user import *
from backend.common.user.resource import ResourceManager
from backend.common.user.models import StoreResourceUsage
from backend.common.speech.tts_base import get_my_speech_url


def tts_finished(dic):
    if dic["success"]:
        status = "success"
    else:
        status = "failed"
    ResourceManager.get_instance().add(
        dic["id"],
        "tts",
        "tts",
        dic["engine"],
        dic["content_length"],
        dic["during"],
        status,
        dic,
    )


def start_tts(title, content, uid, force_fg=False, debug=True):
    """
    Speech Synthesis
    Args:
        title: MP3 filename
        content: Synthesis content
        uid: user id
        fg: Whether to force foreground synthesis
    """
    user = UserManager.get_instance().get_user(uid)
    settings = user.settings
    privilege = user.privilege
    length = privilege.get("limit_tts_once", -1)
    limit_tts_day = privilege.get("limit_tts_day", -1)
    logger.info(f"do_tts limit length: {length} {uid}")
    if limit_tts_day > 0:
        used_tts_count = ResourceManager.get_instance().get_usage(
            uid, dtype="day", rtype="tts"
        )
        logger.info(f"used_tts_count: {used_tts_count}")
        if used_tts_count >= limit_tts_day:
            return (
                False,
                0,
                _(
                    "the_daily_limit_of_synthesized_characters_has_been_reached_{limit_tts_day}"
                ).format(limit_tts_day=limit_tts_day),
            )
        length = min(length, limit_tts_day - used_tts_count + 10)
    if content is not None:
        if length > 0 and len(content) > length:
            content = content[:length]
            logger.debug(f"length limit {len(content)}")
        conv_time, audio_time = tts_tools.estimate_time(
            content, settings, TTSResource.get_instance().get_dic()
        )
        logger.info(f"do_tts conv_time: {conv_time}")
        if conv_time > 30 and not force_fg:
            ret, info = tts_tools.do_tts(
                content,
                uid,
                settings.get_json(),
                fg=False,
                on_finished=tts_finished,
                debug=debug,
            )
            if ret:
                return (
                    ret,
                    conv_time,
                    _('the_content_is_relatively_long_{length}_characters_comma__and_it_will_take_about_{time}_minutes_to_synthesize_dot__if_you_do_not_wish_to_continue_converting_comma__please_reply_colon__stop').format(length=len(content), time=round(conv_time / 60, 1)),
                )
            else:
                return ret, 0, info
        else:
            ret, info = tts_tools.do_tts(
                content, uid, settings.get_json(), on_finished=tts_finished, debug=debug
            )
            if ret:
                return (
                    ret,
                    0,
                    {"type": "audio", "path": info, "filename": f"{title}.mp3"},
                )
            else:
                return ret, 0, info
    return False, 0, _("no_content_found")


def stop_tts(uid):
    return tts_tools.stop_tts(uid)


def get_tts_result(uid):
    return tts_tools.get_tts_result(uid)


def tts_set_engine(base_engine_setting, uid):
    """
    Set TTS engine and voice, called through wechat
    """
    engine_setting = base_engine_setting.lower()
    for key, value in VOICE_MAP.items():
        if value == base_engine_setting:
            engine_setting = key
            break

    if engine_setting in ["xunfei", "google", "openai", "edge"]:
        UserManager.get_instance().get_user(uid).set("tts_engine", engine_setting)
        return True, _("set_the_engine_to_colon__{base_engine_setting}").format(
            base_engine_setting=base_engine_setting
        )
    else:
        models = tts_mine.TtsMine().get_model_list()
        if engine_setting in models:
            UserManager.get_instance().get_user(uid).set("tts_engine", "mytts")
            UserManager.get_instance().get_user(uid).set("tts_voice", engine_setting)
            return True, _("set_engine_to_custom_colon__{base_engine_setting}").format(
                base_engine_setting=base_engine_setting
            )
    return False, _("engine_not_found_colon__{base_engine_setting}").format(
        base_engine_setting=base_engine_setting
    )


def tts_get_engine(uid):
    """
    Get TTS Engine
    """
    engine = UserManager.get_instance().get_user(uid).get("tts_engine", "xunfei")
    return engine


VOICE_MAP = {
    "edge": _("microsoft"),
    "google": _("google"),
    "xunfei": _("xunfei"),
    "openai": "OpenAI",
    "mytts": _("customization"),
    "default": _("default"),
    "caicai": _("storytelling_fairy"),
    #'caicai2': 'The little fairy who tells stories 2', # removed
    "tianly": _("book_review_master"),
    "fengjh": _("ghost_story_expert"),
    "guangbj": _("romance_novel"),
    "zhaozx": _("documentary_commentary"),
    "pangbai": _("clear_female_voice"),
    "shenlei2": _("deep_male_voice"),
    #'shenlei3': 'Male Voice Actor 1_Style 2', # Remove
    #'jiang1':'Male Voice Actor 2_Style 1',# Removed
    "jiang2": _("gentle_male_voice"),
}


def tts_get_voice_and_engine(uid, keyword):
    privilege = UserManager.get_instance().get_user(uid).privilege
    ret = []
    if privilege.b_tts:
        ret.append((VOICE_MAP["edge"], f"{keyword} {VOICE_MAP['edge']}"))
        ret.append((VOICE_MAP["xunfei"], f"{keyword} {VOICE_MAP['xunfei']}"))
        ret.append((VOICE_MAP["google"], f"{keyword} {VOICE_MAP['google']}"))
        ret.append((VOICE_MAP["openai"], f"{keyword} {VOICE_MAP['openai']}"))
        if privilege.b_tts_mine and get_my_speech_url() is not None:
            mytts_voice = tts_get_voice_list("mytts")
            for voice in mytts_voice:
                ret.append(
                    (
                        f"{VOICE_MAP['mytts']}: {VOICE_MAP[voice['value']]}",
                        f"{keyword} {VOICE_MAP[voice['value']]}",
                    )
                )

    user_engine = UserManager.get_instance().get_user(uid).get("tts_engine")
    user_voice = UserManager.get_instance().get_user(uid).get("tts_voice")
    ret_new = []
    for item in ret:
        if item[0] == VOICE_MAP[user_engine] or (
            user_engine == "mytts" and VOICE_MAP[user_voice] in item[0]
        ):
            item = (f"{item[0]} *", item[1])
        ret_new.append(item)
    return ret_new


def tts_get_voice_list(engine="mytts"):
    """
    Get the list of currently supported TTS voices
    """
    logger.info(f"tts_get_voice_list {engine}")
    ret = ["default"]
    if engine == "mytts":
        ret = tts_mine.TtsMine().get_model_list()
    return [{"label": VOICE_MAP.get(x, x), "value": x} for x in ret if x in VOICE_MAP]


def tts_get_engine_list(uid):
    """
    Get TTS engine list
    """
    privilege = UserManager.get_instance().get_user(uid).privilege
    ret = []
    if privilege.b_tts:
        ret.append({"label": _("xunfei"), "value": "xunfei"})
        ret.append({"label": _("microsoft"), "value": "edge"})
        ret.append({"label": _("google"), "value": "google"})
        ret.append({"label": "OpenAI", "value": "openai"})
        if privilege.b_tts_mine and get_my_speech_url() is not None:
            ret.append({"label": _("customization"), "value": "mytts"})
    return ret


def run_tts(title, content, uid, fg=False, debug=True):
    ret, delay, detail = start_tts(title, content, uid, debug=debug)
    if ret:
        dic = {"type": "text"}
        if isinstance(detail, dict):
            dic["type"] = detail["type"]
            dic["path"] = detail["path"]
            dic["filename"] = detail["filename"]
            return dic
        else:
            if delay > 0:
                dic["request_delay"] = delay
            dic["content"] = detail
        return dic
    else:
        return detail


class TTSResource:
    """
    Write a class to collect statistics on TTS resource usage
    """

    _instance = None

    @staticmethod
    def get_instance():
        if TTSResource._instance is None:
            TTSResource._instance = TTSResource()
        return TTSResource._instance

    def __init__(self) -> None:
        self.dic = {1: 10, 2: 13, 3: 16}
        self.last_updated = 0

    @staticmethod
    def parse_workers(info):
        try:
            d = dict(json.loads(info))
            if "workers" in d:
                return int(d["workers"])
        except Exception as e:
            print(info, e)
        return 2

    def calc_wps(self):
        """
        Calculate the synthesis time for each character
        """
        # Minimum hourly updates
        if time.time() - self.last_updated < 3600:
            return
        self.last_updated = time.time()
        # Retrieve up to 100 records
        try:
            data = StoreResourceUsage.objects.filter(method="mytts").order_by(
                "-updated_time"
            )[:100]
            df = pd.DataFrame(list(data.values()))
            if not df.empty:
                df["workers"] = df["info"].apply(lambda x: TTSResource.parse_workers(x))
                df["wps"] = df["amount"] / df["during"]
                df = df[df["amount"] > 100]  # Remove too short
                grp = df.groupby("workers")
                for name, group in grp:
                    self.dic[name] = round(group["wps"].median(), 2)
        except Exception as e:
            traceback.print_exc()
            logger.warning(f"calc_wps error {e}")
        logger.info(f"real calc_wps {self.dic}")

    def get_wps(self, workers):
        self.calc_wps()
        return self.dic.get(workers, 10)

    def get_dic(self):
        self.calc_wps()
        return self.dic
