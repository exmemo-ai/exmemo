from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from loguru import logger

from backend.common.user.utils import parse_common_args
from app_dataforge.models import StoreEntry
from app_bm_syncex.views import SOURCE
from .common import make_response, make_error_response

class BookmarkCustomOrderAPIView(APIView):
    """Custom ordering for bookmarks"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get custom order bookmarks"""
        args = parse_common_args(request)
        try:
            custom_bookmarks = StoreEntry.objects.filter(
                user_id=args['user_id'],
                source=SOURCE,
                is_deleted='f',
                meta__custom_order=True
            ).order_by('-created_time')
            
            results = [{
                'id': bm.idx,
                'title': bm.title,
                'url': bm.addr,
                'created_at': bm.created_time,
                'meta': bm.meta
            } for bm in custom_bookmarks]
            
            return make_response(data=results)
            
        except Exception as e:
            logger.error(f"Error fetching custom bookmarks: {e!r}")
            return make_error_response(500, str(e))

    def post(self, request):
        """Post the custom order"""
        args = parse_common_args(request)
        is_single_bookmark = request.data.get('singleBookmark', False)
        remove_id = request.data.get('removeId')
        
        try:
            if remove_id:
                bookmark = StoreEntry.objects.get(
                    user_id=args['user_id'],
                    idx=remove_id,
                    is_deleted='f'
                )
                meta = bookmark.meta if bookmark.meta else {}
                meta['custom_order'] = False  # set custom_order to False, remove from custom order
                bookmark.meta = meta
                bookmark.save()
                
                return make_response(
                    msg=f"Bookmark {remove_id} custom_order has been set to False"
                )
                
            elif is_single_bookmark:
                bookmark_id = request.data.get('bookmarkId')
                if not bookmark_id:
                    return make_error_response(
                        400, 
                        "bookmarkId is required for single bookmark update"
                    )
                
                bookmark = StoreEntry.objects.get(
                    user_id=args['user_id'],
                    idx=bookmark_id,
                    is_deleted='f'
                )
                
                meta = bookmark.meta if bookmark.meta else {}
                meta['custom_order'] = True
                bookmark.meta = meta
                bookmark.save()
                
                return make_response(
                    msg=f"Custom order updated for bookmark {bookmark_id}"
                )

        except StoreEntry.DoesNotExist:
            return make_error_response(404, "Bookmark not found")
        except Exception as e:
            logger.error(f"Error updating custom order: {str(e)}")
            return make_error_response(500, str(e))