import os
import unittest
from django.core.files.uploadedfile import SimpleUploadedFile
from .support import BaseTestCase


class FileManagerTestCase(BaseTestCase):
    def inner_upload_file(self):
        """
        Test uploading files through the web
        """
        file_data = b"This is some file data."
        file_name = "my_file.html"
        file = SimpleUploadedFile(file_name, file_data)
        response = self.client.post(
            "/api/entry/data/",
            {"from": "web", "etype": "file", "files": file, "filepaths": file_name},
            format="multipart",
        )
        data = self.parse_return_info(response)
        if "list" in data:
            return data["list"]
        AssertionError(False)

    def test_1_local_file(self):
        os.environ["FILE_STORE"] = "local"
        ret = self.inner_upload_file()
        AssertionError(len(ret) > 0)

    def test_2_minio_file(self):
        os.environ["FILE_STORE"] = "minio"
        ret = self.inner_upload_file()
        AssertionError(len(ret) > 0)


if __name__ == "__main__":
    unittest.main()
