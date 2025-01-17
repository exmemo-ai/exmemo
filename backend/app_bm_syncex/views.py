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
# from .config_manager import BookmarkConfigManager
# from .config_service import config_service

SOURCE = "bookmark"

class BookmarkAPIView(APIView):
    """
    Google Chrome Bookmark Synchronization API
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    
    # def _update_llm_env(self, config):
    #     """
    #     Update LLM environment variables
    #     """
    #     if config.get('llm_model'):
    #         os.environ['DEFAULT_CHAT_LLM'] = config['llm_model']
    #         os.environ['DEFAULT_TOOL_LLM'] = config['llm_model']
            
    #     if config.get('llm_api_key'):
    #         os.environ['OPENAI_API_KEY'] = config['llm_api_key']
            
    #     if config.get('llm_base_url'):
    #         os.environ['OPENAI_API_BASE'] = config['llm_base_url']

    # def _get_parsing_config(self, username):
    #     """
    #     Get parsing configuration from user settings
    #     """
    #     config = config_service.get_config(username)
    #     parsing_args = {
    #         "parse_content": config['extract_content'],
    #         "truncate_content": config['truncate_content'],
    #         "max_content_length": config['max_content_length'],
    #         "truncate_mode": config['truncate_mode'],
    #         "use_llm": False
    #     }
        
    #     # check config and update LLM environment
    #     if (config['extract_content'] and 
    #         config['llm_api_key'] and 
    #         config['llm_base_url'] and 
    #         config['llm_model']):
    #         parsing_args["use_llm"] = True
            
    #     return parsing_args

    def post(self, request):
        return self.do_web_bm(request)
    
    def remove_duplicates(self, post_data_lis):
        seen = set()
        unique_list = []
        
        for item in post_data_lis:
            # 使用url和path组合作为唯一key
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
        args = parse_common_args(request)
        post_data_lis = request.data
        post_data_lis = self.remove_duplicates(post_data_lis)
        # 对比去重前后数据长度
        if debug:
            print(f"before remove duplicates: {len(request.data)}")
            print(f"after remove duplicates: {len(post_data_lis)}")

        results = []

        extract_content = request.META.get('HTTP_X_EXTRACT_CONTENT', 'false').lower() == 'true'
        os.environ['IS_PARSE_CONTENT'] = str(extract_content)

        for item in post_data_lis:
            try:
                args["resource_path"] = f"chrome{item.get('path')}"
                args["add_date"] = item.get("add_date")
                args["title"] = item.get("title")
                args['status'] = item.get('status')
                args["source"] = SOURCE
                args["error"] = None
                action = item.get("action")
                
                # 将 url 转换为 addr
                url = item.get("url")
                if args["title"]=='深圳科学院':
                    print(item)
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
            
            # 确保meta字段初始化
            if not isinstance(bookmark.meta, dict):
                bookmark.meta = {}
            
            # 记录访问
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

# ======= 前端llm&截断配置项接收，暂时注释 =======
# class BookmarkSettingsView(APIView): 
#     """."""
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.config_manager = BookmarkConfigManager()

    # def get(self, request):
    #     """获取用户配置"""
    #     try:
    #         config = config_service.get_config(request.user.username)
    #         return Response(config)
    #     except Exception as e:
    #         logger.error(f"Error loading config: {str(e)}")
    #         return Response({'status': 'error', 'message': str(e)}, status=500)

    # def post(self, request):
    #     """更新用户配置"""
    #     try:
    #         logger.info(f"Received settings data: {request.data}")
            
    #         config = request.data.get('settings', {})
    #         logger.info(f"Parsed config data: {config}")
            
    #         if 'BOOKMARK_EXTRACT_CONTENT' in config:
    #             config['BOOKMARK_EXTRACT_CONTENT'] = config['BOOKMARK_EXTRACT_CONTENT'].lower() == 'true'
    #             logger.info(f"Converted extract_content: {config['BOOKMARK_EXTRACT_CONTENT']}")
            
    #         if 'BOOKMARK_TRUNCATE_CONTENT' in config:
    #             config['BOOKMARK_TRUNCATE_CONTENT'] = config['BOOKMARK_TRUNCATE_CONTENT'].lower() == 'true'
    #         if 'BOOKMARK_AUTO_TAG' in config:
    #             config['BOOKMARK_AUTO_TAG'] = config['BOOKMARK_AUTO_TAG'].lower() == 'true'
            
    #         save_result = config_service.update_config(request.user.username, config)
    #         logger.info(f"Config save result: {save_result}")
            
    #         return Response({'status': 'success'})
    #     except Exception as e:
    #         logger.error(f"Error saving config: {str(e)}")
    #         return Response({'status': 'error', 'message': str(e)}, status=500)
