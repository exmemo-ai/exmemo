import os
import json
import unittest
from loguru import logger
from django.core.files.uploadedfile import SimpleUploadedFile
from .support import BaseTestCase


class DataFileTestCase(BaseTestCase):
    def test_1_upload_by_frontend(self):
        """
        Test uploading files via web
        """
        file_data = b"This is some file data."
        file_name = "my_file.html"
        file = SimpleUploadedFile(file_name, file_data)
        response = self.client.post(
            "/api/entry/data/",
            {"from": "web", "etype": "file", "files": file, "filepaths": file_name},
            format="multipart",
        )
        self.parse_return_info(response)

    def test_2_upload_by_wechat(self):
        """
        Test uploading files through other methods
        """
        file_data = b"This is some file data."
        file_name = "my_file.html"
        file = SimpleUploadedFile(file_name, file_data)

        response = self.do_message(
            {"rtype": "file", "from": "others", "file": file}, format="multipart"
        )
        self.parse_return_info(response)

        response = self.do_message({"content": "收藏文件"})
        self.parse_return_info(response)

    def test_3_get_file_list(self):
        """
        Get file list, download file, delete file
        """
        self.test_1_upload_by_frontend()

        response = self.client.get("/api/entry/data/")
        print(f"list has {response.data['count']} items")
        title = None
        idx = None
        for x in response.data["results"]:
            print("@@@@", x)
            if "title" in x and "idx" in x:
                title = x["title"]
                idx = x["idx"]
                logger.warning(f"item idx {idx} title {title}")
                break

        # download file
        if idx is not None:
            response = self.client.get(f"/api/entry/data/{idx}/download/")
            ret = self.parse_return_file(response, None, f"/tmp/tmp.txt")
            self.assertEqual(ret, True)

        # delete file
        if idx is not None:
            print(f"delete item idx {idx}")
            response = self.client.delete(f"/api/entry/data/{idx}/")
            self.parse_return_info(response)


class DataWebTestCase(BaseTestCase):
    def test_add_web1(self):
        """
        Send Webpage
        """
        response = self.do_message({"content": "http://www.baidu.com"})
        self.parse_return_info(response)

    def test_add_web2(self):
        """
        Bookmark Page
        """
        response = self.do_message({"content": "收藏网页 http://www.baidu.com"})
        self.parse_return_info(response)


class DataRecordTestCase(BaseTestCase):
    def inner_add(self, idx=None):
        """
        Add Record
        """
        data = {
            "ctype": "type1",
            "etype": "record",
            "title": "Test Title",
            "atype": "主观",
            "tags": "tag1,tag2",
            "status": "todo",
            "level": "1",
            "raw": "Test Content",
        }
        if idx is None:
            url = "/api/entry/data/"
            response = self.client.post(url, data)
        else:
            url = f"/api/entry/data/{idx}/"
            response = self.client.put(url, data)
            # print('request', request, request.data)
        self.parse_return_info(response)

    def test_2_list(self):
        """
        Get record column for, retrieve record, delete record; need to add record first before retrieving and deleting
        """
        self.inner_add()

        response = self.client.get("/api/entry/data/", {"etype": "record"})
        self.assertEqual(response.status_code, 200)

        print(f"list has {response.data['count']} items")
        title = None
        idx = None
        for x in response.data["results"]:
            print("@@@@", x)
            if "title" in x and "idx" in x:
                title = x["title"]
                idx = x["idx"]
                logger.warning(f"item idx {idx} title {title}")
                break

        # test retrieve, return item data
        if idx is not None:
            print(f"retrieve item idx {idx}")
            response = self.client.get(f"/api/entry/data/{idx}/")
            self.assertEqual(response.status_code, 200)
            logger.warning(f"data {response.data}")

        # test edit
        if idx is not None:
            print(f"edit item idx {idx}")
            self.inner_add(idx)

        # test delete
        if idx is not None:
            print(f"delete item idx {idx}")
            response = self.client.delete(f"/api/entry/data/{idx}/")
            self.parse_return_info(response)


class EmbeddingTestCase(BaseTestCase):
    def inner_add_data(self):
        response = self.do_message({"content": "记录 今天天气不错"})
        self.parse_return_info(response)

    def inner_check_embedding(self):
        response = self.client.post("/api/sync/", {"rtype": "check_embedding"})
        data = self.parse_return_info(response)
        if "list" in data:
            return data["list"]
        return []

    def inner_regen_embedding(self, filelist):
        if len(filelist) == 0:
            return
        print("regen embedding", filelist)
        response = self.client.post(
            "/api/sync/",
            {"rtype": "regerate_embedding", "addr_list": json.dumps(filelist)},
        )
        self.parse_return_info(response)

    def test_embedding(self):
        os.environ["USE_EMBEDDING"] = "True"
        os.environ["EMBEDDING_TYPE"] = "ollama"
        os.environ["EMBEDDING_URL"] = "http://192.168.10.168:11434"
        os.environ["EMBEDDING_MODEL"] = "znbang/bge:small-zh-v1.5-f16"
        self.inner_add_data()
        os.environ["EMBEDDING_MODEL"] = "mofanke/dmeta-embedding-zh"
        addrlist = self.inner_check_embedding()
        self.inner_regen_embedding(addrlist)


if __name__ == "__main__":
    unittest.main()
