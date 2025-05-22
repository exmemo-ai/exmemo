"""
apt-get install ghostscript
pip install baidu-aip
pip install PyMuPDF # fitz
pip install pdfplumber
pip install pypdf2

vim /etc/ImageMagick-6/policy.xml
Comment out <policy domain="coder" rights="read|write" pattern="PDF" />

Can solve the text in PDF, generating different titles based on different font sizes
"""

import os
import PyPDF2.generic
import pdfplumber
import PyPDF2
from loguru import logger
import numpy as np
import pandas as pd
import fitz
import traceback
from .base_parser import BaseParser
from .block import *
from . import difflibparser as difflibparser
from . import utils_tools as utils_tools
from . import ocr_baidu as ocr_baidu

from backend.common.files import utils_file as utils_file

END_SYMBOL = ["。", "；"]
DEFAULT_LANG = "zh-cn"
MAX_DESC_LEN = 2048
MAX_TITLE_LEN = 256


def is_near(x1, x2, size_list=None, debug=False):
    """
    According to the font size size_list, determine whether x1 and x2 are close, mainly used to judge the space at the beginning of the paragraph.
    """
    if debug:
        logger.debug(f"is_near (check paragraph start) {x1} {x2}")
    if size_list is None:
        return abs(x1 - x2) < 5
    else:
        return abs(x1 - x2) < np.percentile(size_list, 0.5)


def merge_para(string, percent=75, debug=False):
    """
    Merge lines into paragraphs, mainly for processing text in images, and for cases where the fitz library is not used
    """
    arr = string.split("\n")
    if debug:
        logger.debug(f"merge_para has line {len(arr)}")

    ll = [len(x) for x in arr]
    para_arr = []

    # The text in the table does not fill the entire line, but there are also line breaks, which are currently not supported.
    full_len = np.percentile(
        ll, percent
    )  # Greater than the 75th percentile is considered to occupy the full line
    if debug:
        logger.debug(f"merge_para full line len {full_len}")
    para = ""
    for idx, line in enumerate(arr):
        line = line.strip()
        para += line
        if len(line) >= full_len and len(line) > 0:
            if line[-1] not in END_SYMBOL:
                continue
        para_arr.append(para)
        para = ""
    if len(para) > 0:
        para_arr.append(para)
    if debug:
        logger.debug(f"merge_para to {len(para_arr)}")
    return para_arr


def parse_image(dir_path, page, idx=None, debug=False):
    utils_file.create_dir(dir_path)
    if idx is None:
        file_path = os.path.join(dir_path, f"tmp.png")
    else:
        file_path = os.path.join(dir_path, f"{idx}.png")
    if not os.path.exists(file_path):
        if debug:
            logger.info(f"save {file_path}")
        if len(page.images) > 0:
            width = page.images[0]["srcsize"][0]
            if width > 1024:
                width = 1024
        else:
            width = 1024
        img = page.to_image(width=width)
        img.save(file_path)

    ret, text = ocr_baidu.img_to_str_baidu(file_path, debug=debug)
    if debug:
        logger.info(f'img {file_path} has text "{len(text)}"')
    return text


class PdfTable:
    @staticmethod
    def merge_tables(texts, tables, arr, auto_detect=True, keywords=None, debug=False):
        """
        Merge text and table, then add to arr
        """
        remove_dict = {}  # Used to record text that needs to be deleted
        table_df = []  # for storing table data
        already_add = []  # Used to record tables that have been added

        if debug:
            logger.debug(f"merge tables, has {len(tables)} tables")
        for table_idx, table in enumerate(tables):
            arr_table = []
            data = []
            for row in table:
                data.append(
                    [
                        cell.replace("\n", " ") if isinstance(cell, str) else cell
                        for cell in row
                    ]
                )
                arr_table.append(" ".join([x for x in row if pd.notnull(x)]))
            df = pd.DataFrame(data)
            table_df.append(PdfTable.regular_table(df, debug=debug))

            # Compare text and tables, remove text that has been identified as tables
            diff = difflibparser.DifflibParser(texts, arr_table)
            count = 0  # Text location for record deletion
            for d in enumerate(diff):
                if d[1]["code"] != difflibparser.DiffCode.RIGHTONLY:
                    if d[1]["code"] != difflibparser.DiffCode.LEFTONLY:
                        remove_dict[count] = table_idx
                    count += 1
            if debug and len(remove_dict) > 0:
                logger.debug(f"merge tables, remove line {remove_dict}")

        for idx, text in enumerate(texts):
            if idx not in remove_dict:
                arr_line = text.split("\n")
                for line in arr_line:
                    arr.append(
                        Block(
                            {"text": line, "auto_detect": auto_detect},
                            keywords=keywords,
                        )
                    )
            else:
                if remove_dict[idx] not in already_add:
                    already_add.append(remove_dict[idx])
                    df = table_df[remove_dict[idx]]
                    if debug:
                        logger.debug(df)
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

    @staticmethod
    def regular_table(df, debug=False):
        """
        Convert table data to standard format
        """
        if df is None:
            return None
        df = df.replace(np.nan, "", regex=True)
        df = df.replace(" ", "", regex=True)
        df = df.replace("\n", "", regex=True)
        df = df.replace("\t", "", regex=True)
        df = df.replace("None", "", regex=True)
        df = df.replace("nan", "", regex=True)
        df = df.replace("", np.nan, regex=True)
        df = df.dropna(axis=1, how="all")
        # df = df.replace(np.nan, '', regex=True)
        df_ret = PdfTable.merge_columns(df, debug=False)
        if debug:
            logger.debug(f"merge columns {df.shape} -> {df_ret.shape}")
        df_ret.columns = range(df_ret.shape[1])
        df_ret = df_ret.replace(np.nan, "", regex=True)
        return df_ret

    @staticmethod
    def merge_columns(df, debug=False):
        """
        Merge adjacent empty columns
        """
        if df is None:
            return None

        columns = df.columns
        merge_list = []
        idx = 0
        already_merge = False

        while idx < len(columns) - 1:
            col1 = columns[idx]
            col2 = columns[idx + 1]

            # Determine if staggered
            need_merge = True
            for index, row in df.iterrows():
                if pd.notnull(row[col1]) and pd.notnull(row[col2]):
                    if debug:
                        logger.debug(
                            f"merge table, not na *{row[col1]}*, *{row[col2]}*, {index}"
                        )
                    need_merge = False
            if debug:
                logger.debug(f"merge table {col1}, {col2}, {need_merge}")

            if need_merge:
                merge_list.append((idx, idx + 1))
                idx += 2
            else:
                idx += 1
            if debug:
                logger.debug(f"merge list {merge_list}")

            for x in merge_list:
                df.loc[:, columns[x[0]]] = df[columns[x[0]]].fillna(df[columns[x[1]]])
                df.loc[:, columns[x[1]]] = np.nan
                already_merge = True

        df = df.dropna(axis=1, how="all")

        if already_merge:
            return PdfTable.merge_columns(
                df, debug
            )  # may need to be merged multiple times
        else:
            return df


class PdfBlock:
    """
    Each block may contain multiple lines
    """

    def __init__(self, block, language):
        self.block = block
        self.language = language
        self.parse()

    def is_empty(self):
        if self.block is None and "lines" not in self.block:
            return True
        return False

    def __str__(self) -> str:
        if "lines" not in self.block:
            return "empty lines block"
        return f"pdf block has {len(self.block['lines'])} lines"

    def parse(self, debug=False):
        """
        Get block information
        """
        size_list = []  # Font Size List
        lines = []
        last_right = -1  # Used to judge line breaks
        last_y_mid = -1  # Middle position in y
        base_left, base_right = self.calc_left_right()

        last_line_full = False
        if "lines" in self.block:
            for line in self.block["lines"]:
                line_text = ""  # String in line
                if debug:
                    logger.debug(f"   spans  {len(line['spans'])}")
                # print('line', line['bbox'])
                for span in line["spans"]:  # Blocks in different formats in line
                    size_list.append(
                        round(span["size"], 1)
                    )  # Keep one decimal place in font size
                    if debug:
                        logger.debug(
                            f"     {round(span['size'],1)}, {span['text']}, {span['bbox']}"
                        )
                    if self.is_zh():
                        line_text += span["text"].replace(" ", "")  # Remove spaces
                    else:
                        line_text += span["text"]
                if last_right == -1:
                    lines.append((line_text, "NEW_PARAGRAPH"))
                elif (
                    line["bbox"][0] < last_right and line["bbox"][1] > last_y_mid
                ):  # Line feed
                    # Determine leading spaces: The end of the line is more complicated, let's look at it later
                    if not last_line_full:
                        lines.append((line_text, "NEW_PARAGRAPH"))
                    elif is_near(line["bbox"][0], base_left, size_list):
                        lines.append((line_text, "NEW_LINE"))
                    else:
                        lines.append((line_text, "NEW_LINE"))
                else:
                    lines.append((line_text, "SAME_LINE"))
                last_right = line["bbox"][2]
                last_y_mid = (line["bbox"][3] + line["bbox"][1]) / 2
                if (
                    line["bbox"][2] < base_right * 0.8
                ):  # The previous line did not fill 80%
                    last_line_full = False
                else:
                    last_line_full = True

        if len(size_list) > 0:
            self.size = utils_tools.most_common(size_list)
        else:
            self.size = 8
        self.size_list = (
            size_list  # List of text sizes for calculating headings and body text
        )
        if debug:
            logger.debug(
                f"fontsize {np.percentile(size_list,0.25)}, {np.percentile(size_list,0.5)}, {np.percentile(size_list,0.75)}"
            )

        self.text = self.merge_lines(
            lines, debug=debug
        )  # Plain text, optimize the handling of line breaks
        self.lines = [
            line for (line, _) in lines
        ]  # Array of lines, no optimization for newline handling
        if debug:
            logger.debug(f"info {lines}")

    def get_text(self):
        return self.text

    def get_bbox(self):
        return self.block[
            "bbox"
        ]  # Block position, which can potentially be used to determine the order

    def calc_left_right(self):
        """
        Take the logical left and right boundaries of the block, distinguishing between line breaks and paragraph breaks
        """
        # TODO If there's only one line, it needs special handling
        left_list = []
        right_list = []
        if "lines" in self.block:
            for line in self.block["lines"]:
                left_list.append(line["bbox"][0])
                right_list.append(line["bbox"][2])
            base_left = utils_tools.most_common(left_list)
            base_right = utils_tools.most_common(right_list)
            if base_left is None:
                base_left = self.block["bbox"][0]
            if base_right is None:
                base_right = self.block["bbox"][2]
            return base_left, base_right
        else:
            return self.block["bbox"][0], self.block["bbox"][2]

    def is_zh(self):
        if self.language == DEFAULT_LANG:
            return True
        else:
            return False

    def merge_lines(self, line_arr, debug=False):
        """
        Remove extra line breaks based on the positions shown in line_arr
        """
        ret = ""
        for line, dtype in line_arr:
            if debug:
                logger.debug(f"merge_line, line {line}, dtype {dtype}")
            if dtype == "NEW_LINE":
                if self.is_zh():
                    ret += line
                else:
                    if len(ret) > 0 and ret[-1] == "-":
                        ret = ret[:-1]
                        ret += line
                    else:
                        ret += " " + line
            elif dtype == "NEW_PARAGRAPH":
                if ret != "":
                    ret += "\n" + line
                else:
                    ret += line
            elif dtype == "SAME_LINE":
                ret += " " + line
        return ret


def check_header_footer(block, page_height, percent=0.1, debug=False):
    """
    Determine headers and footers
    """
    if debug:
        logger.debug(f"check_header_footer {block['bbox']}, {page_height}")
    if block["bbox"][1] < page_height * percent:
        return "header"
    elif block["bbox"][3] > page_height * (1 - percent):
        return "footer"
    else:
        return None


def parse_pdf(
    path_in,
    page_limit=-1,
    support_image=True,
    use_fitz=True,
    parse_table=True,
    auto_detect=True,
    use_ocr=False,
    keywords=None,
    debug=False,
):
    # def parse_pdf(path_in, page_limit = 5, support_image = True, use_fitz = True, parse_table = True, debug=False):
    # debug = True # xieyan
    # use_fitz = False # xieyan
    """
    Use two libraries simultaneously to parse PDF files, extracting text and images from the PDF
    auto_detect: Whether to automatically detect titles
    """
    if use_fitz:
        pdf_document = fitz.open(path_in)
    arr = []
    ret_info = {}
    image_count = 0
    with pdfplumber.open(path_in) as pdf:
        if debug:
            logger.info(f"total page {len(pdf.pages)}")

        for pidx, page in enumerate(pdf.pages):
            if page_limit != -1 and pidx >= page_limit:
                break
            if debug:
                logger.debug(f"parse page {pidx}")

            # Parsing Text
            page_text = ""
            if use_fitz:
                fitz_page = pdf_document.load_page(pidx)
                # font_list = fitz_page.get_fonts()
                # for font_index in font_list:
                #    print(font_index)
                try:
                    text = fitz_page.get_text()
                    if pd.notnull(text) and len(text) > 0:
                        language = utils_file.check_language_by_data(text)
                        text_areas = fitz_page.get_text("dict")
                        page_height = text_areas["height"]
                        if debug:
                            logger.info(
                                f"  has {len(text_areas['blocks'])} blocks, language {language}"
                            )
                        blocks = []
                        for bidx, t in enumerate(text_areas["blocks"]):
                            b = PdfBlock(t, language)
                            if not b.is_empty():
                                if debug:
                                    logger.debug(b)
                                # blocks.append(b)
                                ptype = check_header_footer(t, page_height, debug=debug)
                                if ptype is None:
                                    blocks.append(b)
                                else:
                                    ftext = b.get_text().strip()
                                    if (
                                        ftext.isdigit() and int(ftext) > 0
                                    ):  # Page numbers may not necessarily match page_number
                                        if debug:
                                            logger.debug(f"found page number {ftext}")
                                    else:
                                        blocks.append(b)

                        texts = [b.get_text() for b in blocks]
                        # for text in texts: # for test
                        #    logger.debug(f"@@@ {text[:30]}")
                        if parse_table:
                            PdfTable.merge_tables(
                                texts,
                                page.extract_tables(),
                                arr,
                                auto_detect=auto_detect,
                                keywords=keywords,
                                debug=debug,
                            )
                        else:
                            for b in blocks:
                                text = b.get_text(language)
                                arr_line = text.split("\n")
                                for line in arr_line:
                                    arr.append(
                                        Block(
                                            {"text": line, "auto_detect": auto_detect},
                                            keywords=keywords,
                                        )
                                    )
                        page_text = "\n".join(texts)
                    else:
                        page_text = ""
                except Exception as e:
                    logger.warning(f"Exception: {e}")
                    traceback.print_exc()
            else:
                text = page.extract_text()
                if text is not None and len(text) > 0:
                    page_text = text
                    if debug:
                        logger.debug(f"  has text {len(text)}")
                    arr.append(
                        Block(
                            {"text": text, "auto_detect": auto_detect},
                            keywords=keywords,
                        )
                    )

            # Extracting Image Data
            if debug:
                logger.info(
                    f"page:{pidx}, txt len:{len(page_text)}, has section image {len(page.images)}"
                )
            # if support_image and (len(page.images) > 0 or text is None): # for test
            if (
                support_image
                and (len(page.images) > 0 or len(page_text) == 0)
                and len(page_text) < 50
            ):
                dir_path = os.path.join("/tmp/", utils_file.get_basename(path_in))
                if use_ocr:
                    text = parse_image(dir_path, page, pidx, debug=debug)
                else:
                    text = ""
                image_count += 1
                arr.append(
                    Block({"text": text, "auto_detect": auto_detect}, keywords=keywords)
                )
    if debug:
        logger.info(f"after convert {len(arr)} pages")
    if use_fitz:
        pdf_document.close()
    ret_info["image_count"] = image_count
    return ret_info, arr


class PdfMeta:
    @staticmethod
    def extract_pdf_info(pdf_path, debug=False):
        """
        Extract PDF metadata and table of contents
        """
        meta_info = {}
        toc_items = []
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                meta_data = pdf_reader.metadata
                if debug:
                    logger.info(f"meta_data {meta_data}")
                if "/Author" in meta_data:
                    meta_info["creator"] = str(meta_data["/Author"])
                if "/Title" in meta_data:
                    meta_info["title"] = str(meta_data["/Title"])
                toc_items = PdfMeta.get_outline_item(pdf_reader.outline)
        except Exception as e:
            logger.warning(f"Exception: {e}")
            traceback.print_exc()
        return meta_info, toc_items

    @staticmethod
    def get_outline_item(item, depth=-1):
        """
        Recursively get the catalog of the pdf
        """
        ret = []
        try:
            if type(item) == list:
                for i in item:
                    sub_ret = PdfMeta.get_outline_item(i, depth + 1)
                    ret.extend(sub_ret)
            else:
                title = item.title
                if isinstance(item.page, PyPDF2.generic.NumberObject):
                    ret.append(
                        {"title": title, "level": depth, "page": item.page.as_numeric()}
                    )
                else:
                    ret.append(
                        {"title": title, "level": depth, "page": item.page.idnum}
                    )
        except Exception as e:
            logger.warning("Exception:", e)
            traceback.print_exc()
        return ret


def get_toc_item_title(text):
    print(text)
    return text


def get_toc_item_detail(text):
    print(text)
    return text


def find_block(text, blocks, last_idx):
    sim_max = 0.3
    sim_idx = -1
    for idx, block in enumerate(blocks):
        if idx <= last_idx:
            continue
        sim = utils_text.calc_similarity(text, block.text)
        if sim > sim_max:
            sim_max = sim
            sim_idx = idx
    return sim_idx


def reset_toc(blocks, toc_items, debug=False):
    """
    Reset the directory title
    """
    last_idx = -1
    for toc_item in toc_items:
        real_text = toc_item["title"]
        if len(real_text) == 0:
            continue
        sim_idx = find_block(real_text, blocks, last_idx)
        if sim_idx == -1:
            logger.warning(f"can't match toc item {toc_item}")
            last_idx = -1
            sim_idx = find_block(real_text, blocks, last_idx)
            if sim_idx == -1:
                continue
        if debug:
            print("set toc", toc_item, blocks[sim_idx].get_text()[:50])
        blocks[sim_idx].type = TYPE_HEADING_BASE
        blocks[sim_idx].level = toc_item["level"] + 1
        last_idx = sim_idx


class PDFParser(BaseParser):
    def __init__(self, data, with_parse=True, debug=False, **kwargs):
        self.use_ocr = kwargs.get("use_ocr", False)
        if ocr_baidu.get_baidu_client() is None:
            self.use_ocr = False
        logger.info(
            f"PDFParser, use_ocr:{self.use_ocr}, ocr_env:{ocr_baidu.get_baidu_client()}"
        )
        super().__init__(data, with_parse=with_parse, debug=debug, **kwargs)

    def set_keywords(self, keywords):
        self.keywords = keywords

    def parse(self, data, debug=False):
        meta_info, toc_items = PdfMeta.extract_pdf_info(data, debug=debug)
        if debug:
            logger.info(f"meta_info {meta_info}")
            logger.info(f"toc_items {toc_items}")
        if len(toc_items) > 0:
            info, arr = parse_pdf(
                data, auto_detect=False, use_ocr=self.use_ocr, debug=debug
            )
            reset_toc(arr, toc_items, debug=debug)
        else:
            if hasattr(self, "keywords"):
                info, arr = parse_pdf(
                    data,
                    auto_detect=False,
                    use_ocr=self.use_ocr,
                    keywords=self.keywords,
                    debug=debug,
                )
            else:
                info, arr = parse_pdf(
                    data, auto_detect=True, use_ocr=self.use_ocr, debug=debug
                )

        if "title" in meta_info and len(meta_info["title"].strip()) > 0:
            self.title = meta_info["title"]
        if "creator" in meta_info and len(meta_info["creator"].strip()) > 0:
            self.creator = meta_info["creator"]

        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        if len(toc_items) > 0:
            root_block.add(
                Block({"type": TYPE_HEADING_TOC, "text": "Table of Contents"})
            )
            for item in toc_items:
                if debug:
                    logger.info(f"toc {item}")
                root_block.add(
                    Block(
                        {
                            "type": TYPE_CONTENT_TOC_ITEM,
                            "text": item["title"],
                            "level": item["level"] + 1,
                        }
                    )
                )
        for block in arr:
            root_block.add(block)
        return root_block

    def get_meta_info(self, debug=False):
        info = {}
        if hasattr(self, "title") and self.title is not None:
            info["title"] = self.title
        else:
            # Use the first line of the body as the title (if too long, do not set)
            if hasattr(self, "root_block"):
                blocks = get_block_list(self.root_block, dtype=TYPE_CONTENT_PARAGRAPH)
                for b in blocks:
                    text = b.get_text()
                    if len(text) < MAX_TITLE_LEN:
                        info["title"] = b.get_text()
                    break
        if hasattr(self, "creator") and self.creator is not None:
            info["author"] = self.creator
        return info


def test():
    in_path = "xxx.pdf"
    out_path = in_path.replace(".pdf", "_new.md")
    parser = PDFParser(in_path)
    parser.save(out_path)


# test()
