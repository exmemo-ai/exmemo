"""
To handle file-related operations
"""

import os
import json
import pytz
from typing import Any
from loguru import logger
from django.utils import timezone
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpResponse
from django.utils.translation import gettext as _

from backend.common.files import utils_filemanager, filecache
from backend.common.llm.llm_hub import EmbeddingTools
from backend.common.parser import converter, utils_md
from backend.common.parser.md_parser import MarkdownParser
from backend.common.utils.file_tools import is_plain_text, convert_to_md
from backend.common.utils.text_tools import convert_dic_to_json
from backend.common.utils.regular_tools import regular_keyword
from backend.common.utils.web_tools import get_url_content
from backend.common.user.user import UserManager

from .models import StoreEntry
from .feature import EntryFeatureTool, DEFAULT_CATEGORY
from .entry_item import EntryItem
from .entry_storage import EntryStorage

REL_DIR_FILES = "files"
REL_DIR_NOTES = "notes"
DESC_LENGTH = 50
# get PARSE_CONTENT from backend env settings


class EntryService:
    @staticmethod
    def process_entry(obj: dict | EntryItem, data=None, use_llm=True):
        if isinstance(obj, dict):
            entry_item = EntryItem.from_dict(obj)
        else:
            entry_item = obj
            
        handlers = {
            "file": EntryService._process_file_entry,
            "note": EntryService._process_file_entry,
            "record": EntryService._process_record_entry,
            "chat": EntryService._process_chat_entry,
            "web": EntryService._process_web_entry,
        }

        handler = handlers.get(entry_item.etype)
        if not handler:
            return False, False, _("unknown_type_colon_") + entry_item.etype

        return handler(entry_item, data, use_llm)

    @staticmethod
    def _process_chat_entry(entry: EntryItem, data: Any, use_llm: bool = True):
        # 默认title与ctype同时存在
        if ((entry.ctype == DEFAULT_CATEGORY or entry.ctype is None) 
            and data is not None and 'reduce_msg' in data 
            and data['reduce_msg'] is not None and len(data['reduce_msg']) > 0):
            EntryFeatureTool.get_instance().parse(entry, data['reduce_msg'], use_llm=use_llm)
        if entry.title is None and data is not None and 'default_title' in data:
            entry.title = data['default_title']
        content = None
        if data is not None and 'content' in data:
            content = data['content']
        return EntryStorage.save_entry(entry, content)


    @staticmethod
    def _process_record_entry(entry: EntryItem, data: Any, use_llm: bool = True):
        current_time = timezone.now().astimezone(pytz.UTC)
        if entry.addr is None:
            entry.addr = f'record_{current_time.strftime("%Y%m%d_%H%M%S")}'
        content = None
        if data is not None and 'content' in data:
            content = data['content']
        ret = EntryFeatureTool.get_instance().parse(
            entry, content, use_llm=use_llm
        )
        ret, ret_emb, detail = EntryStorage.save_entry(
            entry, content
        )
        if ret:
            if entry.ctype is not None:
                detail = _("record_successful_comma__type_colon_") + entry.ctype
        return ret, ret_emb, detail
    

    @staticmethod
    def _process_file_entry(entry: EntryItem, data: Any, use_llm: bool = True):
        user = UserManager.get_instance().get_user(entry.user_id)
        filename = os.path.basename(entry.addr)

        if entry.etype == "note":
            entry.path = os.path.join(REL_DIR_NOTES, entry.addr)
        else:
            entry.path = os.path.join(REL_DIR_FILES, entry.addr)
            
        if data is not None and "path" in data:
            path = data["path"]
        else:
            path = data

        if path is None:
            has_new_content = False
            if entry.idx is None:
                return False, False, _("save_file_failed_excl_")
        else:
            has_new_content = True
            ret = utils_filemanager.get_file_manager().save_file(
                entry.user_id, entry.path, path
            )
            if not ret:
                return False, False, _("save_file_failed_excl_")

        if has_new_content and entry.md5 is None:
            entry.md5 = utils_md.get_file_md5(path)

        meta_dic = {}
        content = None
        if has_new_content:
            if (entry.etype == "note" and user.get("note_save_content")) or (
                entry.etype == "file" and user.get("file_save_content")
            ):
                meta_dic, content = get_file_content_by_path(path, user)
            elif converter.is_markdown(path):
                parser = MarkdownParser(path)
                meta_dic = parser.fm

        if meta_dic is not None and isinstance(meta_dic, dict):
            entry.meta.update(meta_dic)
        ret = EntryFeatureTool.get_instance().parse(
            entry, filename, use_llm=use_llm
        )
        return EntryStorage.save_entry(entry, content, has_new_content)


    @staticmethod
    def _process_web_entry(entry: EntryItem, data: Any, use_llm: bool = True, debug: bool = False):
        """
        Download the file from the URL, parse the file, and store the data from the file into the database;
        This only handles plain web pages, does not consider files
        """
        user = UserManager.get_instance().get_user(entry.user_id)
        has_error = (
            "error" in entry.meta 
            and entry.meta["error"] is not None
        )
        need_download = (
            entry.source != "bookmark" or user.get("bookmark_download_web") == True
        )
        if has_error or not need_download:
            entry.ctype = DEFAULT_CATEGORY
            ret = EntryFeatureTool.get_instance().parse(
                entry, entry.addr, use_llm=False, debug=debug
            )
            if entry.path is None:
                entry.path = entry.title
            ret, ret_emb, detail = EntryStorage.save_entry(
                entry, None, debug=debug
            )
        else:
            ret = EntryFeatureTool.get_instance().parse(
                entry, entry.addr, use_llm=use_llm, debug=debug
            )
            if entry.path is None:
                entry.path = entry.title
            if user.get("web_save_content"):
                title, content = get_url_content(entry.addr)
                ret, ret_emb, detail = EntryStorage.save_entry(
                    entry, content
                )
            else:
                ret, ret_emb, detail = EntryStorage.save_entry(
                    entry, None
                )
        if ret:
            if entry.ctype is not None:
                if entry.status == "todo":
                    detail = _("set_to_pending_comma__type_colon__{ctype}").format(
                        ctype=entry.ctype
                    )
                else:
                    detail = _(
                        "collection_successful_comma__type_colon__{ctype}"
                    ).format(ctype=entry.ctype)
            if entry.meta.get("error"):
                detail = _(
                    "storage_successful_comma__found_url_exception_error_colon__{error}"
                ).format(error=entry.meta["error"])
        return ret, ret_emb, detail


def filter_model_fields(data):
    model_fields = {}
    for f in StoreEntry._meta.get_fields():
        max_length = getattr(f, "max_length", None)
        model_fields[f.name] = max_length

    filtered_data = {}
    for k, v in data.items():
        if k in model_fields:
            if isinstance(v, str) and model_fields[k] is not None:
                if len(v) > model_fields[k]:
                    logger.warning(
                        f"Field '{k}' value too long ({len(v)}), truncating to {model_fields[k]} chars"
                    )
                    v = v[: model_fields[k]]
            filtered_data[k] = v
    return filtered_data


def check_entry_exist(user_id, url, path):
    """
    Check if the data already exists in the database
    """
    return StoreEntry.objects.filter(
        user_id=user_id, addr=url, path=path, is_deleted="f"
    ).exists()


def regerate_embedding(uid, addr, emb_model):
    """
    Regenerate the embedding for the specified user and address
    call from app_sync
    """
    use_embedding = EmbeddingTools.use_embedding()
    entries = StoreEntry.objects.filter(user_id=uid, addr=addr)
    if len(entries) == 0 or not use_embedding:
        return False
    all_splits = [entry.raw for entry in entries]
    ret_emb, embeddings = EmbeddingTools.do_embedding(all_splits, True)
    if ret_emb:
        for entry, embedding in zip(entries, embeddings):
            entry.embeddings = embedding
            entry.emb_model = emb_model
            entry.save()
    return True


def get_path_by_title(uid, title):
    """
    Get the absolute path of the file according to the title
    """
    try:
        objs = StoreEntry.objects.filter(user_id=uid, title=title)
        if len(objs) > 0:
            obj = objs[0]
            info = eval(obj.info)
            if "path" in info:
                return info["path"]
    except Exception as e:
        logger.warning(f"get_path_by_title failed {e}")
    return None


def get_entry(idx):
    objs = StoreEntry.objects.filter(idx=idx)
    if len(objs) > 0:
        return objs[0]
    else:
        return None


def escape_regex(s):
    special_chars = r"[]()*+?.^$|{}\/"
    return "".join("\\" + c if c in special_chars else c for c in s)


def get_entry_list(keywords, query_args, max_count=-1, fields=None):
    query_args["block_id"] = 0
    query_args["is_deleted"] = False
    if fields is None:
        fields = [
            "idx",
            "block_id",
            "raw",
            "title",
            "etype",
            "atype",
            "ctype",
            "status",
            "addr",
            "path",
            "created_time",
            "updated_time",
        ]
    if keywords is not None and len(keywords) > 0:
        keywords = regular_keyword(keywords)
        keyword_arr = keywords.split(" ")
        escaped_keywords = escape_regex(keywords)
        escaped_keyword_arr = [escape_regex(k) for k in keyword_arr]

        queryset = StoreEntry.objects.filter(
            addr__iregex=escaped_keywords, **query_args
        ).values(*fields)

        if not queryset.exists():
            # find by title
            q_obj = Q()
            for keyword in escaped_keyword_arr:
                q_obj &= Q(title__iregex=keyword)
            queryset = StoreEntry.objects.filter(q_obj, **query_args).values(*fields)

        if not queryset.exists():
            # find by raw
            q_obj = Q()
            for keyword in escaped_keyword_arr:
                q_obj &= Q(raw__iregex=keyword)
            query_args_2 = query_args.copy()
            query_args_2.pop("block_id")
            queryset = StoreEntry.objects.filter(q_obj, **query_args_2).values(*fields)
            if queryset.exists():
                queryset = queryset.order_by("addr", "block_id").distinct("addr")

        if not queryset.exists():
            # find by title trigram
            queryset = (
                StoreEntry.objects.filter(**query_args)
                .annotate(
                    similarity=TrigramSimilarity("title", keywords),
                )
                .filter(similarity__gt=0.05)
                .order_by("-similarity")
                .values(*fields)
            )
    else:
        queryset = StoreEntry.objects.filter(**query_args).values(*fields)

    # Apply slicing only if max_count > 0
    if max_count > 0:
        queryset = queryset[:max_count]
    return queryset


def get_type_options(ctype):
    try:
        if (ctype != "all"):
            unique_values = StoreEntry.objects.values_list(
                ctype, flat=True
            ).distinct()  # pgsql not support distinct
            unique_values = list(set(unique_values))
            unique_values = [x for x in unique_values if x is not None and len(x) > 0]
            logger.debug(f"unique_values {unique_values}")
            return HttpResponse(json.dumps(unique_values))
        else:
            ret_dict = {}
            for field in ["ctype", "etype", "status"]:
                unique_values = StoreEntry.objects.values_list(
                    field, flat=True
                ).distinct()
                unique_values = list(set(unique_values))
                unique_values = [
                    x for x in unique_values if x is not None and len(x) > 0
                ]
                logger.debug(f"unique_values {unique_values}")
                ret_dict[field] = unique_values
            return HttpResponse(json.dumps(ret_dict))
    except Exception as e:
        logger.warning(f"record get failed {e}")
        return HttpResponse(json.dumps([]))


def get_file_content_by_path(path, user):
    meta_data = {}
    content = None
    ret_convert = False

    if converter.is_markdown(path):
        md_path = path
        ret_convert = True
    elif converter.is_support(path):
        md_path = filecache.get_tmpfile(".md")
        ret_convert, md_path = convert_to_md(
            path, md_path, force=True, use_ocr=user.privilege.b_ocr
        )
    logger.info("after convert")
    if ret_convert:
        parser = MarkdownParser(md_path)
        meta_data = parser.fm
        content = parser.content
    if content is None and is_plain_text(path):
        content = open(path, "r").read()
    return meta_data, content


def add_data(obj, data=None, use_llm=True):
    return EntryService.process_entry(obj, data, use_llm)


def delete_entry(uid, filelist):
    return EntryStorage.delete_entry(uid, filelist)
