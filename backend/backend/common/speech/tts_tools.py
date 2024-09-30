import time
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from django.utils.translation import gettext as _
from backend.common.files import utils_file
from backend.common.files import filecache

from .tts_xunfei import TtsXunfei
from .tts_mine import TtsMine
from .tts_google import TtsGoogle
from .tts_openai import TtsOpenai
from .tts_edge import TtsEdge
from .tts_base import *

MAX_TASKS = 5

g_engine_dic = {}


# parameter specifies whether it is a single instance
def get_engine(engine_name, single=False):
    if single:
        global g_engine_dic
        if engine_name in g_engine_dic:
            return g_engine_dic[engine_name]
        if engine_name == "google":
            g_engine_dic[engine_name] = TtsGoogle()
        elif engine_name == "openai":
            g_engine_dic[engine_name] = TtsOpenai()
        elif engine_name == "edge":
            g_engine_dic[engine_name] = TtsEdge()
        elif engine_name == "xunfei":
            g_engine_dic[engine_name] = TtsXunfei()
        else:
            g_engine_dic[engine_name] = TtsMine()
        return g_engine_dic[engine_name]
    else:
        if engine_name == "google":
            return TtsGoogle()
        elif engine_name == "openai":
            return TtsOpenai()
        elif engine_name == "edge":
            return TtsEdge()
        elif engine_name == "xunfei":
            return TtsXunfei()
        else:
            return TtsMine()


class SegTools:
    @staticmethod
    def segment(content, segsize):
        """
        Split the content by punctuation, with a maximum length of segsize
        """
        content = re.sub(r"[\n]+", "\n", content)
        content = re.sub(r"[“”‘’]", '"', content)
        content = re.sub(r"[……]+", "...", content)
        segs = []
        seg = ""
        arr = re.findall(
            r"[^。！？.；;\n]+[。！？.;；\n]?", content
        )  # Split into sentences
        for c in arr:
            if len(seg) + len(c) >= segsize:
                if len(seg) > 0:
                    segs.append(seg)
                    seg = ""
            seg += c
        segs.append(seg)
        return segs

    @staticmethod
    def strip_line(content):
        """
        Remove the punctuation and spaces from the beginning and end of the content
        """
        content = content.strip()
        # If content does not end with punctuation, add punctuation.
        if len(content) > 0 and content[-1] not in '，。！？,.!?……;；"':
            content += "。"
        # Remove those starting with punctuation or spaces
        while len(content) > 0 and (
            content[0] in "，。！？,.!?……；;-—" or content[0].isspace()
        ):
            content = content[1:]
        content = content.replace("\n", "")
        content = content.replace("\r", "")
        # Space between Chinese and English
        content = re.sub(r"([a-zA-Z0-9])([\u4e00-\u9fa5])", r"\1 \2", content)
        content = re.sub(r"([\u4e00-\u9fa5])([a-zA-Z0-9])", r"\1 \2", content)
        # Remove extra spaces
        content = re.sub(r"[\s]+", " ", content)
        return content

    @staticmethod
    def text_filter(string, dtype, debug=False):
        """
        Filter the string, only keeping the content of dtype type; translation uses mix, so it won't be tested for now
        """
        if string is None or len(string.strip()) == 0:
            return ""
        if dtype == "mix":
            return string
        ret = []
        lines = string.split("\n")
        lines = [line.strip() for line in lines if line.strip() != ""]
        for idx, line in enumerate(lines):
            line_type = utils_file.check_language(line, debug=debug)
            if debug:
                logger.debug(f"filter {idx}, {line_type}, {dtype}, {line}")
            if dtype == "en" and (line_type == "en" or line_type == "mix"):
                ret.append(line)
            elif dtype == "zh" and (line_type == "zh" or line_type == "mix"):
                ret.append(line)
        return "\n".join(ret)

    @staticmethod
    def do_seg(content, segsize, language="mix", log_file="/tmp/seg.log"):
        segs = SegTools.segment(content, segsize)
        ret = []
        for seg in segs:
            seg = SegTools.text_filter(seg, language)
            seg = SegTools.strip_line(seg)
            if len(seg) == 0:
                continue
            ret.append(seg)

        if log_file is not None:
            with open(log_file, "w", encoding="utf-8") as fp:
                for idx, x in enumerate(ret):
                    fp.write(f"{idx} {x} \n")
                fp.close()
        return ret


def get_audio_path(user_id):
    return os.path.join(filecache.get_tmpfile_dir(), f"{user_id}.mp3")


def regular_volume(path_in, path_out, m_base=0.065, max=0.8, debug=True):
    """
    Adjust the volume of the audio file to the reference volume
    Args:
        m_base: Reference volume, 0.065 as calculated from iFlytek TTS
        max: Maximum volume, beyond which clipping occurs
    demo:
        regular_volume('/tmp/test_nan1.mp3', '/tmp/test_new.mp3', debug=False)
    """
    audio_data, sample_rate = librosa.load(path_in)
    volume = np.abs(audio_data[: 10 * sample_rate])  # Only take the first 10 seconds
    base_length = len(volume)
    if debug:
        print("length", round(len(volume) / sample_rate, 1), "frame", len(volume))
        print(
            "median",
            round(np.percentile(volume, 50), 3),
            "mean",
            round(np.mean(volume), 3),
        )
    # Remove parts where the volume is less than 10%
    volume = volume[volume > np.percentile(volume, 10)]
    if debug:
        print(
            "remove empty by 10 percentile，frame, remains",
            round(len(volume) / base_length, 3),
        )
        print(
            "median",
            round(np.percentile(volume, 50), 3),
            "mean",
            round(np.mean(volume), 3),
        )
    m_current = np.mean(volume)

    # No need to align perfectly, retain some of the previous style
    scale_base = round(m_base / m_current, 3)
    scale = round(1 + (scale_base - 1) * 0.8, 3)
    if debug:
        print("scale", scale_base, "->", scale)

    audio_data_adj = audio_data * scale
    audio_data_adj = np.clip(audio_data_adj, -max, max)
    if debug:
        print("after adj, max", np.max(audio_data_adj))
        print(
            "clip percent",
            round(len(audio_data_adj[audio_data_adj > max]) / len(audio_data_adj), 5),
        )
    sf.write(path_out, audio_data_adj, sample_rate)


class TtsTask:
    def __init__(self, content, user_id, settings, on_finished=None):
        self.content = content
        self.user_id = user_id
        self.on_finished = on_finished
        self.save_path = get_audio_path(user_id)
        self.options = settings
        self.engine = get_engine(self.options["tts_engine"], single=True)
        self.tts_language = self.options.get("tts_language", "mix")
        self.status = "waiting"
        self.list = []

    def run(self):
        start_time = time.time()
        self.status = "running"
        segsize = self.engine.get_segsize()
        contents = SegTools.do_seg(self.content, segsize, language=self.tts_language)
        logger.info(f"seg total: { len(contents)}")
        args = []
        path_list = []
        self.list = []
        if os.path.exists(self.save_path):
            os.remove(self.save_path)
        for idx, content in enumerate(contents):
            path = self.save_path.replace(".mp3", "") + "_{:04}.mp3".format(idx + 1)
            self.list.append(path)
            dic = {"content": content, "path": path}
            dic.update(self.options)
            args.append(dic)

        logger.info(f"multi_thread: {self.engine.multi_thread()}")
        if self.engine.multi_thread():
            rets = self.start_tasks(args, self.engine.workers)
            for idx, (ret, tmp_path) in enumerate(rets):
                # logger.debug(f'multi_thread {idx} {ret} {tmp_path}')
                if ret:
                    path_list.append(tmp_path)
                else:
                    logger.warning(f"multi_thread failed {idx} {tmp_path}")
                    # self.status = 'failed' # Some only have one symbol, synthesis failed, can be ignored
                    # break
        else:
            for idx, item in enumerate(args):
                ret, tmp_path = self.task(item)
                if ret:
                    path_list.append(tmp_path)
                else:
                    logger.warning(f"failed {idx} {tmp_path}")
                    # self.status = 'failed'
                    # break

        ret = False
        logger.debug(f"self.status {self.status} {self.save_path}")
        if self.status == "running":
            path_list = [x for x in path_list if os.path.exists(x)]
            if len(path_list) > 0:
                path_list = sorted(path_list)
                logger.debug(f"path_list {len(path_list)} {path_list}")
                merge_audio(path_list, self.save_path)
                if self.options["tts_engine"] == "mytts":
                    logger.info(f"regular_volume {self.options['tts_engine']}")
                    regular_volume(self.save_path, self.save_path)
                ret = True
            else:
                self.status = "empty"

        for path in path_list:  # Delete temporary files on error
            if os.path.exists(path):
                os.remove(path)

        end_time = time.time()
        logger.info(f"tts, {len(self.content)} cost {end_time-start_time:.2f}s")
        self.status = "finished"
        if self.on_finished is not None:
            self.on_finished(
                {
                    "id": self.user_id,
                    "success": ret,
                    "workers": self.engine.workers,
                    "during": (end_time - start_time),
                    "path": self.save_path,
                    "engine": self.options["tts_engine"],
                    "content_length": len(self.content),
                }
            )
        if ret:
            return ret, _("assembled")
        else:
            if self.options["tts_engine"] == "mytts":
                return ret, _("custom_synthesis_failed")
            else:
                return ret, _("synthesis_failed")

    def get_percent(self):
        count = 0
        for idx, path in enumerate(self.list):
            if os.path.exists(path):
                count += 1
        if len(self.list) == 0:
            return 0
        percent = round(count / len(self.list), 3)
        logger.info(f"task percent {percent}")
        return percent

    def stop(self):
        self.status = "stopped"

    def task(self, dic):
        if self.status != "running":
            return False, dic["path"]
        ret, detail = self.engine.synthesize(
            dic["content"],
            dic["path"],
            voice=dic["tts_voice"],
            speed=float(dic["tts_speed"]),
            language=dic["tts_language"],
        )
        logger.debug(f"ret {ret}, {detail}, {dic['path']}")
        return ret, dic["path"]

    def start_tasks(self, data, max_workers):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            rets = executor.map(self.task, data)
        # Waiting for all tasks to be completed
        logger.debug("All tasks done")
        return rets


def test_TtsTask():
    string = """
    He never paid attention to it. Of course, more crucially, no one had ever emphasized "love" to him.
    Therefore, although Ning Yi had experienced hardships and gains that many people wouldn't encounter in several lifetimes, he still didn't know how to love himself, nor how to receive love, let alone express it. He would put
    """
    TtsTask(string, "user_id").run()


class TtsManager:
    """
    If no threads are running and new tasks arrive, start a thread. After the thread completes, set the thread to null.
    """

    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(TtsManager, "_instance"):
            with TtsManager._instance_lock:
                if not hasattr(TtsManager, "_instance"):
                    TtsManager._instance = object.__new__(cls)
        return TtsManager._instance

    def __init__(self, debug=True):
        self.debug = debug
        if not hasattr(self, "tasks"):
            self.tasks = []
            self.thread = None
            if self.debug:
                print("TtsManager init tasks")

    def add_task(self, content, user_id, settings, on_finished=None):
        logger.debug(f"before add task, tasks {len(self.tasks)}")
        for task in self.tasks:
            logger.info(f"check task {task.user_id}, {user_id}, {task.status}")
            if task.user_id == user_id:
                return False, _("the_current_user_already_has_a_task_in_progress")
        if len(self.tasks) >= MAX_TASKS:
            return False, _("the_current_task_list_is_full_comma__please_try_again_later")
        self.tasks.append(TtsTask(content, user_id, settings, on_finished))
        # If no threads are running, start a thread
        if len(self.tasks) > 0 and (self.thread is None or not self.thread.is_alive()):
            self.thread = threading.Thread(target=self.run_tasks)
            self.thread.start()
        logger.debug("after add task")
        return True, _("the_task_has_been_added__excl_")

    def remove_task(self, user_id):
        for task in self.tasks:
            if task.user_id == user_id:
                if task.status == "running":
                    task.stop()
                self.tasks.remove(task)
                return True, _("task_removed")
        return False, _("quest_does_not_exist")

    def get_task_status(self, user_id):
        for task in self.tasks:
            if task.user_id == user_id:
                return True, task.status
        return False, _("quest_does_not_exist")

    def run_tasks(self):
        while len(self.tasks) > 0:
            for idx, task in enumerate(self.tasks):
                logger.debug(f"in run_tasks {idx} {task.status}")
                if task.status == "waiting":
                    task.run()  # block; hold up
            self.tasks = [
                task for task in self.tasks if task.status in ["waiting", "running"]
            ]
            print("run tasks:", len(self.tasks))

    def join(self):
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()
            print("after join thread")

    def __del__(self):
        self.join()


def test_TtsManager():
    tm = TtsManager(debug=True)
    tm.add_task("xxxx", "user1")
    tm.join()
    # TtsManager(debug=True).tasks
    # tm.start_thread()


def estimate_time(content, settings, wps_dic):
    if settings is None:
        return -1, -1
    speed = settings.get("tts_speed", 1.0)
    engine_name = settings.get("tts_engine", "xunfei")
    return get_engine(engine_name).estimate_time(content, speed, wps_dic)


def do_tts(content, user_id, settings, fg=True, on_finished=None, debug=False):
    """
    Speech Synthesis
    Args:
        content: Content
        user_id: User ID
        setting: User Setting
        fg: Foreground Synthesis
    """
    # logger.warning(f"do_tts {content[:10]} {user_id} {settings}")
    if fg:
        task = TtsTask(content, user_id, settings, on_finished=on_finished)
        ret, status = task.run()
        if ret:
            return True, task.save_path
        else:
            return False, status
    else:
        tm = TtsManager(debug=True)
        return tm.add_task(content, user_id, settings, on_finished=on_finished)


def stop_tts(user_id):
    return TtsManager().remove_task(user_id)


def get_tts_result(user_id):
    ret, status = TtsManager().get_task_status(user_id)
    logger.info(f"get_tts_result {ret} {status}")
    if ret:
        if status == "waiting":
            prev_task_n = 0
            for task in TtsManager().tasks:
                if task.user_id == user_id:
                    break
                prev_task_n += 1
            return (
                False,
                60,
                _("in_the_queue_comma__there_are_still_{prev_task_n}_tasks_ahead").format(
                    prev_task_n=prev_task_n
                ),
            )
        if status == "running":
            percent = 0
            for task in TtsManager().tasks:
                if task.user_id == user_id:
                    percent = task.get_percent()
            return (
                False,
                15,
                _("currently_synthesizing_comma__{_colon__dot_1%}_completed").format(percent),
            )
    path = get_audio_path(user_id)
    logger.debug(f"get_tts_result path {path}")
    if os.path.exists(path):
        return True, -1, path
    else:
        return False, -1, _("no_synthesized_audio_found")
