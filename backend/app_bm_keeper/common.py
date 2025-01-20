import re
from loguru import logger
from pathlib import Path
from django.utils import timezone
from rest_framework.response import Response

from app_dataforge.models import StoreEntry
from app_bm_syncex.views import SOURCE

def get_base_query(user_id, query_type='default'):
    """Enhanced base query builder supporting different query types"""
    base_conditions = {
        'user_id': user_id,
        'block_id': 0,
        'is_deleted': 'f'
    }
    
    if query_type == 'readlater':
        return StoreEntry.objects.filter(
            **base_conditions,
            etype='web',
            status='todo'
        )
    return StoreEntry.objects.filter(
        **base_conditions,
        source=SOURCE
    )

def remove_duplicates(bookmarks):
    """Remove duplicate bookmarks based on key attributes"""
    def get_key(item):
        if isinstance(item, dict):
            return (item.get('addr', ''), item.get('path', ''), 
                   item.get('title', ''), item.get('is_deleted', ''))
        return (getattr(item, 'addr', ''), getattr(item, 'path', ''),
                getattr(item, 'title', ''), getattr(item, 'is_deleted', ''))
    
    seen = set()
    unique_items = []
    for item in bookmarks:
        key = get_key(item)
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    return unique_items

def format_bookmarks(bookmarks, bookmark_type='default'):
    """Format bookmarks into serializable dictionary format
    """
    if bookmark_type == 'tree':
        return [{
            'id': bm['idx'],
            'title': bm['title'], 
            'url': bm['addr'],
            'folder': bm['path'],
            'is_deleted': bm['is_deleted'],
            'meta': bm['meta']
        } for bm in bookmarks]

    return [{
        'id': bookmark.idx,
        'title': bookmark.title,
        'url': bookmark.addr,
        'created_at': bookmark.created_time,
        'meta': bookmark.meta,
    } for bookmark in bookmarks]

def save_bookmark_changes(bookmark, changed_fields):
    """Save bookmark changes and return response"""
    if not changed_fields:
        return make_error_response(400, "No fields to update")
    changed_fields['updated_time'] = timezone.now()
    rows_updated = StoreEntry.objects.filter(idx=bookmark.idx).update(**changed_fields)
    bookmark.refresh_from_db()
    
    return make_response(data={
        "id": bookmark.idx,
        "title": bookmark.title,
        "url": bookmark.addr,
        "folder": bookmark.path,
        "tags": bookmark.ctype,
        "created_at": bookmark.created_time,
        "updated_time": bookmark.updated_time
    })

def make_response(data=None, code=200, msg="success", status="success", **kwargs):
    """create a success response object"""
    response = {
        "code": code,
        "status": status,
        "msg": msg
    }
    
    if data is not None:
        response["data"] = data
        
    response.update(kwargs)
    return Response(response)

def make_error_response(code, msg, status="error"):
    """Create an error response object"""
    return make_response(code=code, status=status, msg=msg)

class PathManager:
    """Manage all path related operations"""
    
    @staticmethod
    def get_chrome_prefix(base_path):
        """Get chrome prefix based on path content"""
        if base_path and ('bookmarks' in base_path.lower() or 'bookmark' in base_path.lower()):
            return 'chrome/bookmarkBar/'
        return 'chrome/书签栏/'

    @staticmethod
    def validate_path(path):
        """Validate path format"""
        return bool(re.match(r'^/?([^/]+/)*[^/]*$', str(path)))

    @staticmethod
    def clean_path(path):
        """Clean and normalize path"""
        if not path:
            return ''
        return re.sub(r'/{2,}', '/', path.lstrip('/'))

    @staticmethod
    def format_path_readlater(base_path, title, add_chrome_prefix=True):
        """Format path with optional chrome prefix for read later bookmarks"""
        base_path = PathManager.clean_path(base_path)
        
        if add_chrome_prefix:
            chrome_prefix = PathManager.get_chrome_prefix(base_path)
            return f"{chrome_prefix}{base_path}/{title}".rstrip('/')
        
        return f"{base_path}/{title}".rstrip('/')

    @staticmethod
    def validate_and_format_path(folder, title):
        """Validate and format bookmark path
        Args:
            folder: Folder path
            title: Bookmark title
        """
        if not isinstance(folder, str) or not isinstance(title, str):
            return make_error_response(400, "Invalid parameter types")
        
        if not title.strip():
            return make_error_response(400, "Title cannot be empty")

        clean_folder = PathManager.clean_path(folder)
        path = f"{clean_folder}/{title}"

        if not PathManager.validate_path(path):
            return make_error_response(400, "Invalid path format")
            
        return path

    @staticmethod
    def update_title_in_path(current_path, old_title, new_title):
        """Update path when title changes"""
        if not all(isinstance(x, str) for x in [current_path, old_title, new_title]):
            raise TypeError("All parameters must be strings")
            
        if current_path.endswith('/' + old_title):
            base_path = current_path[:-len(old_title)]
            return PathManager.validate_and_format_path(base_path.rstrip('/'), new_title)
            
        return current_path

    @staticmethod
    def update_bookmark_on_title_change(bookmark, new_title):
        """Update bookmark when title changes"""
        changed_fields = {'title': new_title}
        
        new_path = PathManager.update_title_in_path(
            bookmark.path,
            bookmark.title,
            new_title
        )
        
        if new_path != bookmark.path:
            changed_fields['path'] = new_path
        return changed_fields

    @staticmethod 
    def update_bookmark_metapath(bookmark, changed_fields):
        """Update bookmark meta when path changes"""
        if 'path' in changed_fields:
            meta = bookmark.meta.copy() if bookmark.meta else {}
            meta['update_path'] = changed_fields['path']
            changed_fields['meta'] = meta
        return changed_fields