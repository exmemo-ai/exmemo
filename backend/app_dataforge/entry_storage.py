import pytz
import traceback
from typing import Optional
from loguru import logger
import numpy as np
from django.utils import timezone
from django.utils.translation import gettext as _

from backend.common.llm.embedding import embedding_manager
from backend.common.files import utils_filemanager
from .models import StoreEntry
from .entry_item import EntryItem

class EntryStorage:

    @staticmethod 
    def save_entry(
        entry: EntryItem,
        content: Optional[str] = None,
        has_new_content: bool = True,
        debug: bool = False
    ) -> tuple:        
        try:
            entry.updated_time = timezone.now().astimezone(pytz.UTC)
            if debug:
                logger.info(f"save {str(entry.to_dict())[:200]} ... {entry.updated_time}")
            #logger.info(f"save {str(entry.to_dict())}")

            db_entry = None
            operation = _("add_success")
            
            if entry.idx:
                try:
                    db_entry = StoreEntry.objects.get(idx=entry.idx, block_id=0)
                    operation = _("update_success")
                except StoreEntry.DoesNotExist:
                    pass
            
            if db_entry is None and entry.addr:
                try:
                    db_entry = StoreEntry.objects.filter(user_id=entry.user_id, addr=entry.addr, block_id=0).first()
                    if db_entry:
                        entry.idx = db_entry.idx
                        operation = _("update_success")
                except Exception:
                    pass
            
            if db_entry:
                ret_emb = EntryStorage._update_entry(entry, has_new_content, content, debug=debug)
            else:
                ret_emb = EntryStorage._create_entry(entry, content, debug=debug)
            
            return True, ret_emb, operation
            
        except Exception as e:
            logger.error(f"save_entry failed: {str(e)}")
            traceback.print_exc()
            return False, False, _("add_failed")

    @staticmethod
    def _update_entry(entry: EntryItem, has_new_content: bool, content: Optional[str] = None, debug: bool = False):
        ret_emb = True
        if has_new_content:
            db_entry = StoreEntry.objects.get(idx=entry.idx) # block_id=0
            exclude_fields = ['created_time']
            EntryStorage._update_db_entry_fields(db_entry, entry.to_model_dict(), exclude_fields, debug=debug)
            
            abstract = entry.meta.get("description") if entry.meta else None
            if abstract:
                need_new_embedding = (
                    db_entry.raw != abstract or
                    db_entry.embeddings is None or
                    len(db_entry.embeddings) == 0 or
                    db_entry.emb_model != embedding_manager.get_model_name(entry.user_id)
                )
                
                db_entry.raw = abstract
                embedding_scope = embedding_manager.get_embedding_scope(entry.user_id)
                if embedding_scope != 'none' and need_new_embedding:
                    ret, embeddings = embedding_manager.do_embedding(entry.user_id, [abstract])
                    if ret:
                        db_entry.embeddings = embeddings[0]
                        db_entry.emb_model = embedding_manager.get_model_name(entry.user_id)
                    else:
                        db_entry.embeddings = None
                        db_entry.emb_model = None
                        ret_emb = False
                        logger.warning(f"embedding failed for user {entry.user_id}, will continue with empty embeddings")
            if debug:
                logger.info(f"update entry {entry.idx} {entry.addr} {entry.etype} {entry.user_id} {db_entry.raw[:100]}")
            db_entry.save()
            if content:
                ret_emb = EntryStorage._save_content_blocks(entry, content, debug=debug)
        else: # 没有新文件上传/更新文件，只改属性值
            entries = StoreEntry.objects.filter(
                user_id=entry.user_id,
                addr=entry.addr
            )
            entry_dict = entry.to_model_dict()
            exclude_fields = ['idx', 'embeddings', 'emb_model', 'block_id', 'raw', 'created_time']
            for field in exclude_fields:
                entry_dict.pop(field, None)
            for db_entry in entries:
                EntryStorage._update_db_entry_fields(
                    db_entry, 
                    entry_dict, 
                    exclude_fields=[], 
                    update_meta_condition=(db_entry.block_id == 0),
                    debug=debug
                )
                db_entry.save()
        return ret_emb

    @staticmethod 
    def _create_entry(entry: EntryItem, content: Optional[str] = None, debug: bool = False):
        ret_emb = True
            
        entry_dict = entry.to_model_dict()
        entry_dict['block_id'] = 0
        entry_dict['emb_model'] = embedding_manager.get_model_name(entry.user_id)
        
        abstract = entry.meta.get("description") if entry.meta else None
        if abstract:
            entry_dict['raw'] = abstract
            embedding_scope = embedding_manager.get_embedding_scope(entry.user_id)
            if embedding_scope != 'none':
                ret, embeddings = embedding_manager.do_embedding(entry.user_id, [abstract])
                if ret:
                    entry_dict['embeddings'] = embeddings[0]
                else:
                    entry_dict['embeddings'] = None
                    entry_dict['emb_model'] = None
                    ret_emb = False
                    logger.warning(f"embedding failed for user {entry.user_id}, will continue with empty embeddings")
        StoreEntry.objects.create(**entry_dict)
        if content:
            ret_emb = EntryStorage._save_content_blocks(entry, content, debug=debug)
        return ret_emb

    @staticmethod
    def _save_content_blocks(entry: EntryItem, content: str, debug: bool=False) -> bool:
        ret = True
        existing_blocks = StoreEntry.objects.filter(
            user_id=entry.user_id,
            addr=entry.addr,
            block_id__gt=0
        ).order_by('block_id')
        
        has_existing = existing_blocks.count() > 0
        
        if not content:
            existing_blocks.delete()
            return ret
            
        blocks = embedding_manager.split(content) or [content]
        
        if len(blocks) != (existing_blocks.count() if has_existing else 0):
            existing_blocks.delete()
            has_existing = False
        
        embedding_scope = embedding_manager.get_embedding_scope(entry.user_id)
        if embedding_scope != 'all':
            embeddings = []
            for i, block_text in enumerate(blocks):
                if has_existing:
                    old_block = existing_blocks[i]
                    embeddings.append(old_block.embeddings if old_block.raw == block_text else None)
                else:
                    embeddings.append(None)
        else:
            embeddings = []
            blocks_need_embedding = []
            embedding_indices = []
            
            for i, block_text in enumerate(blocks):
                embeddings.append(None)
                if has_existing:
                    old_block = existing_blocks[i]
                    if (safe_equals(old_block.raw, block_text) and 
                        old_block.embeddings is not None and 
                        old_block.emb_model == embedding_manager.get_model_name(entry.user_id)):
                        embeddings[i] = old_block.embeddings
                        continue
                
                blocks_need_embedding.append(block_text)
                embedding_indices.append(i) # 只更新不一样的块
            
            if len(blocks_need_embedding) > 0:
                batch_size = 100
                for batch_start in range(0, len(blocks_need_embedding), batch_size):
                    batch_end = min(batch_start + batch_size, len(blocks_need_embedding))
                    batch_blocks = blocks_need_embedding[batch_start:batch_end]
                    batch_indices = embedding_indices[batch_start:batch_end]
                    
                    ret, batch_embeddings = embedding_manager.do_embedding(entry.user_id, batch_blocks)
                    if debug:
                        logger.debug(f"batch {batch_start//batch_size + 1} embeddings {ret} {len(batch_embeddings)}")
                    
                    if ret:
                        for idx, embedding in zip(batch_indices, batch_embeddings):
                            embeddings[idx] = embedding
                    else:
                        for idx in batch_indices:
                            embeddings[idx] = None
                        logger.warning(f"embedding failed for user {entry.user_id}, batch {batch_start//batch_size + 1}, will continue with empty embeddings for this batch")
                
                successful_embeddings = sum(1 for emb in embeddings if emb is not None)
                if debug:
                    logger.info(f"Successfully embedded {successful_embeddings} out of {len(blocks)} blocks for user {entry.user_id}")
                if successful_embeddings == 0:
                    ret = False
                    logger.warning(f"No embeddings were created for user {entry.user_id}, check embedding service or model configuration")
                
        for i, (block_text, embedding) in enumerate(zip(blocks, embeddings)):
            block_entry = entry.clone(
                block_id=i+1,
                raw=block_text,
                embeddings=embedding,
                emb_model=embedding_manager.get_model_name(entry.user_id) if embedding is not None else None,
                idx=None,
                meta=None
            )
            
            if has_existing:
                old_block = existing_blocks[i]
                for key, value in block_entry.to_model_dict().items():
                    if key not in ['idx', 'created_time']:
                        setattr(old_block, key, value)
                if embedding is None: # if embedding is None, not in key/value
                    setattr(old_block, 'embeddings', None)
                    setattr(old_block, 'emb_model', None)
                old_block.save()
            else:
                StoreEntry.objects.create(**block_entry.to_model_dict())
            
        return ret

    @staticmethod
    def get_content(user_id: str, addr: str) -> str:
        blocks = StoreEntry.objects.filter(
            user_id=user_id,
            addr=addr,
            block_id__gt=0
        ).order_by('block_id')
        
        if blocks.exists():
            return "".join(block.raw for block in blocks)
        return ""

    @staticmethod
    def delete_entry(uid, filelist):
        logger.debug(f"real delete total {len(filelist)}")
        for item in filelist:
            addr = item["addr"]
            filter_args = {"user_id": uid, "addr": addr}
            if "etype" in item:
                filter_args["etype"] = item["etype"]
            entrys = StoreEntry.objects.filter(**filter_args)
            logger.warning(f"real delete {uid} addr {addr}, {entrys.count()}")
            for entry in entrys:
                if entry.block_id == 0:
                    if entry.path is not None:
                        utils_filemanager.get_file_manager().delete_file(
                            uid, entry.path
                        )
                        logger.info(f"real delete server file {entry.path}")
                    entry.is_deleted = True
                    entry.updated_time = timezone.now().astimezone(pytz.UTC)
                    entry.save()
                else:
                    entry.delete()

    @staticmethod
    def _update_db_entry_fields(db_entry, entry_dict, exclude_fields=None, update_meta_condition=True, debug=False):
        if exclude_fields is None:
            exclude_fields = []
            
        for key, value in entry_dict.items():
            if key not in exclude_fields:
                if key == 'meta':
                    if update_meta_condition:
                        if db_entry.meta and value:
                            db_entry.meta.update(value)
                        elif value:
                            db_entry.meta = value
                        if debug:
                            logger.debug(f"Updated meta for {db_entry.idx}: {db_entry.meta}")
                else:
                    setattr(db_entry, key, value)

def safe_equals(a, b) -> bool:
    try:
        def normalize(value):
            if value is None:
                return ""
            if isinstance(value, np.ndarray):
                return str(value.tolist()).strip()
            if hasattr(value, 'tolist'):
                return str(value.tolist()).strip()
            if isinstance(value, (list, tuple)):
                return str(list(value)).strip()
            return str(value).strip()
            
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            return np.array_equal(a, b)
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return a == b
            
        return normalize(a) == normalize(b)
    except Exception as e:
        logger.error(f"Error comparing values: {str(e)}")
        return False