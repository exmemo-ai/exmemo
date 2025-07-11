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
from knox.auth import TokenAuthentication

from backend.common.files import utils_filemanager, filecache
from backend.common.user.utils import get_user_id
from backend.common.utils.net_tools import do_result, get_backend_addr
from backend.common.utils.web_tools import get_url_content
from backend.common.utils.file_tools import get_content_type, get_ext
from backend.common.parser.converter import convert, is_support
from backend.settings import USE_CELERY

from .entry import delete_entry, add_data, get_entry_list
from .entry import EmbeddingNotAvailableError
from .models import StoreEntry
from .serializers import ListSerializer, DetailSerializer
from .zipfile import is_compressed_file
from .file_tools import update_files, rename_file, update_file
from .tasks import update_files_task
from .entry_storage import EntryStorage

MAX_LEVEL = 2

class StoreEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = StoreEntry.objects.filter(is_deleted=False).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ListSerializer
        return DetailSerializer

    def create(self, request, *args, **kwargs):
        """
        update files
        """
        debug = False
        try:
            dic = {}
            dic["etype"] = request.POST.get("etype", "note")
            dic["ctype"] = request.POST.get("ctype", None)
            dic["title"] = request.POST.get("title", None)
            dic["atype"] = request.POST.get("atype", None)
            dic["raw"] = request.POST.get("raw", None)
            dic['content'] = request.POST.get("content", None)
            dic["status"] = request.POST.get("status", "collect")
            dic["idx"] = request.POST.get("idx", None)
            dic["user_id"] = get_user_id(request)
            dic["source"] = request.POST.get("source", "web")
            is_async = request.POST.get("is_async", "false").lower() == "true"
            logger.info(f"now create instance: {dic['etype']}, user_id {dic['user_id']}, is_async {is_async}")
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
                ret, ret_emb, info = add_data(dic, data = {'content': dic["content"]})
                return do_result(ret, info)
            elif dic["etype"] == "file" or dic["etype"] == "note":
                vault = request.POST.get("vault", None)
                is_unzip = request.POST.get("unzip", "false").lower() == "true"
                is_createSubDir = request.POST.get("createSubDir", "true").lower() == "true"
                files = request.FILES.getlist("files")
                filepaths = request.POST.getlist("filepaths")
                filemd5s = request.POST.getlist("filemd5s")
                
                if getattr(settings, 'IS_TRIAL_MODE', True):
                    max_size = getattr(settings, 'TRIAL_MAX_FILE_SIZE', 20 * 1024 * 1024)
                    for file in files:
                        if not is_compressed_file(file.name) and file.size > max_size:
                            size_mb = file.size / (1024 * 1024)
                            return do_result(False, _("File '{}' ({:.1f}MB) exceeds the trial mode limit of 20MB for non-compressed files").format(file.name, size_mb))
                
                if debug:
                    logger.info(
                        f"do_upload files {files}, filepaths {filepaths},  filemd5s {filemd5s}"
                    )

                tmp_file_paths = []
                for file in files:
                    ext = get_ext(file.name)
                    tmp_path = filecache.get_tmpfile(ext)
                    with open(tmp_path, "wb") as f:
                        for chunk in file.chunks():
                            f.write(chunk)
                    tmp_file_paths.append(tmp_path)

                is_zip_file = False
                if is_unzip:
                    for file in files:
                        if is_compressed_file(file.name):
                            is_zip_file = True
                            break
                
                if USE_CELERY and is_async and (len(files) > 1 or is_zip_file):
                    task_id = update_files_task.delay(
                        dic['user_id'], 
                        tmp_file_paths,
                        filepaths,
                        filemd5s,
                        dic,
                        vault,
                        is_unzip,
                        is_createSubDir
                    )
                    return do_result(True, {"task_id": str(task_id)})
                else:
                    success_list, emb_status = update_files(tmp_file_paths, filepaths, filemd5s, dic, vault, is_unzip, is_createSubDir, debug=debug)
                    if debug:
                        logger.info(f"upload_files success {str(success_list)[:200]}...")
                    else:
                        logger.info(f"upload_files success {len(success_list)}")
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
            delete_entry(instance.user_id, [{"addr": instance.addr, "etype": instance.etype}])
            return do_result(True, None)
        except Exception as e:
            logger.warning(f"destroy failed {e}")
            traceback.print_exc()
            return do_result(False, None)

    def list(self, request, *args, **kwargs):
        """
        get entry list by page
        """
        debug = False
        query_args = {}
        user_id = get_user_id(request)
        if user_id is None:
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
        rstatus = request.GET.get("status", None)
        if rstatus is not None and len(rstatus) > 0:
            query_args["status"] = rstatus
        method = request.GET.get("method", 'auto')
        keywords = request.GET.get("keyword", None)
        exclude = request.GET.get("exclude", None)
        case_sensitive = request.GET.get("case_sensitive", "false").lower() == "true"
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

        try:
            queryset = get_entry_list(keywords, query_args, max_count if max_count != -1 else -1, method=method, 
                                      exclude=exclude, case_sensitive=case_sensitive, debug=debug)
            
            if max_count == -1:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                else:
                    serializer = self.get_serializer(queryset, many=True)
                    return Response(serializer.data)
            else:
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)
                
        except EmbeddingNotAvailableError as e:
            logger.warning(f"Embedding not available: {e}")
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            logger.error(f"Error in list: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            full_content = request.query_params.get('full_content', 'true').lower() == 'true'
            if instance.etype == 'record' or instance.etype == 'chat':
                serializer = self.get_serializer(instance)
                data = serializer.data
                data['content'] = EntryStorage.get_content(instance.user_id, instance.addr)
                return Response(data)
            elif instance.etype == 'web':
                serializer = self.get_serializer(instance)
                data = serializer.data
                if full_content:
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
                    if full_content:
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
                    else:
                        serializer = self.get_serializer(instance)
                        data = serializer.data
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
        debug = False
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
        
        ret = False
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
            elif request.FILES:
                if getattr(settings, 'IS_TRIAL_MODE', True):
                    max_size = getattr(settings, 'TRIAL_MAX_FILE_SIZE', 20 * 1024 * 1024)
                    file = request.FILES['files']
                    if not is_compressed_file(file.name) and file.size > max_size:
                        size_mb = file.size / (1024 * 1024)
                        return do_result(False, _("File '{}' ({:.1f}MB) exceeds the trial mode limit of 20MB for non-compressed files").format(file.name, size_mb))
                ext = get_ext(instance.addr)
                tmp_path = filecache.get_tmpfile(ext)
                with open(tmp_path, "wb") as f:
                    file = request.FILES['files']
                    for chunk in file.chunks():
                        f.write(chunk)
                    f.close()
                ret, ret_emb, detail = update_file(dic, instance.addr, tmp_path, None,
                                                   vault=None, is_unzip=False, is_createSubDir=False, debug=debug)
                if not ret:
                    return do_result(False, _("update_failed"))
                return do_result(True, _("update_successfully"))
            else:
                ret, ret_emb, info = add_data(dic, debug=debug)
        elif instance.etype == "record":
            content = request.data.get("content", None)
            ret, ret_emb, info = add_data(dic, data = {'content': content}, debug=debug)
        else:
            ret, ret_emb, info = add_data(dic, debug=debug)
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

