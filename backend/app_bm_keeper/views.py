from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from datetime import timedelta
import random
import json
from loguru import logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from backend.common.user.utils import parse_common_args
from rest_framework.response import Response
from app_dataforge.entry import check_entry_exist
from app_dataforge.views import delete_entry
from app_dataforge.misc_tools import add_url
from app_dataforge.models import StoreEntry
from django.core.validators import ValidationError
import re
from app_bm_syncex.weight_utils import BookmarkWeightCalculator
from app_bm_syncex.views import SOURCE
# from app_bm_syncex.cache_manager import BookmarkCacheManager

class BMKeeperAPIView(APIView):
    """
    Google Chrome Bookmark Synchronization API
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _remove_duplicates(self, bookmarks):
        """Enhanced duplicate removal with better key generation"""
        def get_key(item):
            if isinstance(item, dict):
                return (
                    item.get('addr', ''),
                    item.get('path', ''),
                    item.get('title', ''),
                    item.get('is_deleted', '')
                )
            return (
                getattr(item, 'addr', ''),
                getattr(item, 'path', ''),
                getattr(item, 'title', ''),
                getattr(item, 'is_deleted', '')
            )
        
        seen = set()
        unique_items = []
        
        for item in bookmarks:
            key = get_key(item)
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
                
        return unique_items

    def _get_base_query(self, user_id, query_type='default'):
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
        else:
            return StoreEntry.objects.filter(
                **base_conditions,
                source=SOURCE
            )

    def _get_tree_bookmarks(self, query):
        """get data for tree view"""
        bookmarks = query.filter().values(
            'idx', 'title', 'addr', 'path', 'meta', 'is_deleted'
        ).order_by('path', 'title')
        
        results = [{
            'id': bm['idx'],
            'title': bm['title'].replace('...', ''),
            'url': bm['addr'],
            'folder': bm['path'] or '/',
            'created_at': bm['meta'].get('add_date', '')
        } for bm in bookmarks]
        return results

    def _get_navigation_bookmarks(self, query, sort='recent', limit=10, custom_ids=None):
        """get data for navigation view"""
        bookmarks = query.filter(status='collect', is_deleted='f')
        
        if custom_ids:
            id_list = [int(id) for id in custom_ids.split(',') if id.isdigit()]
            if id_list:
                bookmarks = bookmarks.filter(
                    idx__in=id_list,
                    meta__contains={'custom_order': True}
                )
                from django.db.models import Case, When
                preserved = Case(*[When(idx=pk, then=pos) for pos, pk in enumerate(id_list)])
                bookmarks = bookmarks.order_by(preserved)[:limit]
                return self._format_bookmarks(bookmarks)  # 使用格式化方法
        
        custom_bookmarks = bookmarks.filter(meta__contains={'custom_order': True})
        
        remaining_limit = limit - custom_bookmarks.count()
        if remaining_limit > 0:
            other_bookmarks = bookmarks.exclude(
                meta__contains={'custom_order': True}
            ).order_by('-meta__weight')[:remaining_limit]
            
            from itertools import chain
            results = list(chain(custom_bookmarks, other_bookmarks))
        else:
            results = custom_bookmarks[:limit]
            
        return self._format_bookmarks(results)  # 使用格式化方法

    def _format_bookmarks(self, bookmarks):
        """Format bookmarks into serializable dictionary format"""
        return [{
            'id': bookmark.idx,
            'title': bookmark.title,
            'url': bookmark.addr,
            'created_at': bookmark.created_time,
            'meta': bookmark.meta,
        } for bookmark in bookmarks]

    def _get_readlater_bookmarks(self, user_id, page=1, page_size=10):
        """get data for read later view with deduplication"""
        query = self._get_base_query(user_id, query_type='readlater')

        all_bookmarks = list(query.order_by('-created_time'))
        unique_bookmarks = self._remove_duplicates(all_bookmarks)
        
        total = len(unique_bookmarks)
        start = (page - 1) * page_size
        results = unique_bookmarks[start:start + page_size]

        return results, total

    def get(self, request):
        args = parse_common_args(request)
        req_type = request.GET.get('type', '')
        param = request.GET.get('param', '')
        user_id = args['user_id']

        try:
            request_type = request.GET.get('type')
            param = request.GET.get('param')
            
            logger.debug(f"BMKeeper GET request - type: {request_type}, param: {param}")
            
            if request_type == 'navigation':
                # 添加调试日志
                limit = int(param) if param and param.isdigit() else 6
                logger.debug(f"Fetching navigation bookmarks with limit: {limit}")
                
                # 获取书签数据的代码...
                bookmarks = self._get_navigation_bookmarks(self._get_base_query(user_id, query_type='default'), sort='recent', limit=limit)
                
                logger.debug(f"Found {len(bookmarks)} bookmarks")
                
                return Response({
                    'code': 200,
                    'data': bookmarks
                })
                
        except Exception as e:
            logger.error(f"Error in BMKeeperAPIView: {str(e)}")
            return Response({
                'code': 500,
                'message': str(e)
            })

        if 'folders' in request.path:
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
                    if (sub_path):  
                        parent_folder = sub_path.rsplit('/', 1)[0]
                        if parent_folder: 
                            processed_folders.append(parent_folder)
            processed_folders = sorted(set(processed_folders))
            
            return Response({
                "code": 200,
                "msg": "success",
                "data": ['/', *processed_folders]
            })

        base_query = self._get_base_query(user_id, query_type='default')

        if req_type == 'tree':
            results = self._get_tree_bookmarks(base_query)
            return Response({
                "code": 200,
                "msg": "success",
                "data": results
            })

        elif req_type == 'navigation':
            sort = request.GET.get('sort', 'recent')
            limit = int(param) if param and param.isdigit() else 10
            custom_ids = request.GET.get('custom_ids')
            nav_results = self._get_navigation_bookmarks(base_query, sort, limit, custom_ids)
            results = self._remove_duplicates(nav_results)

        elif req_type == 'search' and param:
            search_results = base_query.filter(
                Q(title__icontains=param) | Q(addr=param)
            ).order_by('-created_time')
            results = self._remove_duplicates(search_results)

        elif req_type == 'readlater':
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            results, total = self._get_readlater_bookmarks(user_id, page, page_size)
            
            bookmarks = [{
                'id': entry.idx,
                'title': entry.title,
                'url': entry.addr,
                'created_at': entry.created_time,
                'updated_time': entry.updated_time,
                'raw': entry.raw,
                'tags': entry.ctype
            } for entry in results]

            return Response({
                "code": 200,
                "msg": "success",
                "data": bookmarks,
                "total": total,
                "current_page": page,
                "page_size": page_size
            })
        
        else:
            return Response({
                "code": 400,
                "msg": "Invalid request type"
            })

        bookmarks = [{
            'id': entry.idx,
            'title': entry.title,
            'url': entry.addr,
            'created_at': entry.created_time,
            'meta': entry.meta,
        } for entry in results]

        return Response({
            "code": 200,
            "msg": "success",
            "data": bookmarks
        })

    def post(self, request):
        """post new bookmark"""
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
                folder = request.data.get('folder', '/')
                if folder == '/':
                    prefix_path = 'chrome/书签栏'
                else:
                    prefix_path = f"chrome/书签栏/{folder.lstrip('/')}"
                    
                full_path = f"{prefix_path}/{bookmark.title}"
                bookmark.status = 'collect'
                bookmark.path = full_path
                bookmark.save()
                return Response({
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "id": bookmark.idx,
                        "folder": bookmark.path
                    }
                })

            action = request.data.get('action')

            if action == 'summary':
                summary = request.data.get('summary', '')
                bookmark.summary = summary
                bookmark.save()
            
            elif action == 'move':
                folder = request.data.get('folder', '/')
                bookmark.status = 'done' 
                bookmark.folder = folder 
                bookmark.save()
            return Response({"code": 200, "msg": "success"})

        except StoreEntry.DoesNotExist:
            return Response({"code": 404, "msg": "Bookmark not found"})
        except Exception as e:
            return Response({
                "code": 500,
                "msg": str(e)
            })

    def _format_bookmark_path(self, folder, bookmark_title):
        """
        format bookmark path
        """
        folder = folder.lstrip('/') if folder else ''
        if not folder.endswith(f'/{bookmark_title}'):
            folder = f'{folder.rstrip("/")}/{bookmark_title}'
            
        return folder

    def _get_folder_bookmarks(self, user_id, folder_path):
        """get bookmarks in a folder"""
        return StoreEntry.objects.filter(
            user_id=user_id,
            source=SOURCE,
            is_deleted='f',
            path__startswith=folder_path
        )

    def put(self, request):
        """update bookmark"""
        args = parse_common_args(request)
        req_type = request.data.get('type', 'tree')
        bookmark_id = request.data.get('id')
        
        try:
            bookmark = StoreEntry.objects.get(
                idx=bookmark_id,
                user_id=args['user_id'],
                is_deleted='f'
            )
            
            if req_type == 'tree':
                return self._update_tree_bookmark(request, bookmark)
            elif req_type == 'navigation':
                return self._update_navigation_bookmark(request, bookmark)
            elif req_type == 'search':
                return self._update_search_bookmark(request, bookmark)
            elif req_type == 'readlater':
                return self._update_readlater_bookmark(request, bookmark)
            else:
                return Response({
                    "code": 400,
                    "msg": "Invalid request type"
                })

        except StoreEntry.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "Bookmark not found"
            })

    def _update_tree_bookmark(self, request, bookmark):
        """update bookmark in tree view"""
        title = request.data.get('title')
        url = request.data.get('url')
        folder = request.data.get('folder', '/')
        tags = request.data.get('tags')

        changed_fields = {}
        
        if folder:
            old_title = bookmark.title
            new_title = title or old_title
            folder = self._format_bookmark_path(folder, old_title)
            
            if not re.match(r'^(/[^/]+)*/?$', folder):
                return Response({
                    "code": 400,
                    "msg": "Invalid folder path format"
                })
            changed_fields['path'] = folder
            meta = bookmark.meta if bookmark.meta else {}
            meta['update_path'] = folder
            changed_fields['meta'] = meta

        if title:
            changed_fields['title'] = title
            if 'path' in changed_fields:
                old_path = changed_fields['path']
                changed_fields['path'] = old_path.replace(f'/{bookmark.title}', f'/{title}')
                if 'meta' in changed_fields:
                    changed_fields['meta']['update_path'] = changed_fields['path']

        if url:    
            changed_fields['addr'] = url
        if tags is not None:
            changed_fields['ctype'] = tags

        return self._save_bookmark_changes(bookmark, changed_fields)

    def _update_navigation_bookmark(self, request, bookmark):
        """update bookmark in navigation view"""
        title = request.data.get('title')
        url = request.data.get('url')
        tags = request.data.get('tags')

        changed_fields = {}
        if title:
            changed_fields['title'] = title
        if url:
            changed_fields['addr'] = url
        if tags is not None:
            changed_fields['ctype'] = tags
            
        return self._save_bookmark_changes(bookmark, changed_fields)

    def _update_search_bookmark(self, request, bookmark):
        """update bookmark in search view"""
        title = request.data.get('title')
        url = request.data.get('url')
        tags = request.data.get('tags')

        changed_fields = {}
        if title:
            changed_fields['title'] = title
        if url:
            changed_fields['addr'] = url
        if tags is not None:
            changed_fields['ctype'] = tags
            
        return self._save_bookmark_changes(bookmark, changed_fields)

    def _update_readlater_bookmark(self, request, bookmark):
        """update bookmark in read later view"""
        title = request.data.get('title')
        tags = request.data.get('tags')
        # edit source
        source = request.data.get('source', SOURCE)
        
        changed_fields = {}
        if title:
            changed_fields['title'] = title
        if tags is not None:
            changed_fields['ctype'] = tags
        if source:
            changed_fields['source'] = SOURCE

        return self._save_bookmark_changes(bookmark, changed_fields)

    def _save_bookmark_changes(self, bookmark, changed_fields):
        """save bookmark changes"""
        if changed_fields:
            changed_fields['updated_time'] = timezone.now()
            StoreEntry.objects.filter(
                idx=bookmark.idx
            ).update(**changed_fields)

            bookmark.refresh_from_db()
            
            return Response({
                "code": 200,
                "msg": "success",
                "data": {
                    "id": bookmark.idx,
                    "title": bookmark.title,
                    "url": bookmark.addr,
                    "folder": bookmark.path,
                    "tags": bookmark.ctype, 
                    "created_at": bookmark.created_time,
                    "updated_time": bookmark.updated_time 
                }
            })
        return Response({
            "code": 400,
            "msg": "No fields to update"
        })

    def delete(self, request):
        """delete bookmark"""
        args = parse_common_args(request)
        bookmark_id = request.GET.get('id')
        
        try:
            bookmark = StoreEntry.objects.get(
                idx=bookmark_id,
                user_id=args['user_id'],
                is_deleted='f'
            )
            
            delete_entry(args['user_id'], [
                {
                    'addr': bookmark.addr,
                }
            ])
            
            return Response({
                "code": 200,
                "msg": "success",
                "detail": "Bookmark deleted successfully"
            })

        except StoreEntry.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "Bookmark not found"
            })
        except Exception as e:
            return Response({
                "code": 500, 
                "msg": str(e)
            })

class BookmarkClickAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        args = parse_common_args(request)
        bookmark_id = request.data.get('id')
        user_id = args['user_id']
        
        try:
            bookmark = StoreEntry.objects.get(
                id=bookmark_id,
                user_id=user_id,
                is_deleted="f"
            )
            current_time = timezone.now()
            clicked_at = request.data.get('clicked_at', current_time.isoformat())
            
            StoreEntry.objects.filter(id=bookmark_id).update(
                meta=F('meta').concat({
                    'clicks': F('meta__clicks') + 1,
                    'visit_history': F('meta__visit_history').append({
                        'time': clicked_at,
                        'browser': request.data.get('browser', 'chrome')
                    })
                })
            )

            calculator = BookmarkWeightCalculator(bookmark, current_time)
            weight = calculator.calculate_total_weight()

            bookmark.refresh_from_db()
            bookmark.meta['weight'] = weight
            bookmark.save()

            return Response({
                "code": 200,
                "msg": "success",
                "data": {
                    "clicks": bookmark.meta.get('clicks', 0),
                    "weight": weight
                }
            })
            
        except StoreEntry.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "Bookmark not found"
            })
        except Exception as e:
            return Response({
                "code": 500,
                "msg": f"Error: {str(e)}"
            }, status=500)

class BookmarkCustomOrderAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取所有自定义排序的书签"""
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
            
            return Response({
                "code": 200,
                "msg": "success",
                "data": results
            })
            
        except Exception as e:
            logger.error(f"Error fetching custom bookmarks: {e!r}")
            return Response({
                "code": 500,
                "msg": str(e)
            })

    def post(self, request):
        args = parse_common_args(request)
        is_single_bookmark = request.data.get('singleBookmark', False)
        remove_id = request.data.get('removeId')  # 新增: 要删除的书签ID
        
        try:
            if remove_id:
                # 处理删除操作
                bookmark = StoreEntry.objects.get(
                    user_id=args['user_id'],
                    idx=remove_id,
                    is_deleted='f'
                )
                
                meta = bookmark.meta if bookmark.meta else {}
                meta['custom_order'] = False  # 设置为False表示移除自定义顺序
                bookmark.meta = meta
                bookmark.save()
                
                return Response({
                    "code": 200,
                    "msg": f"Removed bookmark {remove_id} from custom order"
                })
                
            elif is_single_bookmark:
                bookmark_id = request.data.get('bookmarkId')
                if not bookmark_id:
                    return Response({
                        "code": 400,
                        "msg": "bookmarkId is required for single bookmark update"
                    })
                
                bookmark = StoreEntry.objects.get(
                    user_id=args['user_id'],
                    idx=bookmark_id,
                    is_deleted='f'
                )
                
                meta = bookmark.meta if bookmark.meta else {}
                meta['custom_order'] = True
                bookmark.meta = meta
                bookmark.save()
                
                return Response({
                    "code": 200,                    "msg": f"Custom order updated for bookmark {bookmark_id}"
                })


        except StoreEntry.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "Bookmark not found"
            })
        except Exception as e:
            logger.error(f"Error updating custom order: {str(e)}")
            return Response({
                "code": 500,
                "msg": str(e)
            })