"""
Manage local file cache
"""

import os
import json
import datetime
from loguru import logger
from django_cron import CronJobBase, Schedule
from django.core.cache import cache

DATA_DIR = "/tmp/"
TMPFILE_DIR = "/tmp/files/"


def get_tmpfile_dir():
    if not os.path.exists(TMPFILE_DIR):
        os.makedirs(TMPFILE_DIR)
    return TMPFILE_DIR


def set_tmpfile_dir(dir):
    global TMPFILE_DIR
    TMPFILE_DIR = dir
    if not os.path.exists(TMPFILE_DIR):
        os.makedirs(TMPFILE_DIR)


def get_tmpfile(ext):
    now = datetime.datetime.now()
    timestr = now.strftime("%Y%m%d_%H%M%S_%f")
    tmp_path = os.path.join(get_tmpfile_dir(), f"{timestr}{ext}")
    file_dir = os.path.dirname(tmp_path)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
        logger.debug(f"create dir {file_dir}")
    return tmp_path


class TmpFileManager:
    # Single Example
    _instance = None

    @staticmethod
    def get_instance():
        if TmpFileManager._instance is None:
            TmpFileManager._instance = TmpFileManager()
        return TmpFileManager._instance

    def __init__(self):
        self.last_clear_time = None
        self.file_cache = {}
        self.file_cache_path = os.path.join(DATA_DIR, "file_cache.json")
        self.load()
        self.clear()

    def __repr__(self) -> str:
        return f"<TmpFileManager {len(self.file_cache)}>"

    def load(self):
        if os.path.exists(self.file_cache_path):
            with open(self.file_cache_path, "r") as fp:
                self.file_cache = json.load(fp)

    def save(self, with_clear=True):
        with open(self.file_cache_path, "w") as fp:
            json.dump(self.file_cache, fp)
        if with_clear:
            self.clear()

    def add_file(self, path, info={}):
        now = datetime.datetime.now()
        self.file_cache[path] = {
            "info": info,
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.save()

    def get_file_info(self, path):
        if path in self.file_cache:
            return self.file_cache[path]["info"]
        return None

    def set_file_info(self, path, key, value):
        if path in self.file_cache:
            if self.file_cache[path]["info"] is None:
                self.file_cache[path]["info"] = {}
            self.file_cache[path]["info"][key] = value
            self.save()

    def get_file_by_key(self, key, value):
        for path, v in self.file_cache.items():
            if v["info"] is not None and key in v["info"] and v["info"][key] == value:
                if os.path.exists(path):
                    return path
        return None

    def clear(self):
        if (
            self.last_clear_time is None
            or (datetime.datetime.now() - self.last_clear_time).days > 1
        ):
            self.last_clear_time = datetime.datetime.now()
            logger.info("now clear file cache")
            # Convenient file caching, deletes expired files, whether they are in the cache directory or not
            now = datetime.datetime.now()
            for path in list(self.file_cache.keys()):
                if (
                    now
                    - datetime.datetime.strptime(
                        self.file_cache[path]["time"], "%Y-%m-%d %H:%M:%S"
                    )
                ).days > 1:
                    logger.debug(f"remove cache file {path}")
                    del self.file_cache[path]
                    if os.path.exists(path):
                        os.remove(path)
            self.save(False)
            # Deleting Files Not in the Cache List
            for root, dirs, files in os.walk(get_tmpfile_dir()):
                for file in files:
                    path = os.path.join(root, file)
                    if path not in self.file_cache:
                        logger.debug(f"remove loss file {path}")
                        os.remove(path)


def init(dir):
    set_tmpfile_dir(dir)
    TmpFileManager.get_instance()


class ClearCacheCronJob(CronJobBase):
    RUN_AT_TIMES = ["04:00"]  # 4:00 am

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = "backend.common.clear_cache_cron"

    def do(self):
        logger.info("cronjob clear cache")
        TmpFileManager.get_instance().clear()
