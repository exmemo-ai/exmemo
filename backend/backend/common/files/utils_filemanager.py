"""
Provide file management functionality, support file address saving, use cloud storage
"""

import os
import minio
import shutil
import traceback
from loguru import logger
from minio.commonconfig import CopySource


class FileManager:
    def save_file(self, uid, filename, path):
        """
        Save File
        Args:
            uid: User ID
            filename: Name of the file to be saved
            path: Actual path of the file
        """
        raise NotImplementedError

    def get_file(self, uid, filename, path):
        """
        Get File
        Args:
            filename: The name of the file
            path: The file save path
        """
        raise NotImplementedError

    def delete_file(self, uid, filename):
        """
        Delete a file
        Args:
            filename: file name
        """
        raise NotImplementedError


class MinioFileManager:
    BUCKET_NAME = "dataforge"

    def __init__(self, minio_host=None, minio_access_key=None, minio_secret_key=None):
        if minio_host is None:
            minio_host = os.environ.get("MINIO_HOST")
        if minio_access_key is None:
            minio_access_key = os.environ.get("MINIO_ACCESS_KEY")
        if minio_secret_key is None:
            minio_secret_key = os.environ.get("MINIO_SECRET_KEY")
        logger.info(
            f"minio_host {minio_host}, minio_access_key {minio_access_key}, minio_secret_key {minio_secret_key}"
        )
        self.client = minio.Minio(
            minio_host, minio_access_key, minio_secret_key, secure=False
        )

    def save_file(self, uid, filename, path):
        try:
            if not self.client.bucket_exists(MinioFileManager.BUCKET_NAME):
                self.client.make_bucket(MinioFileManager.BUCKET_NAME)
            remote_path = f"{uid}/{filename}"
            self.client.fput_object(MinioFileManager.BUCKET_NAME, remote_path, path)
            return True
        except Exception as e:
            logger.warning(f"save_file failed {e}")
            return False

    def get_file(self, uid, filename, path):
        try:
            remote_path = f"{uid}/{filename}"
            self.client.fget_object(MinioFileManager.BUCKET_NAME, remote_path, path)
            return True
        except Exception as e:
            logger.warning(f"get_file failed {e}, filename {filename}, path {path}")
            return False

    def delete_file(self, uid, filename):
        try:
            remote_path = f"{uid}/{filename}"
            self.client.remove_object(MinioFileManager.BUCKET_NAME, remote_path)
            return True
        except Exception as e:
            logger.warning(f"delete_file failed {e}")
            return False

    def rename_file(self, uid, oldpath, newpath):
        try:
            self.client.copy_object(
                MinioFileManager.BUCKET_NAME,
                f"{uid}/{newpath}",
                CopySource(MinioFileManager.BUCKET_NAME, f"{uid}/{oldpath}"),
            )
            self.client.remove_object(MinioFileManager.BUCKET_NAME, f"{uid}/{oldpath}")
            return True
        except Exception as e:
            logger.warning(f"rename_file failed {e}")
            traceback.print_exc()
            return False


class LocalFileManager:
    def __init__(self, base_path):
        self.base_path = base_path

    def save_file(self, uid, filename, path):
        try:
            path_dst = os.path.join(self.base_path, uid, filename)
            file_dir = os.path.dirname(path_dst)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                logger.debug(f"create dir {file_dir}")
            if not os.path.exists(path_dst) or not os.path.samefile(path, path_dst):
                shutil.copyfile(path, path_dst)
            return True
        except Exception as e:
            logger.info(f"filename {filename}, path {path}, path_dst {path_dst}")
            traceback.print_exc()
            logger.warning(f"save_file failed {e}")
            return False

    def get_file(self, uid, filename, path):
        try:
            shutil.copyfile(f"{self.base_path}/{uid}/{filename}", path)
            return True
        except Exception as e:
            logger.warning(f"get_file failed {e}")
            return False

    def delete_file(self, uid, filename):
        try:
            path = f"{self.base_path}/{uid}/{filename}"
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.warning(f"delete_file failed {path} not exists")
            return True
        except Exception as e:
            logger.warning(f"delete_file failed {e}")
            return False

    def rename_file(self, uid, oldpath, newpath):
        real_oldpath = f"{self.base_path}/{uid}/{oldpath}"
        real_newpath = f"{self.base_path}/{uid}/{newpath}"
        try:
            target_dir = os.path.dirname(real_newpath)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            os.rename(real_oldpath, real_newpath)
            return True
        except Exception as e:
            logger.warning(f"rename_file failed {e}")
            return False


def get_file_manager():
    """
    Get File Manager
    """
    if os.environ.get("FILE_STORE") == "local":
        return LocalFileManager(os.environ.get("LOCAL_FILE_STORE_DIR"))
    else:
        return MinioFileManager()


def test():
    # import utils_filemanager
    manager = MinioFileManager("tencent.xyan666.com:9000", "root", "xy800811")
    manager.get_file("Mistake_Notes.txt", "/tmp/test.txt")
    manager.save_file("Mistake_Notes_2.txt", "/tmp/test.txt")
    manager.delete_file("Mistake_Notes_2.txt")
