import pystardict
import re
import os
from loguru import logger
from django.utils.translation import gettext as _

current_path = os.path.dirname(os.path.abspath(__file__))
# SRC_DIR = os.path.dirname(os.path.dirname(current_path))
SRC_DIR = "/exports/"  # later move to docker inner
DICT_DIR = os.path.join(SRC_DIR, "data/stardict")


class MyDict:
    _instance = None

    def get_instance():
        if MyDict._instance is None:
            MyDict._instance = MyDict()
        return MyDict._instance

    def __init__(self):
        # self.dict_xdict = pystardict.Dictionary('/root/data/stardict/dic/stardict-xdict-ec-gb-2.4.2/xdict-ec-gb')
        path = os.path.join(DICT_DIR, "dic/stardict-lazyworm-ec-2.4.2/lazyworm-ec")
        dirname = os.path.dirname(path)
        if os.path.exists(dirname):
            self.dict_xdict = pystardict.Dictionary(path, True)
        else:
            self.dict_xdict = None
        path = os.path.join(
            DICT_DIR, "dic/stardict-oxford-gb-formated-2.4.2/oxford-gb-formated"
        )
        dirname = os.path.dirname(path)
        if os.path.exists(dirname):
            self.dict_oxford = pystardict.Dictionary(path, True)
        else:
            self.dict_oxford = None
        path = os.path.join(DICT_DIR, "dic/stardict-gcfx/gcfx5894")
        dirname = os.path.dirname(path)
        if os.path.exists(dirname):
            self.dict_gcfx = pystardict.Dictionary(path, True)
        else:
            self.dict_gcfx = None

    def en_to_ch(self, en, etc=True):
        if self.dict_xdict is None:
            logger.warning("dict_xdict is None")
            return False, en, ""
        ret = self.dict_xdict.get(en)
        if ret is None or len(ret) == 0:
            en = en.lower()
            ret = self.dict_xdict.get(en)
        if etc and ret != None and len(ret) > 30:
            ret = ret[:30] + "..."
        if ret is None or ret == "":
            return False, en, ""
        return True, en, ret

    def en_root(self, en):
        if self.dict_gcfx is None:
            logger.warning("dict_gcfx is None")
            return ""
        ret = self.dict_gcfx.get(en)
        if len(ret) > 0:
            logger.info(f"get root {en} {ret}")
            arr = ret.split("\n")
            ret = "\n".join(
                [x for x in arr if x.startswith(_("explanation_colon_")) == False]
            )
        return ret

    def sent_by_en(self, en):
        ret = []
        if self.dict_oxford is None:
            logger.warning("dict_oxford is None")
            return ret
        arr = self.dict_oxford.get(en)
        # print(arr)
        arr = arr.split("\n")
        for x in arr:
            x = re.sub("[｀`＇']", "'", x)
            if x.startswith("*"):
                x = x[1:].strip()
                x = [x for x in re.split("([\u4e00-\u9fa5]+)", x) if x != ""]
                if (
                    len(x) >= 2
                    and re.match('["a-zA-Z]', x[0]) is not None
                    and len(x[0]) > 5
                    and len(x[1]) > 5
                ):
                    en_sent = x[0]
                    zh_sent = x[1:]
                    sel_sent = []
                    for section in x[1:]:
                        if (
                            len(section) > 5
                            and re.search("[a-zA-Z]{2,}", section) is not None
                        ):
                            break
                        sel_sent.append(section)
                    zh_sent = "".join(sel_sent)
                    ret.append([en_sent, zh_sent])
        return ret
