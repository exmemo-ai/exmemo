from .base_parser import BaseParser
from .block import *
from backend.common.files import utils_file as utils_file


class TxtParser(BaseParser):
    def parse(self, data, debug=False):
        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        codec = utils_file.detect_encoding(data)
        if codec == "GB2312":
            codec = "GB18030"
        elif codec is None:
            codec = "GB18030"
        print(f"codec, {codec}")
        with open(data, "r", encoding=codec, errors="ignore") as f:
            lines = f.readlines()
            for line in lines:
                root_block.add(Block({"text": line.strip()}))
        return root_block
