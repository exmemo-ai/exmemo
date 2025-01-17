from django.utils import timezone
from loguru import logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from backend.common.user.utils import parse_common_args
from app_dataforge.models import StoreEntry
from app_dataforge.entry import delete_entry

from .common import get_base_query, format_bookmarks, make_response, make_error_response
from .tree import get_tree_bookmarks, update_tree_bookmark, get_bookmark_folders
from .navigation import get_navigation_bookmarks, update_navigation_bookmark
from .search import search_bookmarks, update_search_bookmark
from .readlater import get_readlater_bookmarks, update_readlater_title_and_ctype, update_readlater_move

class BMKeeperAPIView(APIView):
    """Google Chrome Bookmark Synchronization API"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Handle GET requests"""
        args = parse_common_args(request)
        req_type = request.GET.get('type', '')
        param = request.GET.get('param', '')
        user_id = args['user_id']

        try:
            if 'folders' in request.path:
                return get_bookmark_folders(user_id)

            base_query = get_base_query(user_id)

            if req_type == 'tree':
                results = get_tree_bookmarks(base_query)
                return make_response(data=format_bookmarks(results, bookmark_type='tree'))
            elif req_type == 'navigation':
                limit = int(param) if param and param.isdigit() else 6
                custom_ids = request.GET.get('custom_ids')
                results = get_navigation_bookmarks(base_query, limit, custom_ids)
            elif req_type == 'search' and param:
                results = search_bookmarks(base_query, param)
            elif req_type == 'readlater':
                page = int(request.GET.get('page', 1))
                page_size = int(request.GET.get('page_size', 10))
                results, total = get_readlater_bookmarks(user_id, page, page_size)
                return make_response(
                    data=format_bookmarks(results),
                    total=total,
                    current_page=page,
                    page_size=page_size
                )
            elif req_type not in ['tree', 'navigation', 'search']:
                return make_error_response(400, "Invalid request type")

            return make_response(data=format_bookmarks(results))

        except Exception as e:
            logger.error(f"Error in BMKeeperAPIView: {str(e)}")
            return make_error_response(500, str(e))

    def put(self, request):
        """Handle PUT requests"""
        args = parse_common_args(request)
        req_type = request.data.get('type', 'tree')
        bookmark_id = request.data.get('id')
        
        try:
            logger.debug(f"PUT request data: {request.data}")
            
            bookmark = StoreEntry.objects.get(
                idx=bookmark_id,
                user_id=args['user_id'],
                is_deleted='f'
            )
            
            if req_type not in ['tree', 'navigation', 'search', 'readlater']:
                return make_error_response(400, "Invalid request type")

            # Update bookmark based on request type
            update_funcs = {
                'tree': update_tree_bookmark,
                'navigation': update_navigation_bookmark,
                'search': update_search_bookmark,
                'readlater': update_readlater_title_and_ctype
            }
            return update_funcs[req_type](request, bookmark)

        except StoreEntry.DoesNotExist:
            return make_error_response(404, "Bookmark not found")

    def post(self, request):
        """Handle POST requests"""
        args = parse_common_args(request)
        user_id = args['user_id']
        bookmark_id = request.data.get('id')
        
        try:
            bookmark = StoreEntry.objects.get(
                idx=bookmark_id,
                user_id=user_id,
                is_deleted='f'
            )
            if 'move' in request.path:
                bookmark = update_readlater_move(request, bookmark)
                return Response({"code": 200,
                                 "status": "success",
                                 "msg": "success",
                                 "data": {
                                     "id": bookmark.idx,
                                     "folder": bookmark.path}})

            action = request.data.get('action')
            if action == 'move':
                bookmark.status = 'collect'
                bookmark.folder = request.data.get('folder', '/')
                bookmark.save()
                
            return Response({"code": 200, "msg": "success"})

        except StoreEntry.DoesNotExist:
            return Response({"code": 404, "msg": "Bookmark not found"})
        except Exception as e:
            return Response({"code": 500, "msg": str(e)})

    def delete(self, request):
        """Handle DELETE requests"""
        args = parse_common_args(request)
        bookmark_id = request.query_params.get('id')
        
        try:
            bookmark = StoreEntry.objects.get(
                idx=bookmark_id,
                user_id=args['user_id'],
                is_deleted='f'
            )
            try:
                delete_entry(args['user_id'], [{'addr': bookmark.addr}])
                return make_response(data="Bookmark deleted successfully")
            except Exception as e:
                logger.error(f"Delete entry failed: {str(e)}")
                return make_error_response(500, str(e))

        except StoreEntry.DoesNotExist:
            return make_error_response(404, "Bookmark not found")
        except Exception as e:
            return make_error_response(500, str(e))