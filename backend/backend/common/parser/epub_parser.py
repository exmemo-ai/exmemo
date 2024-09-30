from .base_parser import BaseParser
from .block import *
import re
import ebooklib
from ebooklib import epub
from markdownify import markdownify as md


def remove_xml_declaration(input_bytes):
    pattern = re.compile(b"<\?xml version='.*' encoding='.*'\?>", re.IGNORECASE)
    result = re.sub(pattern, b"", input_bytes)
    return result


class EPUBParser(BaseParser):
    def parse_info(self, data):
        ret = []
        if isinstance(data, list) and len(data) > 0:
            for item in data:
                if isinstance(item, tuple) and len(item) > 0:
                    ret.append(item[0])
        if len(ret) > 0:
            return ",".join(ret)
        return None

    def parse(self, data, debug=False):
        book = epub.read_epub(data)
        self.title = self.parse_info(book.get_metadata("DC", "title"))
        self.creator = self.parse_info(book.get_metadata("DC", "creator"))
        self.language = self.parse_info(book.get_metadata("DC", "language"))
        toc_items = self.parse_toc(book.toc)
        if debug:
            print("title", self.title)
            print("creator", self.creator)
            print(book.get_metadata("DC", "creator"))
            print("language", self.language)
            print(toc_items)

        text = ""
        for item in book.items:
            if isinstance(item, epub.EpubHtml):
                item_string = md(remove_xml_declaration(item.get_content()))
                item_string = re.sub(r"\n+", "\n", item_string.strip())
                # print('in if', item.file_name, item_string[:50])
                text += item_string
            elif isinstance(item, epub.EpubNcx):
                if debug:
                    print("in elif", item.file_name, item.content[:50])
            else:
                if debug:
                    print("others", type(item), item.file_name, item.content[:50])

        root_block = Block({"text": BLOCK_ROOT, "type": TYPE_HEADING_BASE, "level": 0})
        if len(toc_items) > 0:
            for item in toc_items:
                root_block.add(
                    Block(
                        {
                            "type": TYPE_CONTENT_TOC_ITEM,
                            "text": item["title"],
                            "level": item["level"],
                            "href": item["href"],
                        }
                    )
                )
        for line in text.split("\n"):
            root_block.add(Block({"text": line.strip()}))
        return root_block

    def parse_toc(self, item, level=0, debug=False):
        """
        Parse directory structure
        """
        ret = []
        if isinstance(item, list) or isinstance(item, tuple):
            for sub_item in item:
                if isinstance(sub_item, ebooklib.epub.Link):
                    ret.append(
                        {"title": sub_item.title, "href": sub_item.href, "level": level}
                    )
                    if debug:
                        print(
                            " " * level,
                            "Link, level",
                            level,
                            "title",
                            sub_item.title,
                            "href",
                            sub_item.href,
                        )
                elif isinstance(sub_item, tuple):
                    ret.append(
                        {
                            "title": sub_item[0].title,
                            "href": sub_item[0].href,
                            "level": level,
                        }
                    )
                    if debug:
                        print(
                            " " * level,
                            "Section, level",
                            level,
                            "title",
                            sub_item[0].title,
                            "href",
                            sub_item[0].href,
                        )
                    ret_sub = self.parse_toc(sub_item[1], level + 1)
                    ret.extend(ret_sub)
                else:
                    print("1.unknown item", type(sub_item), sub_item)
        else:
            print("2.unknown item", type(item))
        return ret

    def get_meta_info(self):
        info = {}
        if hasattr(self, "title") and self.title is not None:
            info["title"] = self.title
        if hasattr(self, "creator") and self.creator is not None:
            info["creator"] = self.creator
        if hasattr(self, "language") and self.language is not None:
            info["language"] = self.language
        return info
