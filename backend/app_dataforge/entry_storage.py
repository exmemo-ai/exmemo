import pytz
import traceback
from typing import Optional
from loguru import logger
import numpy as np
from django.utils import timezone
from django.utils.translation import gettext as _

from backend.common.llm.llm_hub import EmbeddingTools
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
        logger.info(f"save {str(entry.to_dict())[:200]}")
        #logger.info(f"save {str(entry.to_dict())}")
        
        try:
            entry.updated_time = timezone.now().astimezone(pytz.UTC)
            
            ret_emb = True
            if entry.idx and StoreEntry.objects.filter(idx=entry.idx, block_id=0).exists():
                ret_emb = EntryStorage._update_entry(entry, has_new_content, content)
            else:
                ret_emb = EntryStorage._create_entry(entry, content)

            return (
                True, 
                ret_emb,
                _("update_success") if entry.idx else _("add_success")
            )
            
        except Exception as e:
            logger.error(f"save_entry failed: {str(e)}")
            traceback.print_exc()
            return False, False, _("add_failed")

    @staticmethod
    def _update_entry(entry: EntryItem, has_new_content: bool, content: Optional[str] = None):
        ret_emb = True
        if has_new_content:
            db_entry = StoreEntry.objects.get(idx=entry.idx) # block_id=0
            for key, value in entry.to_model_dict().items():
                setattr(db_entry, key, value)
            
            abstract = entry.meta.get("description") if entry.meta else None
            if abstract:
                need_new_embedding = (
                    db_entry.raw != abstract or
                    db_entry.embeddings is None or
                    len(db_entry.embeddings) == 0 or
                    db_entry.emb_model != EmbeddingTools.get_model_name()
                )
                
                db_entry.raw = abstract
                if EmbeddingTools.use_embedding() and need_new_embedding:
                    ret, embeddings = EmbeddingTools.do_embedding([abstract], True)
                    if ret:
                        db_entry.embeddings = embeddings[0]
                        db_entry.emb_model = EmbeddingTools.get_model_name()
            db_entry.save()
            if content:
                ret_emb = EntryStorage._save_content_blocks(entry, content)
        else: # 没有新文件上传/更新文件，只改属性值
            entries = StoreEntry.objects.filter(
                user_id=entry.user_id,
                addr=entry.addr
            )
            entry_dict = entry.to_model_dict()
            exclude_fields = ['idx', 'embeddings', 'emb_model', 'block_id', 'raw']
            for field in exclude_fields:
                entry_dict.pop(field, None)
            for db_entry in entries:
                for key, value in entry_dict.items():
                    if key != 'meta' or db_entry.block_id == 0:
                        setattr(db_entry, key, value)
                db_entry.save()
        return ret_emb

    @staticmethod 
    def _create_entry(entry: EntryItem, content: Optional[str] = None):
        ret_emb = True
        if entry.addr:
            StoreEntry.objects.filter(
                user_id=entry.user_id,
                addr=entry.addr
            ).delete()
            
        entry_dict = entry.to_model_dict()
        entry_dict['block_id'] = 0
        entry_dict['emb_model'] = EmbeddingTools.get_model_name()
        
        abstract = entry.meta.get("description") if entry.meta else None
        if abstract:
            entry_dict['raw'] = abstract
            if EmbeddingTools.use_embedding():
                ret, embeddings = EmbeddingTools.do_embedding([abstract], True)
                if ret:
                    entry_dict['embeddings'] = embeddings[0]
        StoreEntry.objects.create(**entry_dict)
        if content:
            ret_emb = EntryStorage._save_content_blocks(entry, content)
        return ret_emb

    @staticmethod
    def _save_content_blocks(entry: EntryItem, content: str, debug: bool=False) -> bool:
        existing_blocks = StoreEntry.objects.filter(
            user_id=entry.user_id,
            addr=entry.addr,
            block_id__gt=0
        ).order_by('block_id')
        
        has_existing = existing_blocks.count() > 0
        
        if not content:
            existing_blocks.delete()
            return True
            
        blocks = EmbeddingTools.split(content) or [content]
        
        if len(blocks) != (existing_blocks.count() if has_existing else 0):
            existing_blocks.delete()
            has_existing = False
        
        if not EmbeddingTools.use_embedding():
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
                        old_block.emb_model == EmbeddingTools.get_model_name()):
                        embeddings[i] = old_block.embeddings
                        continue
                
                blocks_need_embedding.append(block_text)
                embedding_indices.append(i)
            
            if len(blocks_need_embedding) > 0:
                ret, new_embeddings = EmbeddingTools.do_embedding(blocks_need_embedding, True)
                if debug:
                    logger.debug(f"embeddings {ret} {len(new_embeddings)}")
                if not ret:
                    return False
                    
                for idx, embedding in zip(embedding_indices, new_embeddings):
                    embeddings[idx] = embedding
                
        for i, (block_text, embedding) in enumerate(zip(blocks, embeddings)):
            block_entry = entry.clone(
                block_id=i+1,
                raw=block_text,
                embeddings=embedding,
                emb_model=EmbeddingTools.get_model_name() if embedding is not None else None,
                idx=None,
                meta=None
            )
            
            if has_existing:
                old_block = existing_blocks[i]
                for key, value in block_entry.to_model_dict().items():
                    if key not in ['idx', 'created_time']:
                        setattr(old_block, key, value)
                old_block.save()
            else:
                StoreEntry.objects.create(**block_entry.to_model_dict())
            
        return True

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