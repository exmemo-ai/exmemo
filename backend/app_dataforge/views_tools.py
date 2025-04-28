import os
from loguru import logger

from django.utils.translation import gettext as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from knox.auth import TokenAuthentication

from backend.common.user.utils import parse_common_args, get_user_id
from backend.common.utils.net_tools import do_result
from backend.common.parser.converter import is_support
from backend.settings import USE_CELERY

from .feature import EntryFeatureTool
from .entry import delete_entry, get_type_options
from .entry_item import EntryItem
from .models import StoreEntry
from .tasks import import_task, refresh_task
from .file_tools import real_import, real_refresh, rename_file

MAX_LEVEL = 2

class EntryAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.api(request)

    def get(self, request):
        return self.api(request)

    def api(self, request):
        rtype = request.GET.get("rtype", request.POST.get("rtype", "feature"))
        logger.info(f"rtype {rtype}")
        if rtype == "feature":
            return self.feature(request)
        elif rtype == "extract":
            return self.extract(request)
        elif rtype == "tree":
            return self.tree(request)
        elif rtype == "move":
            return self.move(request)
        elif rtype == "import":
            return self.import_to_md(request)
        elif rtype == "delete":
            return self.delete(request)
        elif rtype == "getdir":
            return self.get_dir(request)
        elif rtype == "refreshdata":
            return self.refresh_data(request)
        else:
            return do_result(False, _("unknown_action"))

    def feature(self, request):
        ctype = request.GET.get("ctype", request.POST.get("ctype", None))
        logger.debug(f"ctype {ctype}")
        return get_type_options(ctype)

    def extract(self, request):
        # Extract file features by user
        args = parse_common_args(request)
        entry = EntryItem(
            user_id=args["user_id"],
            etype=request.GET.get("etype", request.POST.get("etype", "record"))
        )
        logger.debug(f"etype {entry.etype}")
        ret = False
        info = request.GET.get("info", request.POST.get("info", None))
        ret = EntryFeatureTool.get_instance().parse(entry, info, force=True)
        if ret:
            return do_result(True, {"dic": entry.to_model_dict(for_json=True)})
        else:
            return do_result(False, {"info": "extract failed"})
        
    def _build_tree_node(self, path_dict, current_level, current_path, path_parts, 
                         entry=None, path=None, is_last_level=False):
        for i, part in enumerate(path_parts):
            if not part:
                continue
                
            current_path = (current_path + '/' + part).lstrip('/')
            if current_path not in path_dict:
                abs_path = os.path.join(path, current_path) if path != "" and path is not None else current_path
                new_node = {
                    'id': entry.idx if entry and i == len(path_parts) - 1 else abs_path,
                    'addr': abs_path,
                    'title': part,
                    'is_folder': i < len(path_parts) - 1 or is_last_level,
                    'need_load': is_last_level and i == len(path_parts) - 1,
                    'children': []
                }
                path_dict[current_path] = new_node
                current_level.append(new_node)
                current_level = new_node['children']
            else:
                current_level = path_dict[current_path]['children']
        return current_level

    def tree(self, request, debug=True):
        """
        Get file tree structure
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return Response([])

            etype = request.GET.get("etype", request.POST.get("etype", None))
            path = request.GET.get("path", request.POST.get("path", None))
            level = request.GET.get("level", request.POST.get("level", MAX_LEVEL))
            if isinstance(level, str):
                level = int(level)

            if debug:
                logger.info(f'get file tree etype: {etype}, path: {path} level: {level}')

            query_conditions = {
                'user_id': user_id,
                'is_deleted': False,
                'block_id': 0
            }
            
            if etype is not None and etype != "":
                query_conditions['etype'] = etype

            if path is not None and path != "" and etype in ['note', 'file']:
                query_conditions['addr__startswith'] = path

            query = StoreEntry.objects.filter(**query_conditions).only(
                'idx', 'addr', 'etype', 'title', 'meta'
            )
            
            """ 影响多级目录的加载
            if level != -1:
                if etype in ['note', 'file']:
                    path_level = 0
                    if path:
                        path_clean = path.strip('/')
                        if path_clean:
                            path_level = path_clean.count('/') + 1
                        if debug:
                            logger.info(f'path: {path}, path_level: {path_level}')
                    
                    query = query.exclude(
                        addr__regex=f'^[^/]*/([^/]*/){{{level+path_level}}}'
                    )
            """
            entries = query.order_by('addr')
            
            if debug:
                logger.info('entries: %s' % len(entries))
            root = []
            path_dict = {}
            count = 0
            for entry in entries:
                if entry.etype == 'note' or entry.etype == 'file':
                    file_path = entry.addr
                elif entry.etype == 'chat' or entry.etype == 'chat_record':
                    file_path = entry.title
                else:
                    if entry.meta and 'update_path' in entry.meta:
                        file_path = entry.meta['update_path']
                    elif entry.meta and 'resource_path' in entry.meta:
                        file_path = entry.meta['resource_path']
                    else:
                        file_path = entry.title

                if file_path is None or file_path == "":
                    rel_path = ""
                elif path != "" and path is not None and file_path.startswith(path):
                    rel_path = file_path[len(path):].lstrip('/')
                else:
                    rel_path = file_path

                arr = rel_path.split('/')
                if level != -1 and len(arr) > level:
                    current_path = ""
                    current_level = root
                    self._build_tree_node(path_dict, current_level, current_path, arr[:level], path=path, is_last_level=True)
                    continue

                current_path = ""
                current_level = root
                self._build_tree_node(path_dict, current_level, current_path, arr, entry=entry, path=path)
                count += 1
            if debug:
                logger.info('count: %s' % count)
            return Response(root)
            
        except Exception as e:
            logger.error(f"Error getting file tree: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to get file tree"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def move(self, request):
        """
        Move file or folder to another location
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return do_result(False, "User_id is empty")

            source = request.GET.get("source", request.POST.get("source", None))
            target = request.GET.get("target", request.POST.get("target", None))
            is_folder = request.GET.get("is_folder", request.POST.get("is_folder", "false")).lower() == "true"
            etype = request.GET.get("etype", request.POST.get("etype", None))

            if not source or not target:
                return do_result(False, "Source or target is empty")

            source = source.strip()
            target = target.strip()

            if source == target:
                return do_result(True, "Source and target are same")

            logger.debug(f'Move: {source} -> {target} (is_folder: {is_folder})')

            if not is_folder:
                entry = StoreEntry.objects.filter(user_id=user_id, addr=source, etype=etype, block_id=0).first()
                if not entry:
                    normalized_source = source.replace('\\', '/').replace('//', '/')
                    entry = StoreEntry.objects.filter(user_id=user_id, addr=normalized_source, etype=etype, block_id=0).first()
                if entry:
                    dic = entry.__dict__.copy()
                    ret = rename_file(user_id, entry.addr, target, dic)
                    if ret:
                        return do_result(True, "Move success")
                else:
                    logger.warning(f"Source file not found: {source}")
                    return do_result(False, "Source file not found")
            else:
                dirname = source if source.endswith('/') else source + '/'
                entries = StoreEntry.objects.filter(user_id=user_id, etype=etype, addr__startswith=dirname, block_id=0)
                
                logger.debug(f"Move entries: {len(entries)} {dirname}")
                for entry in entries:
                    rel_path = entry.addr[len(dirname):]
                    new_dst = os.path.join(target, rel_path)
                    dic = entry.__dict__.copy()
                    ret = rename_file(user_id, entry.addr, new_dst, dic, False);
                    if not ret:
                        return do_result(False, "Move failed")
                return do_result(True, "Move success")

            return do_result(False, "Move failed")
        except Exception as e:
            logger.error(f"Error moving file/folder: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to move file/folder"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def import_to_md(self, request, debug=False):
        """
        Import file to markdown
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return do_result(False, "User_id is empty")

            source = request.GET.get("source", request.POST.get("source", None))
            target = request.GET.get("target", request.POST.get("target", None))
            is_folder = request.GET.get("is_folder", request.POST.get("is_folder", "false")).lower() == "true"
            is_async = request.GET.get("is_async", request.POST.get("is_async", "false")).lower() == "true"
            overwrite = request.GET.get("overwrite", request.POST.get("overwrite", "false")).lower() == "true"

            if not source or not target:
                return do_result(False, "Source or target is empty")

            source = source.strip()
            target = target.strip()

            logger.debug(f'Import: {source} -> {target}')

            if is_folder:
                entries = StoreEntry.objects.filter(user_id=user_id, addr__startswith=source, etype='file', block_id=0)
            else:
                entries = StoreEntry.objects.filter(user_id=user_id, addr=source, etype='file', block_id=0)
            if not entries.exists():
                return do_result(False, "Source file not found")
            
            process_list = []
            for entry in entries:
                if not is_support(entry.path.lower()):
                    continue
                    
                if len(entry.addr) > len(source):
                    rel_path = entry.addr[len(source):]
                else:
                    rel_path = entry.addr
                if rel_path.startswith('/'):
                    rel_path = rel_path[1:]
                dst_path = os.path.join(target, os.path.splitext(rel_path)[0] + '.md')
                if debug: logger.info(f"dst_path: {dst_path}, rel_path: {rel_path}, entry.addr: {entry.addr}, source: {source}")
                
                dst_entry = StoreEntry.objects.filter(user_id=user_id, addr=dst_path, etype='note', block_id=0).first()
                if dst_entry:
                    if not overwrite:
                        logger.warning(f"Target file exists and skip: {dst_path}")
                        continue
                    process_list.append((entry.path, dst_path, True))
                else:
                    process_list.append((entry.path, dst_path, False))

            if not process_list:
                return do_result(False, _("no_file_to_import"))
            
            if USE_CELERY and is_async:
                task_id = import_task.delay(user_id, process_list, debug=debug)
                return do_result(True, {"task_id": str(task_id)})
            else:
                success_list = real_import(user_id, process_list, debug=debug)
                if not success_list:
                    return do_result(False, _("no_file_to_import")) 
                return do_result(True, {"list": success_list})
        except Exception as e:
            logger.error(f"Error importing file: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to import file"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def delete(self, request):
        """
        Delete file or folder
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return do_result(False, "User_id is empty")

            path = request.GET.get("path", request.POST.get("path", None))
            etype = request.GET.get("etype", request.POST.get("etype", None))
            is_folder = request.GET.get("is_folder", request.POST.get("is_folder", "false")).lower() == "true"

            if not path:
                return do_result(False, "Source is empty")

            path = path.strip()

            logger.debug(f'Delete: {path} (is_folder: {is_folder}) etype: {etype}')

            if not is_folder:
                entry = StoreEntry.objects.filter(user_id=user_id, addr=path, etype=etype, block_id=0).first()
                if not entry:
                    normalized_path = path.replace('\\', '/').replace('//', '/')
                    entry = StoreEntry.objects.filter(user_id=user_id, addr=normalized_path, etype=etype, block_id=0).first()
                if entry:
                    delete_entry(user_id, [{"addr": entry.addr, "etype": etype}])
                    return do_result(True, "Delete success")
                else:
                    logger.warning(f"Source file not found: {path}")
                    return do_result(False, "Source file not found")
            else:
                dirname = path if path.endswith('/') else path + '/'
                entries = StoreEntry.objects.filter(user_id=user_id, etype=etype, addr__startswith=dirname, block_id=0)
                
                logger.debug(f"Delete entries: {len(entries)} {dirname}")
                for entry in entries:
                    delete_entry(user_id, [{"addr": entry.addr, "etype": etype}])
                
                return do_result(True, "Delete success")
        except Exception as e:
            logger.error(f"Error deleting file/folder: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to delete file/folder"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_dir(self, request):
        """
        Get all directories for specific etype and path
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return do_result(False, "User_id is empty")

            path = request.GET.get("path", request.POST.get("path", None))
            etype = request.GET.get("etype", request.POST.get("etype", None))
            logger.info(f"get_dir etype: {etype}, path: {path}")
            
            if not etype:
                return do_result(False, "Etype is empty")

            query_conditions = {
                'user_id': user_id,
                'etype': etype,
                'is_deleted': False,
                'block_id': 0
            }

            if path and len(path) > 0:
                query_conditions['addr__startswith'] = path

            entries = StoreEntry.objects.filter(**query_conditions).values_list('addr', flat=True)            
            logger.debug(f"get_dir entries: {len(entries)}")
            dirs = set()
            for entry in entries:
                if path and not entry.startswith(path):
                    continue
                    
                rel_path = entry
                if path:
                    if len(entry) > len(path):
                        rel_path = entry[len(path):].lstrip('/')
                    else:
                        continue

                parts = rel_path.split('/')
                if len(parts) > 1:
                    for i in range(len(parts)-1):
                        dir_path = '/'.join(parts[:i+1])
                        if path:
                            full_path = os.path.join(path, dir_path)
                        else:
                            full_path = dir_path
                        dirs.add(full_path)

            dir_list = sorted(list(dirs))            
            return do_result(True, {"dirs": dir_list})

        except Exception as e:
            logger.error(f"Error getting directories: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to get directories"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def refresh_data(self, request):
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return do_result(False, "User_id is empty")
            is_folder = request.GET.get("is_folder", request.POST.get("is_folder", "false")).lower() == "true"
            etype = request.GET.get("etype", request.POST.get("etype", None))
            path = request.GET.get("path", request.POST.get("path", None))
            is_async = request.GET.get("is_async", request.POST.get("is_async", "false")).lower() == "true"
            if not etype:
                return do_result(False, "Etype is empty")
            if not path:
                return do_result(False, "Path is empty")
            if is_folder and USE_CELERY and is_async:
                task_id = refresh_task.delay(user_id, path, etype, is_folder)
                return do_result(True, {"task_id": str(task_id)})
            else:
                success_list = real_refresh(user_id, path, etype, is_folder)
                if len(success_list) > 0:
                    return do_result(True, _("refreshSuccess"))
                else:
                    return do_result(False, _("refreshFailed"))
        except Exception as e:
            logger.error(f"Error refreshing data: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to refresh data"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
