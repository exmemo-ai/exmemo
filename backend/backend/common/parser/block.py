import pandas as pd
import traceback
from django.utils.translation import gettext as _
from . import utils_md as tools_md
from . import utils_text as utils_text

# Define the types and sort them by priority

BLOCK_ROOT = "Root"
BLOCK_CONTENT = "Content"

TYPE_HEADING_BASE = "heading"
TYPE_HEADING_KEYWORD = "inner_heading_keyword"
TYPE_HEADING_TOP_LEVEL = "top_level_heading"
TYPE_HEADING_TOC = "toc"
TYPE_HEADING_NUM = "inner_heading_base"
TYPE_CONTENT_LIST_ITEM = "list_item"
TYPE_CONTENT_NUM_ITEM = "num_item"

TYPE_CONTENT_PARAGRAPH = "paragraph"
TYPE_CONTENT_TABLE = "table"
TYPE_CONTENT_TOC_ITEM = "toc_item"

HEADING_TYPE = [
    TYPE_HEADING_BASE,
    TYPE_HEADING_TOP_LEVEL,
    TYPE_HEADING_TOC,
    TYPE_HEADING_NUM,
    TYPE_HEADING_KEYWORD,
]
CONTENT_TYPE = [
    TYPE_CONTENT_LIST_ITEM,
    TYPE_CONTENT_NUM_ITEM,
    TYPE_CONTENT_PARAGRAPH,
    TYPE_CONTENT_TABLE,
    TYPE_CONTENT_TOC_ITEM,
]
BLOCK_TYPE = HEADING_TYPE + CONTENT_TYPE

TYPE_LEVEL = {
    TYPE_HEADING_BASE: 0,
    TYPE_HEADING_TOP_LEVEL: 0,
    TYPE_HEADING_TOC: 0,
    TYPE_HEADING_NUM: 1,
    TYPE_HEADING_KEYWORD: 2,
    TYPE_CONTENT_NUM_ITEM: 1,
    TYPE_CONTENT_LIST_ITEM: 1,  # xieyan 231108
    TYPE_CONTENT_PARAGRAPH: 4,
    TYPE_CONTENT_TABLE: 4,
    TYPE_CONTENT_TOC_ITEM: 4,
}


class Block:
    def __init__(self, data, keywords=[]):
        self.children = []  # all sub-blocks
        self.current_child = None  # blocks of the current operation
        self.idx = -1
        self.match_toc = -1
        self.data = data
        self.heading_text = None
        if "type" in data:
            self.type = data["type"]
        else:
            self.type = TYPE_CONTENT_PARAGRAPH
        if "text" in data:
            self.text = data["text"]
        else:
            self.text = None
        if "data" in data:
            self.data = data["data"]
        else:
            self.data = None
        if "level" in data:
            self.level = data["level"]
        else:
            self.level = -1
        if "has_link" in data:
            self.has_link = data["has_link"]
        else:
            self.has_link = False
        if "idx" in data:
            self.idx = data["idx"]
        else:
            self.idx = -1
        if "style" in data:
            self.style = data["style"]
        else:
            self.style = utils_text.STYLE_NONE  # Styles for Inner Headings
        if "restrict" in data:
            self.restrict = data["restrict"]
        else:
            self.restrict = False  # For unformatted documents such as doc, title checks need to be strictly enforced
        if self.type == TYPE_CONTENT_PARAGRAPH:
            if (
                "auto_detect" in data and data["auto_detect"] == True
            ) or "auto_detect" not in data:
                if self.restrict:
                    ret, string, style = utils_text.is_base_title(self.text)
                else:
                    ret, string, style = utils_text.is_base_title(
                        self.text, max_length=-1
                    )
                if ret:
                    # print("????", ret, self.text)
                    self.type = TYPE_HEADING_NUM
                    if self.style == utils_text.STYLE_NONE:
                        self.style = style
                    self.idx = utils_text.get_number_str(string)
            if (
                self.type == TYPE_CONTENT_PARAGRAPH and keywords is not None
            ):  # Did not automatically recognize the title, using keywords to identify again
                ret = utils_text.is_keyword_title(self.text, keywords)
                if ret:
                    self.type = TYPE_HEADING_KEYWORD
                    self.style = utils_text.STYLE_KEYWORD
                # print(TYPE_CONTENT_PARAGRAPH, ret, string, style, self.text)
            self.check_top_level()
            if (
                self.text.replace(" ", "") == _("table_of_contents")
                or self.text.lower() == "Table of Contents".lower()
            ):
                self.type = TYPE_HEADING_TOC
        elif self.type in HEADING_TYPE:
            self.check_top_level()
            if (
                self.text.replace(" ", "") == _("table_of_contents")
                or self.text.lower() == "Table of Contents".lower()
            ):
                self.type = TYPE_HEADING_TOC
        if pd.isna(self.text):
            self.text = ""

    def get_heading(self):
        """
        This function mainly supports searching for titles; if there are no child items, it is not considered a title.
        """
        if self.is_heading():
            if self.heading_text is not None:
                return self.heading_text
            return self.text
        else:
            return ""

    def get_text(self):
        ret = []
        if self.is_heading():
            text = self.get_heading()
            if text != BLOCK_CONTENT and text != BLOCK_ROOT:
                ret.append(text)
        else:
            ret.append(self.text)
        for b in self.children:
            ret.append(b.get_text())
        return "\n".join(ret)

    def get_level(self):
        # Get priority, the smaller the number, the higher the heading level
        return TYPE_LEVEL[self.type] * 100 + self.level

    def __repr__(self):
        # return str(self.data)
        return f"Block(type:{self.type}, has {len(self.children)} blks, text:{self.text[:30]}, level:{self.level}, idx:{self.idx}, style:{self.style}, link:{self.has_link}), toc:{self.match_toc}"

    def __str__(self) -> str:
        return self.__repr__()

    def check_top_level(self):
        """
        Determine whether it is the first level topic, including table of contents/appendix, etc.
        """
        if self.type == TYPE_HEADING_TOC:
            return True
        # keywords_start = ['Appendix', 'Annex', 'Preface', 'Whereas:', 'Recitals:', 'Abstract']
        keywords_start = [
            _("appendices"),
            _("attachment"),
            _("foreword"),
            _("given_that_colon_"),
            _("in_view_of_the_terms_colon_"),
        ]
        for keyword in keywords_start:
            if self.text.lower().startswith(keyword.lower()) and not self.has_link:
                self.type = TYPE_HEADING_TOP_LEVEL
                return True
        keywords_in = [_("(no_text)"), _("signing_page"), _("page_for_signing")]
        for keyword in keywords_in:
            if (
                self.text.find(keyword) != -1
                and len(self.text) <= utils_text.MAX_TOP_KEYWORD_HEADING_LEN
            ):
                self.type = TYPE_HEADING_TOP_LEVEL
                return True
        return False

    def add_to_same_level(self, block):
        # Flattened Headings
        self.current_child = block
        self.children.append(self.current_child)

    def add_content(self, block):
        # Add Body
        if block.is_heading() or self.text != BLOCK_ROOT:
            self.add_to_same_level(block)
        else:  # Table of Contents
            content = Block(
                {"text": BLOCK_CONTENT, "type": TYPE_HEADING_BASE, "level": 1}
            )
            self.add_to_same_level(content)
            content.add_to_same_level(block)

    def add(self, block, debug=False):
        # if block.match_toc != -1:
        #    print('@@@@@@@@@@@@@@@@@@@@@@@@@@', block)
        if debug:
            print(f"add {block} current_child {self.current_child}")
        if self.current_child is None:
            if debug:
                print("  cur_blk none, add", block)
            self.add_content(block)
        elif self.current_child.type == TYPE_HEADING_TOC:  # If in the directory
            if debug:
                print("  in toc, cur_blk", self.current_child, "add", block)
            if (
                block.has_link
                or block.type == TYPE_HEADING_TOP_LEVEL
                or block.type == TYPE_CONTENT_TOC_ITEM
            ):
                block.type = TYPE_CONTENT_TOC_ITEM
                self.current_child.add(block)
            else:
                self.add_content(block)
        elif (
            block.type == TYPE_HEADING_BASE and block.level == 1
        ):  # If it's the first-level title, add it to the first level
            if debug:
                print("  in top base level, cur_blk", self.current_child, "add", block)
            self.add_to_same_level(block)
        elif (
            block.match_toc == 1
        ):  # If in the first level of the directory, then add to the first level
            # if debug:
            if True:  # for test
                print("  match_toc, cur_blk", self.current_child, "add", block)
            self.add_to_same_level(block)
        elif (
            block.type == TYPE_HEADING_TOP_LEVEL
        ):  # If it is the first-level topic such as an appendix, add it to the first level
            if debug:
                print("  in top level, cur_blk", self.current_child, "add", block)
            self.add_to_same_level(block)
        elif self.is_same_level(self.current_child, block):
            if debug:
                print("  in same_level, cur_blk", self.current_child, "add", block)
            self.add_to_same_level(block)
        elif (
            self.current_child.is_heading()
        ):  # If the current block is a title, add a subtitle
            # print("????", 'type', self.text[:20], self.type, 'add inner', block)
            # Add subtitle
            if debug:
                print("    add inner, add", block)
            self.current_child.add(block)
        else:
            # Adding Content to This Layer
            if debug:
                print("    add same level, add", block)
            self.add_to_same_level(block)

    def has_children(self):
        if len(self.children) == 0:
            return False
        text = ""
        for child in self.children:
            text += child.get_text()
        text = text.strip()
        if len(text) == 0:
            return False
        return True

    def is_heading(self, check_children=False):
        """
        Determine if current block is a heading: any form of heading
        """
        if check_children and not self.has_children():
            return False
        # if self.type in HEADING_TYPE and len(self.text) <= utils_text.MAX_BASE_HEADING_LEN:
        if self.type in HEADING_TYPE:  # xieyan 231103
            return True
        if self.type == TYPE_CONTENT_NUM_ITEM or self.type == TYPE_CONTENT_LIST_ITEM:
            return True
        return False

    def is_same_level(self, block1, block2):
        try:
            # print(block1, block2)
            if TYPE_LEVEL[block1.type] < TYPE_LEVEL[block2.type]:
                # print("return 1")
                return False  # Title Down
            elif TYPE_LEVEL[block1.type] == TYPE_LEVEL[block2.type]:
                # Peers
                if block1.level < block2.level:
                    # Lines are bigger
                    # print("return 2")
                    return False
                elif block1.level == block2.level:
                    # print("now compare", block1, block2)
                    compare = utils_text.compare_number_str(block2.idx, block1.idx)
                    if (
                        block1.style == block2.style
                        and compare is not None
                        and compare >= 0
                    ):
                        # print('ret true', block1.style, block2.style, compare)
                        return True
                    else:
                        # print('ret false')
                        return False
                else:
                    # print("return 4")
                    return True
            else:
                # print("return 5")
                return True
        except Exception as e:
            print(e)
            import traceback

            traceback.print_exc()

    def dump_toc(self):
        for b in self.children:
            if b.type == TYPE_HEADING_TOC or b.type == TYPE_CONTENT_TOC_ITEM:
                print(
                    "  " * b.level,
                    b.text[:30],
                    b.type,
                    "level",
                    b.level,
                    "children",
                    len(self.children),
                )
                b.dump_toc()

    def dump(self, space="", show_content=False):
        for b in self.children:
            # print('in for', b, b.is_heading())
            if show_content or b.is_heading():
                if b.is_heading():
                    print(
                        space,
                        b.get_heading()[:30],
                        b.type,
                        "level",
                        b.level,
                        "children",
                        len(b.children),
                        "matching toc",
                        b.match_toc,
                    )
                else:
                    print(
                        space,
                        b.text[:30],
                        b.type,
                        "level",
                        b.level,
                        "children",
                        len(self.children),
                    )
                b.dump(space + "  ", show_content=show_content)

    def get_blocks(self, max_length=utils_text.MAX_BASE_HEADING_LEN, with_toc=False):
        """
        Return all blocks and sub-blocks
        """
        ret = []
        for b in self.children:
            if b.type == TYPE_HEADING_TOC and not with_toc:
                continue
            if b.is_heading(check_children=True) and (
                max_length == -1 or len(b.get_heading()) < max_length
            ):
                ret.append(b)
            ret.extend(b.get_blocks())
        return ret

    def to_md(self):
        """
        Save as md
        """
        ret = []
        if self.is_heading():
            content = self.get_heading()
        else:
            content = self.text
        if self.text in [BLOCK_ROOT, BLOCK_CONTENT]:
            pass
        elif self.type == TYPE_HEADING_KEYWORD:  # Keyword Titles
            ret.append("")
            ret.append(f"## {content}")
            ret.append("")
        elif self.type == TYPE_HEADING_BASE:
            ret.append("")
            ret.append(f"{'#'*self.level} {content}")
            ret.append("")
        elif self.type == TYPE_CONTENT_TOC_ITEM:
            text = self.text.replace("\t", "_").replace(
                " ", "_"
            )  # The mistune library does not support mixed tabs and spaces for anchors
            if self.level == -1:
                ret.append(f"- [{text}](#{text})")
            else:
                ret.append(f"{'  '*self.level}- [{text}](#{text})")
        elif self.type == TYPE_CONTENT_TABLE:
            ret.append("")
            if self.data is not None:
                ret.append(tools_md.table_to_md(self.data))
            else:
                ret.append(self.text)
            ret.append("")
        else:
            ret.append(content)
            ret.append("")

        try:
            for b in self.children:
                ret.append(b.to_md())
        except Exception as e:
            print(e)
            traceback.print_exc()
        ret = "\n".join(ret)
        ret = ret.replace("\n\n\n", "\n\n")
        return ret

    def adjust(self, level=1):
        """
        After completing all add operations, adjust the level hierarchy
        Mainly used to support auto-recognized numbering and keyword titles
        """
        for b in self.children:
            if (
                b.type == TYPE_HEADING_NUM or b.type == TYPE_HEADING_KEYWORD
            ) and b.level == -1:
                b.level = level
                b.adjust(level + 1)
            else:
                b.adjust(level)

    def calc_heading(self, parent_num="", current_num=-1):
        """
        Calculate the title number
        """
        if self.is_heading():
            if self.heading_text is None:
                if self.heading_no_idx():
                    self.heading_text = self.text
                else:
                    if current_num == -1:
                        self.heading_text = self.text
                    elif parent_num == "":
                        if self.type == TYPE_CONTENT_NUM_ITEM:
                            idx_string = utils_text.calc_index_by_level("", current_num)
                            self.heading_text = f"{idx_string} {self.text}"
                        elif self.type == TYPE_HEADING_BASE:
                            idx_string = utils_text.calc_index_by_level("", current_num)
                            self.heading_text = f"{idx_string} {self.text}"
                        else:
                            self.heading_text = self.text
                    else:
                        ret, _, _ = utils_text.is_base_title(
                            self.text, max_length=-1
                        )  # Bring your own number in the text
                        if ret:  # itself is already a numbered title
                            self.heading_text = self.text
                        else:
                            idx_string = self.get_index_string(
                                parent_num, current_num, self.type
                            )
                            self.heading_text = f"{idx_string} {self.text}"
                            # self.heading_text = f"{parent_num}.{current_num} {self.text}"
            real_idx = utils_text.get_real_index(self.heading_text)
            # print("calc_heading", self.text, self.type, parent_num, current_num, "@@", self.heading_text, "real_idx", real_idx)
            idx = 0
            for child in self.children:
                if child.is_heading() and not child.heading_no_idx():
                    idx += 1
                child.calc_heading(".".join(real_idx), idx)

    def merge_index(self, parent_num, current_num):
        """
        Merge the numbers of the new titles
        """
        return f"{utils_text.get_number_str(parent_num)}.{current_num}"

    def get_index_string(self, parent_num, current_num, dtype):
        """
        Calculate the title number
        """
        # print("get_index_string", parent_num, current_num, dtype, self.text)
        if dtype == TYPE_CONTENT_NUM_ITEM:
            if utils_text.get_index_level(parent_num) <= 2:
                return self.merge_index(parent_num, current_num)
            return utils_text.calc_index_by_level(parent_num, current_num)
        elif dtype == TYPE_CONTENT_LIST_ITEM:
            if (
                False
            ):  # xieyan 231108 test, this logic forcibly converts list item to num item
                if utils_text.get_index_level(parent_num) <= 1:
                    return self.merge_index(parent_num, current_num)
                return "*"
            else:
                if utils_text.get_index_level(parent_num) <= 2:
                    return self.merge_index(parent_num, current_num)
                return utils_text.calc_index_by_level(parent_num, current_num)
        else:
            if (
                utils_text.get_index_level(parent_num) <= 2
            ):  # 231108 Generally, Chinese documents rarely have fourth-level headings
                return self.merge_index(parent_num, current_num)
            else:
                return utils_text.calc_index_by_level(parent_num, current_num)

    def heading_no_idx(self):
        """
        Judgment: It is a title without a number
        """
        if self.type == TYPE_HEADING_TOC:
            return True
        if self.type == TYPE_HEADING_TOP_LEVEL:
            return True
        if self.text in [BLOCK_ROOT, BLOCK_CONTENT]:
            return True
        return False


def find_blocks_by_type(block, dtype):
    """
    Find all eligible subblocks from "block"
    """
    ret = []
    if block.type == dtype:
        ret.append(block)
    for b in block.children:
        sub_ret = find_blocks_by_type(b, dtype)
        if sub_ret is not None:
            ret.extend(sub_ret)
    return ret


def get_block_list(block, dtype=None):
    """
    Return the flattened sub-block that meets the conditions
    """
    ret = []
    if dtype is None or block.type == dtype:
        ret.append(block)
    for b in block.children:
        sub_ret = get_block_list(b, dtype=dtype)
        if sub_ret is not None:
            ret.extend(sub_ret)
    return ret


def get_block_by_heading(root_block, heading_list):
    """
    Find the block corresponding to the first heading in the heading_list from root_block
    """
    blocks = get_block_list(root_block)
    for b in blocks:
        if b.get_heading().lower() in [keyword.lower() for keyword in heading_list]:
            return b
    return None
