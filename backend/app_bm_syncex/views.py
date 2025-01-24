import json
import os
from loguru import logger
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from django.utils.translation import gettext as _
from backend.common.user.utils import parse_common_args
from rest_framework.response import Response
from django.utils import timezone
from app_dataforge.entry import check_entry_exist
from app_dataforge.views import delete_entry
from app_dataforge.misc_tools import add_url
from app_dataforge.models import StoreEntry

SOURCE = "bookmark"

class BookmarkAPIView(APIView):
    """
    Google Chrome Bookmark Synchronization API
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.do_web_bm(request)
    
    def remove_duplicates(self, post_data_lis):
        seen = set()
        unique_list = []
        
        for item in post_data_lis:

            key = (item['url'], item['path'])
            if key not in seen:
                seen.add(key)
                unique_list.append(item)
                
        return unique_list
    
    def do_web_bm(self, request):
        """
        Provide interfaces to support webpage parsing
        """
        debug = True
        count_success = 0
        args = parse_common_args(request)
        post_data_lis = request.data
        post_data_lis = self.remove_duplicates(post_data_lis)

        results = []

        # check if the request is_batch
        args['is_batch'] = bool(post_data_lis[0].get('is_batch', False)) if post_data_lis else False

        for idx, item in enumerate(post_data_lis):
            try:
                args["resource_path"] = f"chrome{item.get('path')}"
                args["add_date"] = item.get("add_date")
                args["title"] = item.get("title")
                args['status'] = item.get('status')
                args["source"] = SOURCE
                args["error"] = None
                action = item.get("action")
                
                url = item.get("url")
                if url:
                    item["addr"] = url

                if action == "delete":
                    delete_entry(args["user_id"], [item])
                    results.append({
                        "url": url, 
                        "status": "success", 
                        "info": "bookmark_deleted"
                    })
                    continue
                else:
                    if item.get("url") is not None:
                        # Check if the URL is in the database, return directly if it exists
                        if check_entry_exist(args["user_id"], item.get("url"), args["resource_path"]):
                            results.append(
                                {
                                    "url": item.get("url"),
                                    "status": "success",
                                    "info": _("data_already_exists"),
                                }
                            )
                        else:
                            ret, base_path, info = add_url(url, args, item.get('status'))
                            if ret:
                                count_success += 1
                            if not ret:
                                print(ret, base_path, info)
                            results.append(
                                {"url": url, "status": "success", "info": info}
                            )
            except json.JSONDecodeError as e:
                results.append(
                    {"url": item.get("url"), "status": "failed", "error": str(e)}
                )
            except Exception as e:
                results.append(
                    {"url": item.get("url"), "status": "failed", "error": str(e)}
                )
        logger.info(f"do_web_bm return {count_success}")
        return Response({"status": "success", "results": results})

class BookmarkClickAPIView(APIView):
    """处理书签点击事件的API"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger.info(f"Received click data: {request.data}")
            
            url = request.data.get('url')
            meta = request.data.get('meta', {})
            
            if not url:
                logger.error("Missing URL in request data")
                return Response({'status': 'error', 'message': 'URL is required'}, status=400)
                
            args = parse_common_args(request)
            query_params = {
                'user_id': args['user_id'],
                'addr': url,
                'source': SOURCE,
                'is_deleted': False
            }
            
            logger.info(f"Looking up bookmark with params: {query_params}")
            bookmark = StoreEntry.objects.filter(**query_params).first()
            
            if not bookmark:
                logger.warning(f"Bookmark not found for URL: {url}")
                return Response({
                    'status': 'error',
                    'message': 'bookmark not found',
                    'query_params': query_params
                }, status=404)
            
            if not isinstance(bookmark.meta, dict):
                bookmark.meta = {}
            
            current_time = timezone.now().isoformat()
            visit_record = current_time
            
            if 'visit_history' not in bookmark.meta:
                bookmark.meta['visit_history'] = []
            bookmark.meta['visit_history'].append(visit_record)
            
            if 'visit_history' not in bookmark.meta:
                bookmark.meta['visit_history'] = []
            bookmark.meta['visit_history'].append(visit_record)

            clicks = len(bookmark.meta['visit_history'])
            last_visit_time = datetime.fromisoformat(current_time)
            age_in_days = (timezone.now() - bookmark.created_at).days
            
            frequency_weight = min(1.0, clicks / max(1, age_in_days)) * 0.5
            recency_weight = min(1.0, 1 / max(1, (timezone.now() - last_visit_time).days)) * 0.3
            base_weight = float(bookmark.meta.get('base_weight', 0.0)) * 0.2
            
            bookmark.meta['clicks'] = clicks
            bookmark.meta['weight'] = frequency_weight + recency_weight + base_weight
            bookmark.meta['last_visit'] = current_time
            
            bookmark.save()
            logger.info(f"Successfully updated bookmark: {bookmark.title}, total clicks: {bookmark.meta['clicks']}")
            
            return Response({
                'status': 'success',
                'data': {
                    'title': bookmark.title,
                    'clicks': bookmark.meta['clicks'],
                    'weight': bookmark.meta['weight'],
                    'visit_record': visit_record
                }
            })
            
        except Exception as e:
            logger.exception("Error processing bookmark click")
            return Response({
                'status': 'error',
                'message': str(e),
                'detail': traceback.format_exc()
            }, status=500)