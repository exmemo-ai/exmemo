from app_bm_syncex.views import SOURCE
from app_dataforge.models import StoreEntry

from .common import make_response
from .update_services import BookmarkUpdateService

def get_tree_bookmarks(query):
    """Get bookmarks for tree view"""
    return query.filter().values(
        'idx', 'title', 'addr', 'path', 'meta', 'is_deleted'
    ).order_by('path', 'title')


def update_tree_bookmark(request, bookmark):
    """Update bookmark in tree view"""
    return (BookmarkUpdateService(bookmark)
            .update_title(request.data.get('title'))
            .update_tags(request.data.get('tags'))
            .update_url(request.data.get('url'))
            .update_folder(request.data.get('folder'))
            .save())

def get_bookmark_folders(user_id):
    """Get all available bookmark folders"""
    folders = StoreEntry.objects.filter(
        user_id=user_id,
        source=SOURCE,
        is_deleted='f',
        status='collect'
    ).values_list('path', flat=True).distinct()
    
    base_prefix = 'chrome/书签栏/'
    processed_folders = []
    
    for folder in folders:
        if folder and folder.startswith(base_prefix):
            sub_path = folder.replace(base_prefix, '', 1)
            if sub_path:
                parent_folder = sub_path.rsplit('/', 1)[0]
                if parent_folder:
                    processed_folders.append(parent_folder)
                    
    processed_folders = sorted(set(processed_folders))
    
    return make_response(data=['/', *processed_folders])
