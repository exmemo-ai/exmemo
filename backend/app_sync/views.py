"""
sync obsidian notes
"""

import re
import json
import pytz
from loguru import logger
from backend.common.user.user import *

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Max
from knox.auth import TokenAuthentication

from backend.common.llm.llm_hub import EmbeddingTools
from backend.common.user.utils import parse_common_args

from app_dataforge.entry import delete_entry, regerate_embedding
from app_dataforge.models import StoreEntry


class SyncAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self.parse_sync(request)

    def get(self, request):
        return self.parse_sync(request)

    def parse_sync(self, request):
        """
        main inteface
        """
        args = parse_common_args(request)
        rtype = request.GET.get("rtype", request.POST.get("rtype", "upload"))
        logger.info(f"rtype {rtype}")
        if rtype == "compare":
            return self.do_compare(args, request)
        elif rtype == "check_update": # check update status on server
            return self.check_update(args, request)
        elif rtype == "check_embedding":
            return self.do_check_embedding(args, request)
        elif rtype == "regerate_embedding":
            return self.do_regerate_embedding(args, request)

    def adjust_files(self, file_dic, include, exclude):
        """
        Adjust the file list according to include/exclude rules
        """
        if include == "" and exclude == "":
            return file_dic
        new_dic = {}
        if include != "":
            include_list = include.split(",")
            for key, value in file_dic.items():
                for item in include_list:
                    if key.startswith(item):
                        new_dic[key] = value
                        break
        else:
            new_dic = file_dic
        if exclude != "":
            exclude_list = exclude.split(",")
            exclude_rules = []
            for item in exclude_list:
                rule = item.replace(".", "\.").replace("*", ".*")
                exclude_rules.append(rule)
            logger.warning(exclude_rules)
            for key in list(new_dic.keys()):
                for rule in exclude_rules:
                    if re.search(rule, key):
                        del new_dic[key]
                        break
        logger.info(f"base_dic {len(file_dic)}, new_dic {len(new_dic)}")
        return new_dic

    def do_regerate_embedding(self, args, request):
        uid = args["user_id"]
        addrs = request.GET.get("addr_list", request.POST.get("addr_list", "[]"))
        use_embedding = EmbeddingTools.use_embedding()
        addrs = json.loads(addrs)
        logger.info(f"regerate embedding addrs {len(addrs)} {addrs[0]}...")

        # Update embedding of addrs in the database
        emb_status = "success"
        emb_model = EmbeddingTools.get_model_name(use_embedding)
        if emb_model is None:
            return HttpResponse(
                json.dumps({"status": "failed", "emb_status": "no embedding model"})
            )
        for addr in addrs:
            if regerate_embedding(uid, addr, emb_model) is False:
                emb_status = "failed"
                logger.warning(f"regerate embedding failed {addr}")
                break
        return HttpResponse(json.dumps({"status": "success", "emb_status": emb_status}))

    def do_check_embedding(self, args, request):
        """
        Check which files need to regenerate embeddings
        """
        uid = args["user_id"]
        use_embedding = EmbeddingTools.use_embedding()
        entries = (
            StoreEntry.objects.filter(user_id=uid, is_deleted=False, raw__isnull=False)
            .exclude(raw__exact="")
            .values("addr", "emb_model")
        )
        entries = entries.distinct()
        addr_list = []
        model_name = EmbeddingTools.get_model_name(use_embedding)
        if model_name is not None:
            for entry in entries:
                if entry["emb_model"] == model_name:
                    continue
                addr_list.append(entry["addr"])
        addr_list = list(set(addr_list))
        logger.info(f"check embedding return {len(addr_list)}")
        return HttpResponse(json.dumps({"status": "success", "list": addr_list}))

    def check_update(self, args, request, debug=False):
        vault = request.GET.get("vault", request.POST.get("vault", None))
        last_sync_time = request.GET.get(
            "last_sync_time", request.POST.get("last_sync_time", 0)
        )
        last_sync_time = int(last_sync_time)
        last_sync_time = timezone.datetime.fromtimestamp(
            last_sync_time / 1000, pytz.UTC
        )

        uid = args["user_id"]
        if vault is not None:
            if not vault.endswith("/"):
                vault = vault + "/"
            entries = StoreEntry.objects.filter(
                block_id=0, etype="note", addr__startswith=vault, user_id=uid
            ).aggregate(Max("updated_time"))
        else:
            entries = StoreEntry.objects.filter(
                block_id=0, etype="note", user_id=uid
            ).aggregate(Max("updated_time"))
        max_updated_time = entries['updated_time__max']
        logger.info(f'check_update {last_sync_time} {max_updated_time}')
        if max_updated_time is None:
            max_updated_time = 0
        if last_sync_time < max_updated_time:
            return HttpResponse(json.dumps({"status": "success", "update": True}))
        else:
            return HttpResponse(json.dumps({"status": "success", "update": False}))
    
    def do_compare(self, args, request, debug=False):
        """
        Compare Local Files and Cloud Files
        """
        vault = request.GET.get("vault", request.POST.get("vault", None))
        files = request.GET.get("files", request.POST.get("files", "[]"))
        include = request.GET.get("include", request.POST.get("include", ""))
        exclude = request.GET.get("exclude", request.POST.get("exclude", ""))
        files = json.loads(files)
        logger.info(f"compare files, client {len(files)} {files[:10]}...")
        last_sync_time = request.GET.get(
            "last_sync_time", request.POST.get("last_sync_time", 0)
        )
        last_sync_time = int(last_sync_time)
        last_sync_time = timezone.datetime.fromtimestamp(
            last_sync_time / 1000, pytz.UTC
        )
        uid = args["user_id"]
        if vault is not None:
            if not vault.endswith("/"):
                vault = vault + "/"
            entries = StoreEntry.objects.filter(
                block_id=0, etype="note", addr__startswith=vault, user_id=uid
            ).values("idx", "updated_time", "md5", "is_deleted", "addr")
        else:
            entries = StoreEntry.objects.filter(
                block_id=0, etype="note", user_id=uid
            ).values("idx", "updated_time", "md5", "is_deleted", "addr")

        cloud_dic = {}
        for entry in entries:
            key = entry["addr"]
            if vault is not None:
                if key.startswith(vault):
                    key = key[len(vault) :]
            cloud_dic[key] = {
                "mtime": entry["updated_time"],
                "addr": entry["addr"],
                "is_deleted": entry["is_deleted"],
                "md5": entry["md5"],
                "idx": entry["idx"],
            }
        client_dic = {}
        for item in files:
            if "mtime" in item and item["mtime"] is not None:
                mtime = int(item["mtime"]) / 1000
            else:
                mtime = 0
            client_dic[item["path"]] = {
                "mtime": timezone.datetime.fromtimestamp(mtime, pytz.UTC),
                "md5": item["md5"],
            }
        client_dic = self.adjust_files(
            client_dic, include, exclude
        )  # Currently filtered once on the client side as well
        cloud_dic = self.adjust_files(cloud_dic, include, exclude)
        logger.debug(f"client_dic {str(client_dic)[:200]}")
        # logger.debug(f"cloud {cloud_dic}")
        cloud_remove_list = []
        client_remove_list = []
        client_download_list = []
        client_upload_list = []
        # Compare local file updates
        """
        * Case 1: Local has, cloud has, same md5, do nothing
        * Case 2: Local has, cloud has, different md5, local mtime is larger, upload
        * Case 3: Local has, cloud has, different md5, local mtime is smaller, download
        * Case 4: Local has, cloud does not have, upload pass
        * Case 5: Local does not have, cloud has, cloud mtime is smaller than local update time, delete from cloud
        * Case 6: Local does not have, cloud has, cloud mtime is larger than local update time, download
        * Case 7: Local has, cloud has, cloud is_deleted, local mtime is smaller, delete from local
        * Case 8: Local has, cloud has, cloud is_deleted, local mtime is larger, upload
        """
        # Benchmark against local files
        for key, value in client_dic.items():
            mtime_client = value["mtime"]
            if key in cloud_dic and not cloud_dic[key]["is_deleted"]:
                mtime_cloud = cloud_dic[key]["mtime"]
                if value["md5"] == cloud_dic[key]["md5"]:
                    # logger.info(f"item {key} is same")
                    pass
                elif mtime_client > mtime_cloud:
                    # logger.warning(f"{value['md5']} == {cloud_dic[key]['md5']}")
                    # logger.info(f"item {key} need upload, client {mtime_client}, cloud {mtime_cloud}")
                    client_upload_list.append(
                        {"addr": key}
                    )  # , 'md5':cloud_dic[key]['md5']})
                else:
                    # logger.info(f"item {key} need download, client {mtime_client}, cloud {mtime_cloud}")
                    client_download_list.append(
                        {"addr": key, "idx": str(cloud_dic[key]["idx"])}
                    )  # , 'md5':cloud_dic[key]['md5']})
            else:
                if (
                    key in cloud_dic
                ):  # It's available in the cloud, but it has been deleted
                    mtime_cloud = cloud_dic[key]["mtime"]
                    if mtime_client > mtime_cloud:
                        # logger.info(f"item {key} need upload, client {mtime_client}, cloud {mtime_cloud}")
                        client_upload_list.append(
                            {"addr": key}
                        )  # , 'md5':cloud_dic[key]['md5']})
                    else:
                        # logger.info(f"item {key} need client remove, client {mtime_client}, cloud {mtime_cloud}")
                        client_remove_list.append(
                            {"addr": key}
                        )  # , 'md5':cloud_dic[key]['md5']})
                else:
                    # logger.info(f"item {key} not found, need upload")
                    client_upload_list.append({"addr": key})
        # Benchmarked against cloud files
        count = 0
        for key, value in cloud_dic.items():
            if key in client_dic:  # has been processed above
                continue
            if not value["is_deleted"]:  # Is there a local in the cloud?
                if (
                    last_sync_time > value["mtime"]
                ):  # Local files deleted after last sync
                    cloud_remove_list.append(
                        {"addr": value["addr"], "idx": str(value["idx"])}
                    )
                    # Deletions should be more cautious, print logs, for test
                    if count < 10:  # Only display the first 10
                        logger.info(
                            f"item {key} need db delete, last sync:{last_sync_time}, db file:{value['mtime']}"
                        )
                    count += 1
                else:
                    logger.info(
                        f"item {key} need download, last sync:{last_sync_time}, db file:{value['mtime']}"
                    )
                    client_download_list.append(
                        {"addr": key, "idx": str(cloud_dic[key]["idx"])}
                    )  # , 'md5':value['md5']})
                    # logger.info(f"item {key} need client download, last sync:{last_sync_time}, db file:{value['mtime']}")

        if debug:
            logger.debug(
                f"client_remove_list {len(client_remove_list)}, {client_remove_list[:3]} ..."
            )
            logger.debug(
                f"client_download_list {len(client_download_list)}, {client_download_list[:3]} ..."
            )
            logger.debug(
                f"client_upload_list {len(client_upload_list)}, {client_upload_list[:3]} ..."
            )
            logger.debug(
                f"cloud_remove_list {len(cloud_remove_list)}, {cloud_remove_list[:3]} ..."
            )
        else:
            logger.debug(f"client_remove_list {len(client_remove_list)}")
            logger.debug(f"client_download_list {len(client_download_list)}")
            logger.debug(f"client_upload_list {len(client_upload_list)}")
            logger.debug(f"cloud_remove_list {len(cloud_remove_list)}")

        delete_entry(uid, cloud_remove_list)

        return HttpResponse(
            json.dumps(
                {
                    "status": "success",
                    "info": _("comparison_complete"),
                    "remove_list": client_remove_list,
                    "download_list": client_download_list,
                    "upload_list": client_upload_list,
                    "cloud_remove_list": cloud_remove_list,
                }
            )
        )
