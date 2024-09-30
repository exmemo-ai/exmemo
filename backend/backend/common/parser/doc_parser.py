import subprocess
from django.utils.translation import gettext as _
from .base_parser import BaseParser
from .block import *


def convert_to_txt(path_in, path_out, debug=False):
    try:
        command = f"antiword '{path_in}' > '{path_out}'"
        subprocess.check_output(command, shell=True, text=True)
        if debug:
            print(
                _("successfully_converted_{path_in}_to_{path_out}").format(
                    path_in=path_in, path_out=path_out
                )
            )
        return True
    except Exception as e:
        print("convert failed", e)
        return False


class DOCParser(BaseParser):
    def parse(self, data, debug=False):
        path_out = "/tmp/tmp.txt"
        ret = convert_to_txt(data, path_out, debug=debug)
        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        if ret:
            with open(path_out, "r") as f:
                arr = []
                lines = f.readlines()
                for line in lines:
                    root_block.add(Block({"text": line.strip()}))
        return root_block
