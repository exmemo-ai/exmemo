import html2text
from .base_parser import BaseParser
from .block import *
from backend.common.files import utils_file as utils_file
from loguru import logger


class HtmlParser(BaseParser):
    def parse(self, data, debug=False):
        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        # codec = utils_file.detect_encoding(data)
        codec = utils_file.detect_encoding_2(data)
        if codec == "GB2312":
            codec = "GB18030"
        elif codec is None:
            codec = "GB18030"
        if debug:
            logger.debug(f"codec, {codec}")
        with open(data, "r", encoding=codec, errors="ignore") as f:
            html_content = f.read()
            markdown_content = html2text.html2text(html_content)
            if markdown_content is not None and debug:
                logger.debug(markdown_content[:50].replace("\n", " "))
            lines = markdown_content.split("\n")
            for line in lines:
                root_block.add(Block({"text": line.strip()}))
        return root_block
