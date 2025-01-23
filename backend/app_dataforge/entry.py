"""
To handle file-related operations
"""

import os
import json
import pytz
import traceback
from loguru import logger
from django.utils import timezone
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpResponse
from django.utils.translation import gettext as _

from backend.common.files import utils_filemanager, filecache
from backend.common.utils.text_tools import convert_dic_to_json
from backend.common.utils.file_tools import is_plain_text, convert_to_md, get_file_abstract
from backend.common.utils.regular_tools import regular_keyword
from backend.common.utils.web_tools import get_url_content, get_web_abstract
from backend.common.parser import converter, utils_md
from backend.common.parser.md_parser import MarkdownParser
from backend.common.llm.llm_hub import EmbeddingTools
from backend.common.user.user import UserManager

from .models import StoreEntry
from .feature import EntryFeatureTool, DEFAULT_CATEGORY

DESC_LENGTH = 50
REL_DIR_FILES = "files"
REL_DIR_NOTES = "notes"
# get PARSE_CONTENT from backend env settings

def add_data(dic, path=None, use_llm=True):
    user = UserManager.get_instance().get_user(dic["user_id"])
    if dic.get("is_batch", False) and user.get("batch_use_llm") == False:
        use_llm = False
    #logger.debug(f'use_llm {use_llm} {dic.get("is_batch", False)} {user.get("batch_use_llm") == False}')
    """
    path is the temporary file path to be uploaded
    For the uploaded file, addr is the relative path for storage, under xxx/files/
    For ob notes, addr is the relative path for storage, under xxx/note/
    For web pages, addr is the URL
    For records, addr is the timestamp
    """

    if dic["etype"] == "file" or dic["etype"] == "note":
        return add_file(dic, path, use_llm=use_llm)
    elif dic["etype"] == "record":
        return add_record(dic, use_llm=use_llm)
    elif dic["etype"] == "chat":
        return add_chat(dic, use_llm=use_llm)
    elif dic["etype"] == "web":
        return add_web(dic, use_llm=use_llm)
    else:
        return False, False, _("unknown_type_colon_") + dic["etype"]

def add_chat(dic, use_llm=True):
    abstract = dic["abstract"]
    del dic["abstract"]
    return save_entry(dic, abstract, dic["raw"])

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
    logger.info('after convert')
    if ret_convert:
        parser = MarkdownParser(md_path)
        meta_data = convert_dic_to_json(parser.fm)
        content = parser.content
    if content is None and is_plain_text(path):
        content = open(path, "r").read()
    return meta_data, content

def add_file(dic, path, use_llm=True):
    mtime_datetime = timezone.now().astimezone(pytz.UTC)
    # logger.debug(f'save to serv {path}, {mtime_datetime}')

    user = UserManager.get_instance().get_user(dic["user_id"])
    filename = os.path.basename(dic["addr"])
    ret, dic = EntryFeatureTool.get_instance().parse(dic, filename, use_llm=use_llm)

    if dic["etype"] == "note":
        dic["path"] = os.path.join(REL_DIR_NOTES, dic["addr"])
    if dic["etype"] == "file":
        dic["path"] = os.path.join(REL_DIR_FILES, dic["addr"])
    ret = utils_filemanager.get_file_manager().save_file(
        dic["user_id"], dic["path"], path
    )
    if not ret:
        return False, False, _("save_file_failed_excl_")

    if "md5" not in dic or dic["md5"] is None:
        dic["md5"] = utils_md.get_file_md5(path)
    dic["created_time"] = mtime_datetime

    if (dic['etype'] == 'note' and user.get("note_save_content")) or (dic['etype'] == 'file' and user.get("file_save_content")):
        meta_data, content = get_file_content_by_path(path, user)
    elif converter.is_markdown(path):
        parser = MarkdownParser(path)
        meta_data = convert_dic_to_json(parser.fm)
        content = None
    else:
        meta_data = {}
        content = None
    dic["meta"] = meta_data

    if (dic['etype'] == 'note' and user.get("note_get_abstract")) or (dic['etype'] == 'file' and user.get("file_get_abstract")):
        abstract = get_file_abstract(dic["path"], dic["user_id"])
    else:
        abstract = None

    return save_entry(dic, abstract, content)


def filter_model_fields(data):
    model_fields = {}
    for f in StoreEntry._meta.get_fields():
        max_length = getattr(f, 'max_length', None)
        model_fields[f.name] = max_length

    filtered_data = {}
    for k, v in data.items():
        if k in model_fields:
            if isinstance(v, str) and model_fields[k] is not None:
                if len(v) > model_fields[k]:
                    logger.warning(f"Field '{k}' value too long ({len(v)}), truncating to {model_fields[k]} chars")
                    v = v[:model_fields[k]]
            filtered_data[k] = v         
    return filtered_data


def save_entry(dic, abstract, content, debug=False):
    use_embedding = EmbeddingTools.use_embedding()
    ret_emb = True
    try:
        if "addr" in dic and dic["addr"] is not None:
            StoreEntry.objects.filter(user_id=dic["user_id"], addr=dic["addr"]).delete()
        dic["block_id"] = 0
        dic["emb_model"] = EmbeddingTools.get_model_name(use_embedding)
        dic["raw"] = abstract
        if "created_time" not in dic:
            dic["created_time"] = timezone.now().astimezone(pytz.UTC)
        filtered_dic = filter_model_fields(dic)
        StoreEntry.objects.create(**filtered_dic)
        if content:
            all_splits = EmbeddingTools.split(content)
            if len(all_splits) == 0:
                all_splits = [content]
            if use_embedding == False:
                embeddings = [None for split in all_splits]
            else:
                ret_emb, embeddings = EmbeddingTools.do_embedding(
                    all_splits, use_embedding
                )
            if debug:
                logger.debug(
                    f"save to serv, split blocks {len(all_splits)}, emb {ret_emb}"
                )
            for idx, (text, emb) in enumerate(zip(all_splits, embeddings)):
                dic["block_id"] = idx + 1
                dic["raw"] = text
                if emb is not None:
                    dic["embeddings"] = emb
                elif "embeddings" in dic:
                    dic.pop("embeddings")
                filtered_dic = filter_model_fields(dic)
                StoreEntry.objects.create(**filtered_dic)
            logger.info(f'save blocks {idx}')
        return True, ret_emb, _("add_success")
    except Exception as e:
        traceback.print_exc()
        logger.warning(f"save to db failed {e}")
        return False, ret_emb, _("add_failed")


def check_entry_exist(user_id, url, path):
    """
    Check if the data already exists in the database
    """
    return StoreEntry.objects.filter(user_id=user_id, addr=url, path=path, is_deleted='f').exists()


def add_record(dic, use_llm=True):
    current_time = timezone.now().astimezone(pytz.UTC)
    dic["addr"] = f'record_{current_time.strftime("%Y%m%d_%H%M%S")}'
    ret, dic_new = EntryFeatureTool.get_instance().parse(
        dic, dic["raw"], use_llm=use_llm
    )
    ret, ret_emb, detail = save_entry(dic_new, dic["raw"], dic["raw"])
    if ret:
        if "ctype" in dic_new and dic_new["ctype"] is not None:
            detail = _("record_successful_comma__type_colon_") + dic_new["ctype"]
    return ret, ret_emb, detail


def add_web(dic, use_llm=True, debug=False):
    """
    Download the file from the URL, parse the file, and store the data from the file into the database;
    This only handles plain web pages, does not consider files
    """
    user = UserManager.get_instance().get_user(dic["user_id"])
    has_error = "error" in dic and dic["error"] is not None
    # if it's not bookmark, need_download to get title...
    need_download = dic["source"] != "bookmark" or user.get("bookmark_download_web") == True
    if has_error or not need_download:
        # insert to db directly
        dic['ctype'] = DEFAULT_CATEGORY # if it has ctype, will not download web content
        ret, dic = EntryFeatureTool.get_instance().parse(dic, dic["addr"], use_llm=False, debug=debug)
        ret, ret_emb, detail = save_entry(dic, None, None, debug=debug)
    else:
        if user.get("web_get_abstract"):
            abstract = get_web_abstract(dic['user_id'], dic["addr"])
        else:
            abstract = None
        ret, dic = EntryFeatureTool.get_instance().parse(dic, dic["addr"], use_llm=use_llm, debug=debug)
        if user.get("web_save_content"):
            title, content = get_url_content(dic["addr"])
            ret, ret_emb, detail = save_entry(dic, abstract, content)
        else:
            ret, ret_emb, detail = save_entry(dic, abstract, None)

    if ret:
        if "ctype" in dic and dic["ctype"] is not None:
            if "status" in dic and dic["status"] == "todo":
                detail = _("set_to_pending_comma__type_colon__{ctype}").format(ctype=dic["ctype"])
            else:
                detail = _("collection_successful_comma__type_colon__{ctype}").format(
                    ctype=dic["ctype"]
                )
        if dic.get("meta", {}).get("error"):
            detail = _("storage_successful_comma__found_url_exception_error_colon__{error}").format(
                error=dic["meta"]["error"]
            )        
    return ret, ret_emb, detail


def delete_entry(uid, filelist):
    """
    Delete the file permanently
    """
    logger.debug(f"real delete total {len(filelist)}")
    for item in filelist:
        addr = item["addr"]
        entrys = StoreEntry.objects.filter(user_id=uid, addr=addr)
        logger.warning(f"real delete {uid} addr {addr}, {entrys.count()}")
        for entry in entrys:
            if entry.block_id == 0:
                if entry.path is not None:
                    utils_filemanager.get_file_manager().delete_file(uid, entry.path)
                    logger.info(f"real delete server file {entry.path}")
                entry.is_deleted = True
                entry.updated_time = timezone.now().astimezone(pytz.UTC)
                entry.save()
            else:
                entry.delete()


def regerate_embedding(uid, addr, emb_model):
    use_embedding = EmbeddingTools.use_embedding()
    entrys = StoreEntry.objects.filter(user_id=uid, addr=addr)
    if len(entrys) == 0 or not use_embedding:
        return False
    all_splits = [entry.raw for entry in entrys]
    ret_emb, embeddings = EmbeddingTools.do_embedding(all_splits, True)
    if ret_emb:
        for entry, embedding in zip(entrys, embeddings):
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


def get_entry_list(keywords, query_args, max_count, fields = None):
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
        # find by title
        q_obj = Q()
        for keyword in keyword_arr:
            q_obj &= Q(title__iregex=keyword)
        queryset = StoreEntry.objects.filter(q_obj, **query_args).values(*fields)[:max_count]
        
        if len(queryset) == 0:
            # find by raw
            q_obj = Q()
            for keyword in keyword_arr:
                q_obj &= Q(raw__iregex=keyword)
            query_args_2 = query_args.copy()
            query_args_2.pop("block_id")
            queryset = StoreEntry.objects.filter(q_obj, **query_args_2).values(*fields)
            if len(queryset) > 0:
                queryset = queryset.order_by("addr", "block_id").distinct("addr")[:max_count]

        if len(queryset) == 0:
            # find by title trigram
            queryset = (
                StoreEntry.objects.filter(**query_args)
                .annotate(
                    similarity=TrigramSimilarity("title", keywords),
                )
                .filter(similarity__gt=0.05)
                .order_by("-similarity")[:max_count]
                .values(*fields)
            )
    else:
        queryset = StoreEntry.objects.filter(**query_args).values(*fields)[:max_count]
    return queryset


def get_type_options(ctype):
    try:
        unique_values = StoreEntry.objects.values_list(
            ctype, flat=True
        ).distinct()  # pgsql not support distinct
        unique_values = list(set(unique_values))
        unique_values = [x for x in unique_values if x is not None and len(x) > 0]
        logger.debug(f"unique_values {unique_values}")
        return HttpResponse(json.dumps(unique_values))
    except Exception as e:
        logger.warning(f"record get failed {e}")
        return HttpResponse(json.dumps([]))


def rename_file(uid, oldaddr, newaddr):
    instances = StoreEntry.objects.filter(addr=oldaddr)
    logger.debug(f"found instances {len(instances)}")
    oldpath = os.path.join(REL_DIR_FILES, oldaddr)
    newpath = os.path.join(REL_DIR_FILES, newaddr)
    ret = utils_filemanager.get_file_manager().rename_file(uid, oldpath, newpath)
    if ret:
        for item in instances:
            item.addr = newaddr
            item.path = newpath
            filename = os.path.basename(newpath)
            item.title = filename
            item.save()
        return True
    return False
