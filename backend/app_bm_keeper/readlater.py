from .common import get_base_query, remove_duplicates
from .update_services import BookmarkUpdateService

def get_readlater_bookmarks(user_id, page=1, page_size=10):
    """Get bookmarks for read later view with pagination"""
    query = get_base_query(user_id, query_type='readlater')
    
    all_bookmarks = list(query.order_by('-created_time'))
    unique_bookmarks = remove_duplicates(all_bookmarks)
    
    total = len(unique_bookmarks)
    start = (page - 1) * page_size
    results = unique_bookmarks[start:start + page_size]

    return results, total

def update_readlater_title_and_ctype(request, bookmark):
    """Update bookmark title and tags in read later view"""
    return (BookmarkUpdateService(bookmark)
            .update_title(request.data.get('title'))
            .update_tags(request.data.get('tags'))
            .save())

def update_readlater_move(request, bookmark):
    """Move read later bookmark to a different folder"""
    return (BookmarkUpdateService(bookmark)
            .update_folder(request.data.get('folder'), type='readlater')
            .save())
