"""
Convert docx file to markdown format
# pip install python-docx
"""

import re
import docx
import pandas as pd
from docx.oxml.numbering import CT_NumPr
from .block import *
from .base_parser import BaseParser
from . import utils_text


def find_element(element, ctype=CT_NumPr):
    """
    Returns the first occurrence of the specified type of child element
    """
    for child in element:
        if isinstance(child, ctype):
            return child
        e = find_element(child, ctype)
        if e is not None:
            return e
    return None


def get_number(root):
    """
    Return the paragraph number information
    """
    e = find_element(root)
    if e is not None:
        # ilvl: indent level
        # numId: Id Type
        # print('\t get_number', e.ilvl.val, e.numId.val)
        return True, e.ilvl.val, e.numId.val
    return False, 0, 0


def get_docx_blocks(path_in, debug=False):
    arr = []
    doc = docx.Document(path_in)
    for idx1, section in enumerate(doc.sections):
        for idx2, block in enumerate(section.iter_inner_content()):
            if isinstance(block, docx.text.paragraph.Paragraph):
                # if len(block.text.strip()) == 0:
                #    continue
                # print(idx1, idx2, 'para', len(block.text), block.text[:30], block.style.name)
                if block.style.name.startswith("Heading "):
                    pattern = r"Heading (\d+)"
                    match = re.search(pattern, block.style.name)
                    arr.append(
                        Block(
                            {
                                "type": TYPE_HEADING_BASE,
                                "text": block.text.strip(),
                                "level": int(match.group(1)),
                            }
                        )
                    )
                elif block.style.name.startswith("MACH"):
                    pattern = r"MACH(\d+)"
                    match = re.search(pattern, block.style.name)
                    arr.append(
                        Block(
                            {
                                "type": TYPE_HEADING_BASE,
                                "text": block.text.strip(),
                                "level": int(match.group(1)),
                            }
                        )
                    )
                elif block.style.name.startswith("FWB_L"):
                    pattern = r"FWB_L(\d+)"
                    match = re.search(pattern, block.style.name)
                    if len(block.text.strip()) > 0:
                        arr.append(
                            Block(
                                {
                                    "type": TYPE_HEADING_BASE,
                                    "text": block.text.strip(),
                                    "level": int(match.group(1)),
                                }
                            )
                        )
                    else:
                        arr.append(Block({"type": TYPE_CONTENT_PARAGRAPH, "text": ""}))
                elif block.style.name.startswith("toc "):
                    pattern = r"toc (\d+)"
                    match = re.search(pattern, block.style.name)
                    arr.append(
                        Block(
                            {
                                "type": TYPE_CONTENT_TOC_ITEM,
                                "text": block.text.strip(),
                                "level": int(match.group(1)),
                            }
                        )
                    )
                elif block.style.name.startswith("List"):
                    if debug:
                        print(
                            "list",
                            block.style.name,
                            "len",
                            len(block.text.strip()),
                            "style",
                            block.style,
                        )
                    if len(block.text.strip()) > 0:
                        arr.append(
                            Block(
                                {
                                    "type": TYPE_CONTENT_LIST_ITEM,
                                    "text": block.text.strip(),
                                }
                            )
                        )
                    else:
                        arr.append(Block({"type": TYPE_CONTENT_PARAGRAPH, "text": ""}))
                    # print('list', block.text.strip())
                else:
                    has_num, ilvl, numId = get_number(block._p)
                    if has_num:
                        # if debug:
                        pure_str = block.text.strip()
                        # if True: # xieyan 231023
                        if debug:
                            print(f"numPr ilvl {ilvl} numId {numId}", pure_str)
                        if len(pure_str) > 0:
                            # ret.append(f"{' ' * ilvl}* {pure_str}")
                            # num_str = mtools.get_number_str(ilvl, numId, pure_str, debug=debug)
                            # ret.append(f"{'    ' * ilvl}- {num_str} {pure_str}")
                            # ret.append(f"{'    ' * ilvl}- {pure_str}")
                            arr.append(
                                Block(
                                    {
                                        "type": TYPE_CONTENT_NUM_ITEM,
                                        "level": -1,  # There is no hierarchical relationship between ilvl
                                        "style": numId + ilvl * 100,
                                        "text": f"{pure_str}",
                                    }
                                )
                            )
                        else:
                            arr.append(
                                Block({"type": TYPE_CONTENT_PARAGRAPH, "text": ""})
                            )
                    else:  # Body & Paragraph
                        if block.style.name != "Normal":
                            if debug:
                                print(
                                    "block", block.style.name, block.text.strip()[:30]
                                )
                        arr.append(Block({"text": block.text.strip()}))
            else:
                # print(idx1, idx2, type(block))
                table_arr = []
                for row in block.rows:
                    try:
                        dic = {}
                        for idx2, cell in enumerate(row.cells):
                            # print(f'row {idx2} {cell.text}')
                            if pd.notna(cell.text):
                                text = cell.text.replace("\n", " ")
                                dic[idx2] = text
                        table_arr.append(dic)
                    except Exception as e:
                        print("convert table failed", e)
                        # traceback.print_exc()

                df = pd.DataFrame(table_arr)
                # display(df)
                arr.append(
                    Block(
                        {
                            "type": TYPE_CONTENT_TABLE,
                            "data": df,
                            "text": df.to_string(index=False, header=None),
                        }
                    )
                )
            arr.append(Block({"type": TYPE_CONTENT_PARAGRAPH, "text": ""}))
    return arr


def get_toc_item_title(text):
    arr = text.split("_")
    if len(arr) != 3:
        arr = text.split("\t")
    if len(arr) == 3:
        return arr[1]
    return text


def get_toc_item_detail(text):
    """
    Extract specific format information of the titles from the directory
    """
    arr = text.split("_")
    if len(arr) != 3:
        arr = text.split("\t")
    if len(arr) == 3:
        return f"{arr[0]} {arr[1]}"
    return text


def reset_toc(blocks, debug=False):
    """
    Reset the directory title
    """
    last_idx = -1
    toc_items = []
    for block in blocks:
        if block.type == TYPE_CONTENT_TOC_ITEM:
            toc_items.append(block)
    for toc_item in toc_items:
        real_text = get_toc_item_title(toc_item.text)
        if len(real_text) == 0:
            continue
        sim_max = 0.3
        sim_idx = -1
        for idx, block in enumerate(blocks):
            if idx <= last_idx:
                continue
            sim = utils_text.calc_similarity(real_text, block.text)
            if sim > sim_max:
                sim_max = sim
                sim_idx = idx
        if sim_idx == -1:
            print("can't match toc item", toc_item.text)
            last_idx = -1
            continue
        if debug:
            print("set toc", toc_item.text, blocks[sim_idx].get_text()[:50])
        blocks[sim_idx].heading_text = get_toc_item_detail(toc_item.text)
        blocks[sim_idx].match_toc = toc_item.level
        last_idx = sim_idx


class DOCXParser(BaseParser):
    def parse(self, data, debug=False):
        arr = get_docx_blocks(data, debug=debug)
        reset_toc(arr, debug=debug)
        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        for idx, block in enumerate(arr):
            root_block.add(block)
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 1")
        # root_block.dump()
        # Recalculate Sequence Numbers
        root_block.calc_heading()
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 2")
        # root_block.dump()
        return root_block
