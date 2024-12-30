import os
import time
import hashlib
import unittest
import json
from loguru import logger
from django.core.files.uploadedfile import SimpleUploadedFile
from .support import BaseTestCase

TMP_DIR = "/tmp/tmp"


class SyncTestCase(BaseTestCase):
    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        if not os.path.exists(TMP_DIR):
            os.mkdir(TMP_DIR)

    def inner_sync_upload(self):
        """
        create local files, and upload
        file1.txt: local file = remote file
        file2.txt: local file newer than remote file
        file3.txt: local file older than remote file
        file4.txt: local file only
        file5.txt: local file -> remote file -> rm local file: rm remote file
        file6.txt: local file -> remote file(mtime+) -> rm local file: need download to local
        file7.txt: local file -> remote file -> rm db file, remote op mtime+: rm local file
        file8.txt: local file -> remote file -> rm db file, remote op mtime-: upload
        """
        for i in range(1, 9):
            path = f"{TMP_DIR}/file{i}.txt"
            filename = f"file{i}.txt"
            with open(path, "w") as f:
                f.write(f"file{i}_base")
            if i == 4:
                continue
            with open(path, "rb") as f:
                file_data = SimpleUploadedFile(path, f.read())
                mtime = int(os.path.getmtime(path) * 1000)
                response = self.client.post(
                    "/api/entry/data/",
                    {
                        "from": "web",
                        "etype": "note",
                        "files": file_data,
                        "filepaths": filename,
                    },
                    format="multipart",
                )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data["status"], "success")
            if i == 2:
                with open(path, "w") as f:
                    f.write(f"file{i}_base_new")
                mtime = time.time() + 3600
                os.utime(path, (mtime, mtime))
            if i == 3:
                with open(path, "w") as f:
                    f.write(f"file{i}_base_new")
                mtime = time.time() - 3600
                os.utime(path, (mtime, mtime))
            if i == 5 or i == 6:
                os.remove(path)
            if i == 7:
                self.inner_sync_delete(7)
            if i == 8:
                self.inner_sync_delete(8)
                mtime = time.time() + 3600
                os.utime(path, (mtime, mtime))

    def inner_sync_delete(self, i):
        """
        test delete api, and create test environment
        """
        path = f"file{i}.txt"
        idx = self.inner_get_idx_by_filepath(path)
        response = self.client.delete(f"/api/entry/data/{idx}/")
        self.assertEqual(response.status_code, 200)

    def inner_sync_download(self, i):
        """
        test download api
        """
        path = f"file{i}.txt"
        idx = self.inner_get_idx_by_filepath(path)
        abspath = f"/tmp/file{i}.txt_download"
        response = self.client.get(f"/api/entry/data/{idx}/download/")
        self.assertEqual(response.status_code, 200)
        if response.streaming:
            file_content = b"".join(response.streaming_content)
        else:
            file_content = response.content
        with open(abspath, "wb") as f:
            f.write(file_content)

    def inner_get_idx_by_filepath(self, rpath):
        idx = None
        response = self.client.get(f"/api/entry/data/")
        self.assertEqual(response.status_code, 200)

        print(f"list has {response.data['count']} items")
        for x in response.data["results"]:
            if x["addr"] == rpath:
                idx = x["idx"]
        self.assertIsNotNone(idx)
        return idx

    def inner_update_item(self, i):
        """
        Add Record
        """
        path = f"file{i}.txt"
        idx = self.inner_get_idx_by_filepath(path)
        data = {"raw": "new info"}
        url = f"/api/entry/data/{idx}/"
        response = self.client.put(url, data)
        print(response)
        self.assertEqual(response.status_code, 200)

    def get_file_list(self, list):
        """
        get file list return sync return data
        """
        ret = []
        for item in list:
            if "addr" in item:
                ret.append(item["addr"])
        ret = sorted(ret)
        return ret

    def test_sync_compare(self):
        """
        compare local files with remote files
        """
        self.inner_sync_upload()
        files = []
        # visit all files in TMP_DIR
        for f in os.listdir(TMP_DIR):
            path = f
            abspath = f"{TMP_DIR}/{f}"
            if os.path.isfile(abspath):
                mtime = int(os.path.getmtime(abspath) * 1000)
                with open(abspath, "rb") as f:
                    raw = f.read()
                md5 = hashlib.md5(raw).hexdigest()
                files.append({"path": path, "mtime": mtime, "md5": md5})
        timestamp = int(time.time() * 1000)
        self.inner_update_item(6)  # later than timestamp
        response = self.client.post(
            "/api/sync/",
            {
                "rtype": "compare",
                "files": json.dumps(files),
                "last_sync_time": timestamp,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        logger.info(f"data: {data}")
        self.assertEqual(data["status"], "success")
        self.assertEqual(self.get_file_list(data["remove_list"]), ["file7.txt"])
        self.assertEqual(
            self.get_file_list(data["download_list"]), ["file3.txt", "file6.txt"]
        )
        self.assertEqual(
            self.get_file_list(data["upload_list"]),
            ["file2.txt", "file4.txt", "file8.txt"],
        )
        #
        self.inner_sync_download(3)


if __name__ == "__main__":
    unittest.main()
