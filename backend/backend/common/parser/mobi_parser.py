import re
from markdownify import markdownify as md
from .base_parser import BaseParser
from .block import *
import shutil
from loguru import logger
import tempfile
from os.path import basename, splitext, exists, join
from mobi.kindleunpack import unpackBook, unpackException
from mobi.compatibility_utils import unicode_str
from mobi.unpack_structure import fileNames
from mobi.mobi_sectioner import Sectionizer
from mobi.mobi_header import MobiHeader
from mobi.mobi_ncx import ncxExtract


def analysis_meta(infile, outdir, apnxfile=None, debug=False):
    meta_info = {}
    ncx_list = []
    infile = unicode_str(infile)
    outdir = unicode_str(outdir)
    if apnxfile is not None:
        apnxfile = unicode_str(apnxfile)

    files = fileNames(infile, outdir)

    # process the PalmDoc database header and verify it is a mobi
    sect = Sectionizer(infile)
    if sect.ident != b"BOOKMOBI" and sect.ident != b"TEXtREAd":
        raise unpackException("Invalid file format")

    # scan sections to see if this is a compound mobi file (K8 format)
    # and build a list of all mobi headers to process.
    mh = MobiHeader(sect, 0)
    meta_data = mh.getMetaData()
    if "Title" in meta_data:
        meta_info["title"] = ",".join(meta_data["Title"])
    if "Creator" in meta_data:
        meta_info["creator"] = ",".join(meta_data["Creator"])
    if "Language" in meta_data:
        meta_info["language"] = ",".join(meta_data["Language"])
    if "ISBN" in meta_data:
        meta_info["ISBN"] = ",".join(meta_data["ISBN"])
    if debug:
        logger.debug("meta_info", meta_info)
    if mh.hasNCX():
        ncx = ncxExtract(mh, files)
        ncx_data = ncx.parseNCX()
        for item in ncx_data:
            ncx_list.append({"title": item["text"], "level": item["hlvl"]})
    return meta_info, ncx_list


def extract(infile, debug=False):
    """
    copy from extract.py, and add get meta info and ncx list
    """

    tempdir = tempfile.mkdtemp(prefix="mobiex")
    if hasattr(infile, "fileno"):
        tempname = next(tempfile._get_candidate_names()) + ".mobi"
        pos = infile.tell()
        infile.seek(0)
        with open(join(tempdir, tempname), "wb") as outfile:
            shutil.copyfileobj(infile, outfile)
        infile.seek(pos)
        infile = join(tempdir, tempname)

    if debug:
        logger.debug("file: %s" % infile)
    fname_in = basename(infile)
    base, ext = splitext(fname_in)
    fname_out_epub = base + ".epub"
    fname_out_html = "book.html"
    fname_out_pdf = base + ".001.pdf"
    unpackBook(infile, tempdir)
    meta_info, ncx_list = analysis_meta(infile, tempdir)
    epub_filepath = join(tempdir, "mobi8", fname_out_epub)
    html_filepath = join(tempdir, "mobi7", fname_out_html)
    pdf_filepath = join(tempdir, fname_out_pdf)
    if exists(epub_filepath):
        return tempdir, epub_filepath, meta_info, ncx_list
    elif exists(html_filepath):
        return tempdir, html_filepath, meta_info, ncx_list
    elif exists(pdf_filepath):
        return tempdir, pdf_filepath, meta_info, ncx_list
    raise ValueError("Coud not extract from %s" % infile)


class MOBIParser(BaseParser):
    def parse(self, data, debug=False):
        try:
            mobi_filename = data
            dirpath, html_file, meta_info, toc_items = extract(mobi_filename)
            if debug:
                print("tmp dir", dirpath)
            if "title" in meta_info:
                self.title = meta_info["title"]
            if "creator" in meta_info:
                self.creator = meta_info["creator"]
            if "language" in meta_info:
                self.language = meta_info["language"]
            if "ISBN" in meta_info:
                self.ISBN = meta_info["ISBN"]

            with open(html_file, "r", encoding="utf-8") as f:
                text = md(f.read())
                text = re.sub(r"\n+", "\n", text.strip())

            root_block = Block(
                {"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0}
            )
            if len(toc_items) > 0:
                for item in toc_items:
                    if debug:
                        print("toc item", item)
                    root_block.add(
                        Block(
                            {
                                "type": TYPE_CONTENT_TOC_ITEM,
                                "text": item["title"],
                                "level": item["level"],
                            }
                        )
                    )
            for line in text.split("\n"):
                root_block.add(Block({"text": line.strip()}))
            return root_block
        except Exception as e:
            print(f"MOBIParser:parser() {e}")
            return None

    def get_meta_info(self):
        info = {}
        if hasattr(self, "title") and self.title is not None:
            info["title"] = self.title
        if hasattr(self, "creator") and self.creator is not None:
            info["creator"] = self.creator
        if hasattr(self, "language") and self.language is not None:
            info["language"] = self.language
        if hasattr(self, "ISBN") and self.language is not None:
            info["ISBN"] = self.ISBN
        return info
