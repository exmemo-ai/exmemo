"""
To handle file-related operations
"""

import os
import json
import pytz
import re
from typing import Any
from loguru import logger
from django.utils import timezone
from django.db.models import Q, Case, When
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpResponse
from django.utils.translation import gettext as _
from pgvector.django import CosineDistance
from django.db.models.query import QuerySet

from backend.common.llm.embedding import embedding_manager
from backend.common.files import utils_filemanager, filecache
from backend.common.parser import converter, utils_md
from backend.common.parser.md_parser import MarkdownParser
from backend.common.utils.file_tools import is_plain_text, convert_to_md
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
# Get PARSE_CONTENT from backend env settings


class EmbeddingNotAvailableError(Exception):
    """Exception raised when embedding search is requested but not available"""
    pass


class EntryService:
    @staticmethod
    def _apply_meta_to_entry(entry: EntryItem, meta_dic: dict = None):
        if meta_dic is not None and isinstance(meta_dic, dict):
            entry.meta.update(meta_dic)
        
        # Apply metadata to entry fields (only if entry fields are None)
        if entry.meta.get("category") is not None and entry.ctype is None:
            entry.ctype = entry.meta["category"]
        if entry.meta.get("title") is not None and entry.title is None:
            entry.title = entry.meta["title"]
        if entry.meta.get("status") is not None and entry.status is None:
            entry.status = entry.meta["status"]
        if entry.meta.get("atype") is not None and entry.atype is None:
            entry.atype = entry.meta["atype"]
        
        if entry.atype is None:
            if entry.etype in ["note", "record", "chat"]:
                entry.atype = "subjective"
            elif entry.etype in ["file", "web"]:
                entry.atype = "third_party"
        
        if entry.status is None:
            entry.status = "collect"

    @staticmethod
    def process_entry(obj: dict | EntryItem, data=None, use_llm=True, debug=False):
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

        return handler(entry_item, data, use_llm, debug=debug)

    @staticmethod
    def _process_chat_entry(entry: EntryItem, data: Any, use_llm: bool = True, debug: bool = False):
        EntryService._apply_meta_to_entry(entry)
        
        # Default title and ctype exist at the same time
        if ((entry.ctype == DEFAULT_CATEGORY or entry.ctype is None) 
            and data is not None and 'reduce_msg' in data 
            and data['reduce_msg'] is not None and len(data['reduce_msg']) > 0):
            EntryFeatureTool.get_instance().parse(entry, data['reduce_msg'], use_llm=use_llm)
        if entry.title is None and data is not None and 'default_title' in data:
            entry.title = data['default_title']
        content = None
        if data is not None and 'content' in data:
            content = data['content']
        if content is None:
            has_new_content = False
        else:
            has_new_content = True
        return EntryStorage.save_entry(entry, content, has_new_content=has_new_content)


    @staticmethod
    def _process_record_entry(entry: EntryItem, data: Any, use_llm: bool = True, debug: bool = False):
        EntryService._apply_meta_to_entry(entry)
        
        current_time = timezone.now().astimezone(pytz.UTC)
        if entry.addr is None:
            entry.addr = f'record_{current_time.strftime("%Y%m%d_%H%M%S")}'
        content = None
        if data is not None and 'content' in data:
            content = data['content']
        ret = EntryFeatureTool.get_instance().parse(
            entry, content, use_llm=use_llm
        )
        if content is None:
            has_new_content = False
        else:
            has_new_content = True
        ret, ret_emb, detail = EntryStorage.save_entry(
            entry, content, has_new_content=has_new_content
        )
        if ret:
            if entry.ctype is not None:
                detail = _("record_successful_comma__type_colon_") + entry.ctype
        return ret, ret_emb, detail
    

    @staticmethod
    def _process_file_entry(entry: EntryItem, data: Any, use_llm: bool = True, debug: bool = False):
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

        need_feature_extraction = _should_extract_features(entry, user)
        if debug:
            logger.info(f"need_feature_extraction {need_feature_extraction}")
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

        EntryService._apply_meta_to_entry(entry, meta_dic)

        if need_feature_extraction:
            if content is None:
                ret = EntryFeatureTool.get_instance().parse(
                    entry, filename, use_llm=use_llm
                )
            else:
                entry.title = entry.title or filename
                ret = EntryFeatureTool.get_instance().parse(
                    entry, content, use_llm=use_llm
                )
        
        return EntryStorage.save_entry(entry, content, has_new_content, debug=debug)


    @staticmethod
    def _process_web_entry(entry: EntryItem, data: Any, use_llm: bool = True, debug: bool = False):
        """
        Download the file from the URL, parse the file, and store the data from the file into the database;
        This only handles plain web pages, does not consider files
        """
        EntryService._apply_meta_to_entry(entry)
        
        user = UserManager.get_instance().get_user(entry.user_id)
        has_error = (
            "error" in entry.meta 
            and entry.meta["error"] is not None
        )
        need_download = (
            entry.source != "bookmark" or user.get("bookmark_download_web") == True
        )
        if has_error or not need_download:
            entry.ctype = entry.ctype or DEFAULT_CATEGORY
            ret = EntryFeatureTool.get_instance().parse(
                entry, entry.addr, use_llm=False, debug=debug
            )
            if entry.path is None:
                entry.path = entry.title
            ret, ret_emb, detail = EntryStorage.save_entry(
                entry, None, has_new_content=False,
                debug=debug
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
                    entry, content, has_new_content=True, debug=debug
                )
            else:
                ret, ret_emb, detail = EntryStorage.save_entry(
                    entry, None, has_new_content=False, debug=debug
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
    entries = StoreEntry.objects.filter(user_id=uid, addr=addr)
    if len(entries) == 0 or not embedding_manager.use_embedding(uid):
        return False
    all_splits = [entry.raw for entry in entries]
    ret_emb, embeddings = embedding_manager.do_embedding(uid, all_splits)
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
    # 保证关键字中的特殊字符被正确转义，不被识别为正则表达式的特殊字符
    special_chars = r"[]()*+?.^$|{}\/"
    return "".join("\\" + c if c in special_chars else c for c in s)


class EntrySearchBuilder:
    
    @staticmethod
    def build_title_query(keyword_array, query_args, fields, case_sensitive=False):
        escaped_keyword_arr = [escape_regex(k) for k in keyword_array]
        query_args_title = query_args.copy()
        query_args_title["block_id"] = 0
        
        q_obj = Q()
        for keyword in escaped_keyword_arr:
            if case_sensitive:
                q_obj &= Q(title__regex=keyword)
            else:
                q_obj &= Q(title__iregex=keyword)
        
        return StoreEntry.objects.filter(q_obj, **query_args_title).values(*fields)

    @staticmethod
    def build_raw_content_query(keyword_array, query_args, fields, case_sensitive=False):
        escaped_keyword_arr = [escape_regex(k) for k in keyword_array]
        q_obj = Q()
        for keyword in escaped_keyword_arr:
            if case_sensitive:
                q_obj &= Q(raw__regex=keyword)
            else:
                q_obj &= Q(raw__iregex=keyword)
        
        return StoreEntry.objects.filter(q_obj, **query_args).values(*fields)

    @staticmethod
    def build_tag_query(keyword_array, query_args, fields, case_sensitive=False):
        q_obj = Q()
        for tag in keyword_array:
            escaped_tag = escape_regex(tag)
            logger.warning('Processing tag: {}'.format(escaped_tag))
            if case_sensitive:
                raw_query = Q(raw__regex=escaped_tag)
            else:
                raw_query = Q(raw__iregex=escaped_tag)
            if tag.startswith('#'):
                tag = tag[1:]
            meta_query = Q(meta__icontains=f'"{tag}"')
            q_obj &= (raw_query | meta_query)
        
        return (StoreEntry.objects.filter(q_obj, **query_args)
                .order_by('addr', 'block_id')
                .distinct('addr')
                .values(*fields))

    @staticmethod
    def build_embedding_query(keywords, query_args, fields):
        ret, query_vector = embedding_manager.do_embedding(query_args['user_id'], [keywords])
        if not ret or query_vector is None:
            return None
        
        current_model_name = embedding_manager.get_model_name(query_args['user_id'])
        if current_model_name is None:
            return None
        
        query_args_emb = query_args.copy()
        #query_args_emb["block_id"] = 0
        query_args_emb['embeddings__isnull'] = False
        query_args_emb['emb_model'] = current_model_name
        
        """
        queryset_with_similarity = StoreEntry.objects.filter(**query_args_emb).annotate(
            similarity=1 - CosineDistance('embeddings', query_vector[0])
        ).filter(
            similarity__gt=0.7
        ).order_by('-similarity').values(*fields, 'similarity')
        
        logger.info(f"Embedding search results for keywords '{keywords}':")
        for entry in queryset_with_similarity:
            logger.info(f"  Entry {entry.get('idx', 'N/A')}: {entry.get('title', 'N/A')} - Similarity: {entry['similarity']:.4f}")
        """
        return StoreEntry.objects.filter(**query_args_emb).annotate(
            similarity=1 - CosineDistance('embeddings', query_vector[0])
        ).filter(
            similarity__gt=0.7
        ).order_by('-similarity').values(*fields)

    @staticmethod
    def build_trigram_query(keywords, query_args, fields):
        return (
            StoreEntry.objects.filter(**query_args)
            .annotate(
                similarity=TrigramSimilarity("title", keywords),
            )
            .filter(similarity__gt=0.05)
            .order_by("-similarity")
            .values(*fields)
        )


class EntrySearchEngine:
    
    def __init__(self):
        self.builder = EntrySearchBuilder()
    
    @staticmethod
    def merge_querysets(all_querysets):
        all_entries = []
        seen_ids = set()
        
        for qs in all_querysets:
            if hasattr(qs, '__iter__'):
                for entry in qs:
                    if entry['idx'] not in seen_ids:
                        all_entries.append(entry)
                        seen_ids.add(entry['idx'])
        
        return all_entries

    @staticmethod
    def sort_and_deduplicate_by_addr(queryset):
        if len(queryset) == 0:
            return queryset
        
        seen_addrs = {}  # addr -> (entry, block_id)
        unique_entries = []
        
        for entry in queryset:
            addr = entry.get('addr', '')
            block_id = entry.get('block_id', 0)
            
            if addr not in seen_addrs:
                seen_addrs[addr] = (len(unique_entries), block_id)
                unique_entries.append(entry)
            else:
                existing_index, existing_block_id = seen_addrs[addr]
                if block_id < existing_block_id:
                    unique_entries[existing_index] = entry
                    seen_addrs[addr] = (existing_index, block_id)
        
        return unique_entries

    @staticmethod
    def apply_exclusion_filter(queryset, exclude):
        if not exclude or exclude.strip() == '':
            return queryset
        
        filtered_entries = []
        for entry in queryset:
            should_exclude = False
            
            if not should_exclude and 'path' in entry and entry['path']:
                if EntrySearchEngine.should_exclude_entry(entry['path'], exclude):
                    should_exclude = True
            
            if not should_exclude:
                filtered_entries.append(entry)
        
        return filtered_entries

    @staticmethod
    def should_exclude_entry(file_path, exclude_rules):
        """
        Check if an entry should be excluded based on exclude rules
        Similar to shouldExcludeFile function in search_local_data.ts
        """
        if not exclude_rules or exclude_rules.strip() == '':
            return False
        
        rules = [rule.strip() for rule in exclude_rules.split(',') if rule.strip() != '']
        
        for rule in rules:
            # Convert glob pattern to regex
            # Escape regex special characters except *
            regex_pattern = re.escape(rule).replace(r'\*', '.*')
            
            try:
                regex = re.compile(f'^{regex_pattern}$')
                
                # Check if complete path matches
                if regex.match(file_path):
                    return True
                
                # Check if any part of the path matches
                path_parts = file_path.split('/')
                for part in path_parts:
                    if regex.match(part):
                        return True
                
                # Check if any directory level relative path matches
                for i in range(len(path_parts)):
                    partial_path = '/'.join(path_parts[i:])
                    if regex.match(partial_path):
                        return True
                        
            except re.error:
                # If regex compilation fails, skip this rule
                continue
        
        return False
    
    @staticmethod
    def parse_search_input(keyword):
        """
        Parse search input to determine search type and extract keywords
        Similar to parseSearchInput function in TypeScript
        """
        search_type = 'keyword'
        search_value = keyword
        keyword_array = []
        
        if keyword.startswith('tag:'):
            search_type = 'tag'
            search_value = keyword[4:].strip()
            
            # Split tag terms and format them
            tag_terms = search_value.split()
            for term in tag_terms:
                if term:
                    formatted_tag = term if term.startswith('#') else '#' + term
                    keyword_array.append(formatted_tag)
            
            if not keyword_array and search_value.strip():
                tag_value = search_value.strip()
                formatted_tag = tag_value if tag_value.startswith('#') else '#' + tag_value
                keyword_array.append(formatted_tag)
                
        elif keyword.startswith('file:'):
            search_type = 'file'
            search_value = keyword[5:].strip()
            keyword_array = [search_value] if search_value else []
            
        else:
            search_type = 'keyword'
            search_value = keyword
            # Parse keywords similar to parseKeywords function
            keyword_array = EntrySearchEngine.parse_keywords(search_value)
        
        # Filter out empty keywords
        keyword_array = [kw.strip() for kw in keyword_array if kw.strip()]
        
        return {
            'search_type': search_type,
            'search_value': search_value,
            'keyword_array': keyword_array
        }

    @staticmethod
    def parse_keywords(search_value):
        """
        Parse keywords from search value, handling quoted phrases
        Similar to parseKeywords function in TypeScript
        """
        keyword_array = []
        # Match phrases in quotes and words outside quotes
        regex = r'"([^"]+)"|(\S+)'
        matches = re.findall(regex, search_value)
        
        for match in matches:
            term = match[0] or match[1]  # quoted phrase or single word
            if term and term.strip():
                keyword_array.append(term.strip())
        
        # logger.error(f"Parsed keywords: {keyword_array}")
        return keyword_array
    

    def execute_keyword_search(self, keyword_array, keywords, query_args, fields, max_count, method, 
                               case_sensitive=False, debug=False):
        #debug = True
        all_querysets = []
        
        if debug:
            logger.debug(f"Executing keyword search with keywords: {keywords}, method: {method}, max_count: {max_count}, query_args: {query_args}")

        # 1. Title search
        title_queryset = self.builder.build_title_query(keyword_array, query_args, fields, case_sensitive)
        all_querysets.append(title_queryset)
        if debug:
            logger.debug(f"title search count {title_queryset.count()}")
        
        # 2. Raw content search (if results are insufficient)
        if max_count == -1 or title_queryset.count() < max_count:
            raw_queryset = self.builder.build_raw_content_query(keyword_array, query_args, fields, case_sensitive)
            all_querysets.append(raw_queryset)
            if debug:
                logger.debug(f"raw search count after title search {raw_queryset.count()}")
        
        # 3. Vector search (if enabled and results are insufficient)
        current_count = sum(qs.count() for qs in all_querysets)
        if ((max_count == -1 or current_count < max_count) and 
            method == "embeddingSearch" and embedding_manager.use_embedding(query_args['user_id'])):
            embedding_queryset = self.builder.build_embedding_query(keywords, query_args, fields)
            if embedding_queryset is not None:
                all_querysets.append(embedding_queryset)
                logger.debug(f"added embedding search {embedding_queryset.count()}")
        
        # 4. Fuzzy search (if enabled and results are insufficient)
        current_count = sum(qs.count() for qs in all_querysets)
        if ((max_count == -1 or current_count < max_count) and 
            (method == "fuzzySearch" or method == "auto")):
            trigram_queryset = self.builder.build_trigram_query(keywords, query_args, fields)
            all_querysets.append(trigram_queryset)
            if debug:
                logger.debug(f"trigram search count {trigram_queryset.count()}")
        
        queryset = self.merge_querysets(all_querysets)        
        queryset = self.sort_and_deduplicate_by_addr(queryset)
        if debug:
            logger.debug(f"final count {len(queryset)}")
        
        return queryset
    
    def search(self, keywords, query_args, max_count=-1, fields=None, method="auto", exclude=None, case_sensitive=False, debug=False):
        query_args["is_deleted"] = False
        if fields is None:
            fields = [
                "idx", "block_id", "raw", "title", "etype", "atype", "ctype",
                "status", "addr", "path", "created_time", "updated_time",
            ]
        
        if keywords is not None and len(keywords) > 0:
            keywords = regular_keyword(keywords)
            # Parse search input to determine search type
            parsed_input = EntrySearchEngine.parse_search_input(keywords)
            search_type = parsed_input['search_type']
            keyword_array = parsed_input['keyword_array']
            
            if not keyword_array:
                return []

            if method == "embeddingSearch" and not embedding_manager.use_embedding(query_args['user_id']):
                raise EmbeddingNotAvailableError(_("Embedding search is not available. Please enable embedding in system settings."))

            # logger.error(f"method {method} keywords {keywords} search_type {search_type}")
            
            # Handle different search types
            if search_type == 'tag':
                queryset = self.builder.build_tag_query(keyword_array, query_args, fields, case_sensitive)
                # logger.error(f"tag search count {queryset.count()}")
            elif search_type == 'file':
                query_args['block_id'] = 0
                queryset = self.builder.build_title_query(keyword_array, query_args, fields, case_sensitive)
                # logger.error(f"file search count {queryset.count()}")
            else:  # keyword search
                queryset = self.execute_keyword_search(
                    keyword_array, keywords, query_args, fields, max_count, method, case_sensitive, debug
                )

            # Apply exclude logic if provided
            queryset = self.apply_exclusion_filter(queryset, exclude)
        else:
            query_args['block_id'] = 0
            queryset = StoreEntry.objects.filter(**query_args).values(*fields)
        
        # Apply slicing only if max_count > 0
        if max_count > 0:
            queryset = queryset[:max_count]
            
        return queryset


def get_entry_list(keywords, query_args, max_count=-1, fields=None, method="auto", exclude=None, case_sensitive = False, debug=False):
    search_engine = EntrySearchEngine()
    result_list = search_engine.search(keywords, query_args, max_count, fields, method, exclude, case_sensitive, debug)

    if isinstance(result_list, QuerySet):
        return result_list
    elif isinstance(result_list, list) and len(result_list) > 0:
        idx_list = [item['idx'] for item in result_list if 'idx' in item]
        if idx_list:
            preserved_order = Case(*[When(idx=pk, then=pos) for pos, pk in enumerate(idx_list)])
            return StoreEntry.objects.filter(idx__in=idx_list).order_by(preserved_order)
    return StoreEntry.objects.none()

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


def get_file_content_by_path(path, user, debug=False):
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
    if debug:
        logger.info("after convert")
    if ret_convert:
        parser = MarkdownParser(md_path)
        meta_data = parser.fm
        content = parser.content
    if content is None and is_plain_text(path):
        content = open(path, "r").read()
    return meta_data, content


def add_data(obj, data=None, use_llm=True, debug=False):
    return EntryService.process_entry(obj, data, use_llm, debug=debug)


def delete_entry(uid, filelist):
    return EntryStorage.delete_entry(uid, filelist)


def _should_extract_features(entry: EntryItem, user) -> bool:
    existing_entry = None
    
    if entry.idx:
        try:
            existing_entry = StoreEntry.objects.get(idx=entry.idx, block_id=0)
        except StoreEntry.DoesNotExist:
            pass
    
    if not existing_entry and entry.addr:
        try:
            existing_entry = StoreEntry.objects.filter(
                user_id=entry.user_id, 
                addr=entry.addr, 
                block_id=0,
                is_deleted=False
            ).first()
        except Exception:
            pass
    
    if entry.idx is None and not existing_entry:
        return True
    
    if existing_entry:
        if isinstance(existing_entry.meta, str):
            try:
                existing_entry.meta = json.loads(existing_entry.meta)
            except json.JSONDecodeError:
                existing_entry.meta = {}
        if _check_features_complete(existing_entry, user):
            _copy_features_from_existing(entry, existing_entry)
            return False
        else:
            return True
    
    return True

def _check_features_complete(entry, user) -> bool:
    if not entry.ctype or not entry.title:
        return False
    
    needs_description = (
        (entry.etype == "note" and user.get("note_get_abstract")) or
        (entry.etype == "file" and user.get("file_get_abstract"))
    )
    
    if needs_description:
        meta = getattr(entry, 'meta', None) or {}
        if not meta.get("description"):
            return False
    
    return True


def _copy_features_from_existing(entry: EntryItem, existing_entry) -> None:
    entry.ctype = entry.ctype or existing_entry.ctype
    entry.status = entry.status or existing_entry.status
    entry.atype = entry.atype or existing_entry.atype
    entry.title = entry.title or existing_entry.title
    
    if existing_entry.meta:
        existing_meta = existing_entry.meta
        if existing_meta.get("description") and not entry.meta.get("description"):
            entry.meta["description"] = existing_meta["description"]
