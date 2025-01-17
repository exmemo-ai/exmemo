from django.db.models import Q
from .common import save_bookmark_changes

def search_bookmarks(query, keyword):
    """Search bookmarks by keyword"""
    return query.filter(
        Q(title__icontains=keyword) | 
        Q(addr__icontains=keyword) |
        Q(ctype__icontains=keyword)
    ).order_by('-created_time')

def update_search_bookmark(request, bookmark):
    """Update bookmark in search view"""
    changed_fields = {}
    
    if title := request.data.get('title'):
        changed_fields['title'] = title
    if url := request.data.get('url'):
        changed_fields['addr'] = url
    if (tags := request.data.get('tags')) is not None:
        changed_fields['ctype'] = tags
            
    return save_bookmark_changes(bookmark, changed_fields)
