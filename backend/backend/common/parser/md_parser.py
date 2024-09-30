import mistune
from mistune.renderers.markdown import MarkdownRenderer
from typing import Dict, Any
from mistune.core import BlockState
from mistune.plugins.table import table
from mistune.plugins.task_lists import task_lists

# import toolpal.search.key_tools as key_tools
from .base_parser import BaseParser
from .block import *
from . import utils_md as tools_md


class MyRenderer(MarkdownRenderer):
    def __init__(self, keywords=[]):
        super().__init__()
        self.arr = []
        self.keywords = keywords

    def clear(self):
        self.arr = []

    def heading(self, token: Dict[str, Any], state: BlockState) -> str:
        # print('heading', token, state)
        # return super().heading(token, state)
        self.arr.append(
            Block(
                {
                    "type": TYPE_HEADING_BASE,
                    "text": tools_md.markdown_gettext(token),
                    "level": token["attrs"]["level"],
                },
                self.keywords,
            )
        )
        return ""

    def blank_line(self, token: Dict[str, Any], state: BlockState) -> str:
        # self.arr.append(Block({'type':'paragraph',
        #                       'text':''}))
        return ""

    def thematic_break(self, token: Dict[str, Any], state: BlockState) -> str:
        self.arr.append(
            Block({"type": TYPE_CONTENT_PARAGRAPH, "text": ""}, self.keywords)
        )
        return ""

    def paragraph(self, token: Dict[str, Any], state: BlockState) -> str:
        """
        paragraph
        """
        # print('paragraph', token, state)
        # return super().paragraph(token, state)
        self.arr.append(
            Block({"text": tools_md.markdown_gettext(token)}, self.keywords)
        )
        return ""

    def parse_list(self, token):
        for c in token["children"]:
            # print('\t', c)
            for b in c["children"]:
                if b["type"] == "block_text" or b["type"] == "paragraph":
                    # print('\t\t', tools_md.markdown_gettext(b))
                    # print("\t\t", b)
                    block = Block(
                        {
                            "type": TYPE_CONTENT_LIST_ITEM,
                            "text": tools_md.markdown_gettext(b),
                            "level": token["attrs"]["depth"],
                            "has_link": tools_md.check_link(c),
                        },
                        self.keywords,
                    )
                    # print('now add item', block)
                    self.arr.append(block)
                elif b["type"] == "list":
                    self.parse_list(b)

    def list(self, token: Dict[str, Any], state: BlockState) -> str:
        """
        Since the hierarchy information is stored in a list, it is necessary to handle the Block at this layer.
        """
        # print('list attrs', token['attrs'], token)
        # return super().list(token, state) # 需要访问子列表
        self.parse_list(token)
        return ""

    def block_text(self, token: Dict[str, Any], state: BlockState) -> str:
        """
        List item, skipped here as list has already been processed
        """
        return ""

    def table(self, token: Dict[str, Any], state: BlockState) -> str:
        # print('table', token, state)
        df = tools_md.table_from_md(token)
        self.arr.append(
            Block(
                {"type": TYPE_CONTENT_TABLE, "data": df, "text": df.to_string()},
                self.keywords,
            )
        )
        return ""

    # other blocks

    def block_code(self, token: Dict[str, Any], state: BlockState) -> str:
        # Generic Code Blocks
        self.arr.append(
            Block({"text": tools_md.markdown_gettext(token)}, self.keywords)
        )
        return ""

    def block_quote(self, token: Dict[str, Any], state: BlockState) -> str:
        # Blockquote
        self.arr.append(
            Block({"text": tools_md.markdown_gettext(token)}, self.keywords)
        )
        return ""

    def block_html(self, token: Dict[str, Any], state: BlockState) -> str:
        self.arr.append(
            Block({"text": tools_md.markdown_gettext(token)}, self.keywords)
        )
        return ""

    def block_error(self, token: Dict[str, Any], state: BlockState) -> str:
        self.arr.append(
            Block({"text": tools_md.markdown_gettext(token)}, self.keywords)
        )
        return ""


class MarkdownParser(BaseParser):
    def get_fm_item(self, keyword):
        if self.fm is not None and keyword in self.fm:
            return self.fm[keyword]
        return None

    def parse(self, data, debug=False):
        with open(data, "r", encoding="utf-8") as f:
            markdown_text = f.read()
            self.fm, body = tools_md.parse_front_matter(markdown_text, debug=debug)
        self.content = body  # for get markdown content

        # keywords = key_tools.get_keywords(lang='ALL', debug=debug)
        keywords = []
        root_block = Block(
            {"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0}, keywords
        )
        # if debug:
        #    print("body", body)
        render = MyRenderer(keywords)
        markdown = mistune.create_markdown(renderer=render, plugins=[table, task_lists])
        markdown(body)

        for idx, block in enumerate(render.arr):
            root_block.add(block)
            # print('idx', idx, 'root block len', len(root_block.blocks), 'text', block.text)

        root_block.adjust()
        if debug:
            root_block.dump()
        return root_block
