from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from django.utils import timezone
import pytz
from .models import StoreEntry
from backend.common.utils.text_tools import convert_dic_to_json

@dataclass
class EntryItem:
    user_id: str
    etype: str
    
    addr: Optional[str] = None
    idx: uuid.UUID = field(default_factory=uuid.uuid4)
    block_id: int = 0
    title: Optional[str] = None
    raw: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    path: Optional[str] = None
    md5: Optional[str] = None
    
    ctype: Optional[str] = None
    atype: Optional[str] = 'subjective'
    status: Optional[str] = 'init'
    
    source: Optional[str] = None
    access_level: int = -1
    is_deleted: bool = False
    created_time: datetime = field(default_factory=lambda: timezone.now().astimezone(pytz.UTC))
    updated_time: datetime = field(default_factory=lambda: timezone.now().astimezone(pytz.UTC))
    
    embeddings: Optional[list] = None
    emb_model: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntryItem':
        filtered_data = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**filtered_data)
    
    @classmethod
    def from_model(cls, model: 'StoreEntry') -> 'EntryItem':
        return cls(**{
            k: getattr(model, k) 
            for k in cls.__dataclass_fields__ 
            if hasattr(model, k)
        })
    
    def to_dict(self) -> Dict[str, Any]:
        dic = {k: v for k, v in self.__dict__.items() if v is not None}
        #logger.error(f"dic {dic}")
        return dic
    
    def to_model_dict(self, for_json=False) -> Dict[str, Any]:
        model_fields = {}
        for f in StoreEntry._meta.get_fields():
            max_length = getattr(f, "max_length", None)
            model_fields[f.name] = max_length
        
        filtered_data = {}
        source_data = self.to_dict()
        for k, v in source_data.items():
            if k in model_fields:
                if isinstance(v, str) and model_fields[k] is not None:
                    if len(v) > model_fields[k]:
                        logger.warning(
                            f"Field '{k}' value too long ({len(v)}), truncating to {model_fields[k]} chars"
                        )
                        v = v[:model_fields[k]]
                if for_json:
                    if isinstance(v, uuid.UUID):
                        v = str(v)
                    elif isinstance(v, datetime):
                        v = v.isoformat()
                if k == 'meta' and isinstance(v, dict):
                    v = convert_dic_to_json(v)
                filtered_data[k] = v
        return filtered_data

    @classmethod
    def from_model(cls, model: 'StoreEntry') -> 'EntryItem':
        return cls(**{
            k: getattr(model, k) 
            for k in cls.__dataclass_fields__ 
            if hasattr(model, k)
        })
        
    def clone(self, **kwargs) -> 'EntryItem':
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)
