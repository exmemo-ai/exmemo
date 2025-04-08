import os
import traceback
import datetime
from loguru import logger
from wsgiref.util import FileWrapper

from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _
from django.http import HttpResponse, Http404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from knox.auth import TokenAuthentication

from backend.common.files import utils_filemanager, filecache
from backend.common.user.utils import parse_common_args, get_user_id
from backend.common.utils.net_tools import do_result, get_backend_addr
from backend.common.utils.web_tools import get_url_content
from backend.common.utils.file_tools import get_content_type, get_ext
from backend.common.parser.converter import convert, is_support

from .feature import EntryFeatureTool
from .entry import delete_entry, add_data, get_entry_list, get_type_options, rename_file
from .models import StoreEntry
from .serializers import ListSerializer, DetailSerializer

MAX_LEVEL = 2

class StoreEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreEntry.objects.filter(is_deleted=False).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ListSerializer
        return DetailSerializer

    def update_file(self, dic, addr, file, md5, vault=None):
        if addr.startswith("/"):
            addr = addr[1:]
        dic_item = dic.copy()
        if vault is not None:
            dic_item["addr"] = os.path.join(vault, addr)
        else:
            dic_item["addr"] = addr
        dic_item["md5"] = md5
        tmp_path = filecache.get_tmpfile(get_ext(addr))
        data = file.file.read()
        logger.debug("## save to db " + tmp_path + " len " + str(len(data)))
        with open(tmp_path, "wb") as f:
            f.write(data)
        return add_data(dic_item, tmp_path)

    def create(self, request, *args, **kwargs):
        logger.info("now create instance")
        """
        update files
        """
        debug = True
        try:
            dic = {}
            dic["etype"] = request.POST.get("etype", "note")
            dic["ctype"] = request.POST.get("ctype", None)
            dic["title"] = request.POST.get("title", None)
            dic["atype"] = request.POST.get("atype", None)
            dic["raw"] = request.POST.get("raw", None)
            dic["status"] = request.POST.get("status", "collect")
            dic["idx"] = request.POST.get("idx", None)
            dic["user_id"] = get_user_id(request)
            dic["source"] = request.POST.get("source", "web")
            if dic["etype"] == "web":
                addr = request.POST.get("addr", None)
                if not addr.startswith("http"):
                    addr = f"http://{addr}"
                dic["addr"] = addr
                ret, ret_emb, info = add_data(dic)
                if "content" in info:  # Doesn't return False?
                    return do_result(True, str(info["content"]))
                return do_result(True, str(info))
            elif dic["etype"] == "record":  # maybe more then one entry
                ret, ret_emb, info = add_data(dic)
                return do_result(ret, info)
            elif dic["etype"] == "file" or dic["etype"] == "note":
                vault = request.POST.get("vault", None)
                files = request.FILES.getlist("files")
                filepaths = request.POST.getlist("filepaths")
                filemd5s = request.POST.getlist("filemd5s")
                if debug:
                    logger.info(
                        f"do_upload files {files}, filepaths {filepaths},  filemd5s {filemd5s}"
                    )
                success_list = []
                if len(files) > 0 and len(filemd5s) == 0:
                    filemd5s = [None] * len(files)
                emb_status = "success"
                for file, addr, md5 in zip(files, filepaths, filemd5s):
                    ret, ret_emb, detail = self.update_file(dic, addr, file, md5, vault)
                    if not ret_emb:
                        emb_status = "failed"
                    if ret:
                        success_list.append(addr)
                if debug:
                    logger.info(f"upload_files success {success_list}")
                if len(success_list) > 0:
                    return do_result(True, {"list": success_list, "emb_status": emb_status})
                else:
                    return do_result(False, _("no_update_needed"))
        except Exception as e:
            traceback.print_exc()
            logger.warning(f"upload_files failed {e}")
            return do_result(False, _("uploading_failed"))

    def destroy(self, request, *args, **kwargs):
        """
        remove item
        """
        try:
            logger.debug(request)
            instance = self.get_object()
            logger.debug(f"user_id {instance.user_id}")
            delete_entry(instance.user_id, [{"addr": instance.addr}])
            return do_result(True, None)
        except Exception as e:
            logger.warning(f"destroy failed {e}")
            traceback.print_exc()
            return do_result(False, None)

    def list(self, request, *args, **kwargs):
        """
        get entry list by page
        """
        debug = True  # for test
        count_limit = 100
        query_args = {}
        user_id = get_user_id(request)
        if user_id == None:
            return Response([])
        else:
            query_args["user_id"] = user_id
        max_count = request.GET.get("max_count", -1)
        max_count = int(max_count)
        etype = request.GET.get("etype", None)
        if etype is not None and len(etype) > 0:
            query_args["etype"] = etype
        ctype = request.GET.get("ctype", None)
        if ctype is not None and len(ctype) > 0:
            query_args["ctype"] = ctype
        status = request.GET.get("status", None)
        if status is not None and len(status) > 0:
            query_args["status"] = status
        keywords = request.GET.get("keyword", None)
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)
        if start_date is not None and len(start_date) > 0:
            query_args["created_time__gte"] = datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            )
        if end_date is not None and len(end_date) > 0:
            query_args["created_time__lte"] = datetime.datetime.strptime(
                end_date, "%Y-%m-%d"
            )

        if debug:
            logger.debug(f"args {query_args}, keyword {keywords}")

        if max_count != -1:
            count_limit = max_count
        queryset = get_entry_list(keywords, query_args, count_limit)
        logger.debug(f"list total: {len(queryset)}")

        if max_count == -1: # get item by page
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = sorted(serializer.data, key=lambda x: x["ctype"])
        paginator = PageNumberPagination()
        if queryset.count() > 0:
            paginator.page_size = queryset.count()
        else:
            paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, self.request)
        return paginator.get_paginated_response(data)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.etype == 'record' or instance.etype == 'chat':
                serializer = self.get_serializer(instance)
                data = serializer.data
                data['content'] = instance.raw
                return Response(data)
            elif instance.etype == 'web':
                serializer = self.get_serializer(instance)
                data = serializer.data
                title, data['content'] = get_url_content(instance.addr, format='markdown')
                return Response(data)
            elif instance.etype == 'file' or instance.etype == 'note':
                if instance.path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    user_id = instance.user_id
                    rel_path = os.path.join(user_id, instance.path)
                    static_path = settings.STATICFILES_DIRS
                    if len(static_path) > 0:
                        static_path = static_path[0]
                        media_path = os.path.join(static_path, rel_path)
                        media_dir = os.path.dirname(media_path)
                        if not os.path.exists(media_dir):
                            os.makedirs(media_dir)
                        ret = utils_filemanager.get_file_manager().get_file(
                            user_id, instance.path, media_path
                        )
                        if ret:
                            filecache.TmpFileManager.get_instance().add_file(media_path)
                            serializer = self.get_serializer(instance)
                            data = serializer.data
                            url = rel_path.replace(' ', '%20')
                            data['content'] = f"![]({os.path.join(get_backend_addr(request), 'static', url)})"
                            return Response(data)
                    raise Http404
                elif instance.path.lower().endswith('.md'): # markdown
                    rel_path = instance.path
                    user_id = instance.user_id
                    file_path = filecache.get_tmpfile('.md')
                    ret = utils_filemanager.get_file_manager().get_file(
                        user_id, rel_path, file_path
                    )
                    if ret:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                            serializer = self.get_serializer(instance)
                            data = serializer.data
                            data['content'] = content
                            return Response(data)
                    raise Http404
                elif is_support(instance.path.lower()): # docx, pdf, txt, html
                    rel_path = instance.path
                    user_id = instance.user_id
                    file_path = filecache.get_tmpfile(get_ext(rel_path))
                    ret = utils_filemanager.get_file_manager().get_file(
                        user_id, rel_path, file_path
                    )
                    if ret:
                        filecache.TmpFileManager.get_instance().add_file(file_path)
                        md_path = filecache.get_tmpfile('.md')
                        ret = convert(file_path, md_path)
                        if ret:
                            with open(md_path, 'r', encoding='utf-8') as file:
                                content = file.read()
                                serializer = self.get_serializer(instance)
                                data = serializer.data
                                data['content'] = content
                                return Response(data)
                    raise Http404
            # others
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.warning(f"retrieve failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        instance = self.get_object() # base instance         
        dic = {}
        for key in instance.__dict__.keys():
            if key == "_state":
                continue
            dic[key] = instance.__dict__[key]

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return do_result(False, str(serializer.errors))
        dic.update(serializer.validated_data) # data: base + request
        
        if instance.etype in ["file", "note"]:
            # check rename
            if 'addr' in serializer.validated_data and instance.addr != serializer.validated_data['addr']:
                logger.info(f"update instance addr {instance.addr} {serializer.validated_data['addr']}")
                ret = rename_file(instance.user_id, instance.addr, serializer.validated_data['addr'], dic)
                if not ret:
                    return do_result(False, _("update_failed"))
                else:
                    return do_result(True, _("update_successfully"))
            # check update file
            if request.FILES:
                ret, ret_emb, detail = self.update_file(dic, instance.addr, request.FILES['files'], None)
                if not ret:
                    return do_result(False, _("update_failed"))
                return do_result(True, _("update_successfully"))
        
        ret, ret_emb, info = add_data(dic)
        if not ret:
            return do_result(False, _("update_failed"))
        return do_result(True, _("update_successfully"))

    def perform_custom_logic(self, validated_data):
        # demo
        # if validated_data.get('price') and validated_data['price'] < 0:
        #    raise ValidationError("price err！")
        # print(f": {validated_data}")
        pass

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        """
        Download file according to Django standard.
        """
        try:
            entry = self.get_object()
            rel_path = entry.path
            user_id = entry.user_id

            ext = get_ext(rel_path)
            file_path = filecache.get_tmpfile(ext)
            ret = utils_filemanager.get_file_manager().get_file(
                user_id, rel_path, file_path
            )

            if ret:
                with open(file_path, "rb") as file:
                    # Create an HttpResponse object
                    ctype = get_content_type(file_path)
                    logger.debug(f"download content type {ctype}")
                    response = HttpResponse(FileWrapper(file), ctype)
                    # Set the file name
                    file_name = os.path.basename(rel_path)
                    logger.debug(f"filename:{file_name}")
                    file_name = smart_str(file_name)
                    logger.debug(f"smart_str, filename:{file_name}")
                    response["Content-Disposition"] = (
                        f'attachment; filename="{file_name}"'
                    )
                    # Add the necessary CORS headers
                    response["Access-Control-Allow-Origin"] = "*"
                    response["Access-Control-Expose-Headers"] = "Content-Disposition"
                    return response
            raise Http404
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class EntryAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.api(request)

    def get(self, request):
        return self.api(request)

    def api(self, request):
        rtype = request.GET.get("rtype", request.POST.get("rtype", "feature"))
        if rtype == "feature":
            return self.feature(request)
        elif rtype == "extract":
            return self.extract(request)
        elif rtype == "tree":
            return self.tree(request)
        else:
            return do_result(False, _("unknown_action"))

    def feature(self, request):
        ctype = request.GET.get("ctype", request.POST.get("ctype", None))
        logger.debug(f"ctype {ctype}")
        return get_type_options(ctype)

    def extract(self, request):
        dic = {}
        args = parse_common_args(request)
        dic["etype"] = request.GET.get("etype", request.POST.get("etype", "record"))
        dic["user_id"] = args["user_id"]
        logger.debug(f"etype {dic['etype']}")
        ret = False
        if dic["etype"] in ["record", "chat"]:
            raw = request.GET.get("raw", request.POST.get("raw", None))
            ret, dic_new = EntryFeatureTool.get_instance().parse(dic, raw, force=True)
        elif dic["etype"] in ["web", "note", "file"]:
            addr = request.GET.get("addr", request.POST.get("addr", None))
            ret, dic_new = EntryFeatureTool.get_instance().parse(dic, addr, force=True)
        if ret:
            return do_result(True, {"dic": dic_new})
        else:
            return do_result(False, {"info": "extract failed"})
        
    def _build_tree_node(self, path_dict, current_level, current_path, path_parts, entry=None, path=None, is_last_level=False):
        for i, part in enumerate(path_parts):
            if not part:
                continue
                
            current_path = (current_path + '/' + part).lstrip('/')
            if current_path not in path_dict:
                abs_path = os.path.join(path, current_path) if path != "" and path is not None else current_path
                new_node = {
                    'id': entry.idx if entry and i == len(path_parts) - 1 else abs_path,
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

    def tree(self, request):
        """
        Get file tree structure
        """
        try:
            user_id = get_user_id(request)
            if user_id is None:
                return Response([])

            etype = request.GET.get("etype", request.POST.get("etype", None))
            path = request.GET.get("path", request.POST.get("path", None))

            query_conditions = {
                'user_id': user_id,
                'is_deleted': False
            }
            
            if etype is not None and etype != "":
                query_conditions['etype'] = etype

            if path is not None and path != "" and etype in ['note', 'file']:
                query_conditions['addr__startswith'] = path

            entries = StoreEntry.objects.filter(**query_conditions).order_by('addr')

            root = []
            path_dict = {}
            for entry in entries:
                if entry.etype != 'web':
                    file_path = entry.addr
                else:
                    if entry.meta and 'update_path' in entry.meta:
                        file_path = entry.meta['update_path']
                    elif entry.meta and 'resource_path' in entry.meta:
                        file_path = entry.meta['resource_path']
                    else:
                        file_path = entry.title

                if path != "" and path is not None and file_path.startswith(path):
                    rel_path = file_path[len(path):].lstrip('/')
                else:
                    rel_path = file_path

                arr = rel_path.split('/')
                if len(arr) > MAX_LEVEL:
                    # 处理超过最大层级的情况
                    current_path = ""
                    current_level = root
                    self._build_tree_node(path_dict, current_level, current_path, arr[:MAX_LEVEL], path=path, is_last_level=True)
                    continue

                current_path = ""
                current_level = root
                self._build_tree_node(path_dict, current_level, current_path, arr, entry=entry, path=path)

            return Response(root)
            
        except Exception as e:
            logger.error(f"Error getting file tree: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to get file tree"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


