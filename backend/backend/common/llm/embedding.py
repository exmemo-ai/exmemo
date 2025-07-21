import os
import json
import hashlib
from typing import OrderedDict
from loguru import logger

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from django.utils.translation import gettext as _

from backend.common.user.user import *
from backend.common.user.resource import *

EMBEDDING_CHUNK_SIZE = 512

def _get_config_hash(config: dict) -> str:
    config_str = str(sorted(config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()[:8]

class EmbeddingManager:
    def __init__(self, max_cache_size: int = 10):
        self._user_embeddings: OrderedDict[str, 'EmbeddingTools'] = OrderedDict()
        self._max_cache_size = max_cache_size
    
    def get_embedding_tools(self, uid: str) -> 'EmbeddingTools':
        embedding_type, embedding_url, embedding_model, embedding_apikey = (
            EmbeddingTools.load_embedding_setting(uid)
        )
        
        config = {
            'type': embedding_type,
            'url': embedding_url,
            'model': embedding_model,
            'apikey': embedding_apikey
        }
        config_hash = _get_config_hash(config)
        cache_key = f"{uid}_{config_hash}"
        
        if cache_key in self._user_embeddings:
            self._user_embeddings.move_to_end(cache_key)
            return self._user_embeddings[cache_key]
        
        if len(self._user_embeddings) >= self._max_cache_size:
            oldest_key = next(iter(self._user_embeddings))
            removed_tools = self._user_embeddings.pop(oldest_key)
            logger.info(f"EmbeddingManager: Cache full, removing least recently used user config: {oldest_key}")
            
            if hasattr(removed_tools, 'model') and removed_tools.model is not None:
                try:
                    if hasattr(removed_tools.model, 'cleanup'):
                        removed_tools.model.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up embedding model resources: {e}")
        
        self._user_embeddings[cache_key] = EmbeddingTools(uid)
        self._user_embeddings[cache_key]._preset_config = config
        
        logger.info(f"EmbeddingManager: Created new embedding tools {cache_key}, current cache size: {len(self._user_embeddings)}")
        
        return self._user_embeddings[cache_key]
    
    def split(self, raw: str, chunk_size: int = EMBEDDING_CHUNK_SIZE, chunk_overlap: int = 50) -> list:
        return EmbeddingTools.split(raw, chunk_size, chunk_overlap)

    def get_model_name(self, uid: str) -> str:
        return self.get_embedding_tools(uid).get_model_name()    
    
    def use_embedding(self, uid: str) -> bool:
        return self.get_embedding_tools(uid).use_embedding()
    
    def get_embedding_scope(self, uid: str) -> str:
        return self.get_embedding_tools(uid).get_embedding_scope()
    
    def do_embedding(self, uid: str, all_splits: list, debug: bool = False) -> tuple:
        return self.get_embedding_tools(uid).do_embedding(all_splits, debug)
    
    def clear_user_cache(self, uid: str):
        keys_to_remove = [k for k in self._user_embeddings.keys() if k.startswith(f"{uid}_")]
        for key in keys_to_remove:
            removed_tools = self._user_embeddings.pop(key)
            logger.info(f"EmbeddingManager: Manually cleared user cache: {key}")
            
            if hasattr(removed_tools, 'model') and removed_tools.model is not None:
                try:
                    if hasattr(removed_tools.model, 'cleanup'):
                        removed_tools.model.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up embedding model resources: {e}")
    
    def clear_user_cache_on_setting_change(self, uid: str):
        logger.info(f"EmbeddingManager: User {uid} settings changed, clearing cache")
        self.clear_user_cache(uid)
    
embedding_manager = EmbeddingManager()

class EmbeddingTools:
    def __init__(self, uid: str = None):
        self.uid = uid
        self.model = None
        self._current_config = None
        self._preset_config = None

    @staticmethod
    def load_embedding_setting(uid: str = None):
        try:
            user = UserManager.get_instance().get_user(uid)
            embedding_model_setting = user.get('embedding_model', None)
            embedding_scope = user.get('embedding_scope', None)
            
            if embedding_model_setting:
                if isinstance(embedding_model_setting, str):
                    embedding_info = json.loads(embedding_model_setting)
                else:
                    embedding_info = embedding_model_setting
                embedding_type = embedding_info.get('type', 'none')
                embedding_url = embedding_info.get('url', None)
                embedding_model = embedding_info.get('model', None)
                embedding_apikey = embedding_info.get('apikey', None)
                
                if embedding_scope == 'none':
                    embedding_type = 'none'                
                return embedding_type, embedding_url, embedding_model, embedding_apikey
        except Exception as e:
            logger.warning(f"Failed to load user embedding settings: {e}")
    
        embedding_type = os.getenv("EMBEDDING_TYPE", "none")
        embedding_url = os.getenv("EMBEDDING_URL", None)
        embedding_model = os.getenv("EMBEDDING_MODEL", None)
        embedding_apikey = None
        return embedding_type, embedding_url, embedding_model, embedding_apikey

    def _load_embedding_setting(self):
        if self._preset_config:
            return (
                self._preset_config['type'],
                self._preset_config['url'], 
                self._preset_config['model'],
                self._preset_config['apikey']
            )
        return self.load_embedding_setting(self.uid)

    def get_model(self):
        embedding_type, embedding_url, embedding_model, embedding_apikey = self._load_embedding_setting()
        
        current_config = {
            'type': embedding_type,
            'url': embedding_url,
            'model': embedding_model,
            'apikey': embedding_apikey
        }
        config_hash = _get_config_hash(current_config)
        
        if self._current_config == config_hash and self.model is not None:
            return self.model
        
        if self._current_config != config_hash:
            logger.info(f"EmbeddingTools: Configuration changed, reloading model {embedding_type}:{embedding_model}")
        
        if embedding_type == "openai":
            openai_params = {}
            if embedding_url:
                openai_params['openai_api_base'] = embedding_url
            if embedding_apikey:
                openai_params['openai_api_key'] = embedding_apikey
            if embedding_model:
                openai_params['model'] = embedding_model
            
            self.model = OpenAIEmbeddings(**openai_params)
        elif embedding_type == "ollama":
            if (
                embedding_url is None
                or embedding_url == "none"
                or embedding_model is None
                or embedding_model == "none"
            ):
                self.model = None
            else:
                self.model = OllamaEmbeddings(base_url=embedding_url, model=embedding_model)
        else:  # None
            self.model = None
            
        self._current_config = config_hash
        return self.model
    
    def get_model_name(self):
        if not self.use_embedding():
            return None
        embedding_type, embedding_url, embedding_model, embedding_apikey = self._load_embedding_setting()
        if embedding_type == "none" or embedding_model == "none" or embedding_model is None:
            return None
        return embedding_model
    
    def get_embedding_scope(self):
        try:
            user = UserManager.get_instance().get_user(self.uid)
            embedding_scope = user.get('embedding_scope', None)
            if embedding_scope is not None:
                return embedding_scope
        except Exception as e:
            logger.warning(f"Failed to load user embedding scope setting: {e}")
        
        return 'none'
    
    @staticmethod
    def split(raw, chunk_size=EMBEDDING_CHUNK_SIZE, chunk_overlap=50):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(raw)

    def use_embedding(self):
        try:
            user = UserManager.get_instance().get_user(self.uid)
            embedding_scope = user.get('embedding_scope', None)
            if embedding_scope is not None and embedding_scope == 'none':
                return False
        except Exception as e:
            logger.warning(f"Failed to load user embedding scope setting: {e}")
        
        """
        val = os.getenv("USE_EMBEDDING", "False")
        if val.lower() != "true":
            return False
        """
        
        embedding_type, embedding_url, embedding_model, embedding_apikey = self._load_embedding_setting()
        
        if embedding_type is None or embedding_type == "none":
            return False
        
        if embedding_url is None or embedding_url == "" or embedding_url == "none":
            return False
        
        if embedding_model is None or embedding_model == "" or embedding_model == "none":
            return False
        
        if embedding_type == "openai":
            if embedding_apikey is None or embedding_apikey == "":
                return False
        
        return True
    
    def do_embedding(self, all_splits, debug=True):
        ret = False
        use_embedding = self.use_embedding()
        embeddings = []
        
        if debug:
            logger.info(f"before embedding use_embedding: {use_embedding}, all_splits: {len(all_splits)}")
            if len(all_splits) > 0:
                logger.info(f"first split: {all_splits[0][:100]}..., len: {len(all_splits[0])}")
                
        try:
            if not use_embedding:
                embeddings = [None for split in all_splits]
            else:
                model = self.get_model()
                if model is not None:
                    if debug:
                        logger.info(f"embedding block model {model} {len(all_splits)} splits")
                        for idx, split in enumerate(all_splits):
                            logger.info(f"split: {idx}, len: {len(split)}, {split[:50]}...")
                    embeddings = model.embed_documents(all_splits)
                    ret = True
                else:
                    embeddings = [None for split in all_splits]
                if debug:
                    logger.info(f"after embedding model {model} {len(embeddings)} splits")
        except Exception as e:
            logger.warning(f"embedding failed: {e}")
            embeddings = [None for split in all_splits]
        return ret, embeddings

