from django.db.models import Case, When
from itertools import chain
from .update_services import BookmarkUpdateService

def get_navigation_bookmarks(query, limit=12, custom_ids=None):
    """Get bookmarks for navigation view"""
    bookmarks = query.filter(status='collect', is_deleted='f')
    
    if custom_ids:
        id_list = [int(id) for id in custom_ids.split(',') if id.isdigit()]
        if id_list:
            bookmarks = bookmarks.filter(
                idx__in=id_list,
                meta__contains={'custom_order': True}
            )
            preserved = Case(*[When(idx=pk, then=pos) for pos, pk in enumerate(id_list)])
            bookmarks = bookmarks.order_by(preserved)[:limit]
            return bookmarks
    
    custom_bookmarks = bookmarks.filter(meta__contains={'custom_order': True})
    remaining_limit = limit - custom_bookmarks.count()
    
    if remaining_limit > 0:
        other_bookmarks = bookmarks.exclude(
            meta__contains={'custom_order': True}
        ).order_by('-meta__weight')[:remaining_limit]
        results = list(chain(custom_bookmarks, other_bookmarks))
    else:
        results = custom_bookmarks[:limit]
        
    return results

def update_navigation_bookmark(request, bookmark):
    """Update bookmark in navigation view"""
    return (BookmarkUpdateService(bookmark)
        .update_title(request.data.get('title'))
        .save())
