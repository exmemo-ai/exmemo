""" if call test file directly: python tests/test_app_diet.py, open it
import sys
import os

DIR = '/opt/exmemo/backend/'
if DIR not in sys.path:
    sys.path.append(DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'True'
import django
django.setup()
"""

import json
from loguru import logger
from django.contrib.auth.models import User as SystemUser
from backend.common.user.views import LoginView
from rest_framework.test import APITestCase, APIClient
from knox.models import AuthToken


class BaseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        username = "testuser"
        password = "testpassword"
        LoginView.create_user(username, password)
        user = SystemUser.objects.get(username=username)
        token = AuthToken.objects.create(user)[1]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

    def do_message(self, info, **argv):
        return self.client.post("/api/message/", info, **argv)

    def parse_return_info(self, response):
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "success")
        logger.info(f"return {data}")
        if "info" in data:
            return data["info"]
        elif "type" in data and data["type"] == "json" and "content" in data:
            return data["content"]["info"]
        return data

    def parse_return_file(self, response, format, path):
        self.assertEqual(response.status_code, 200)
        content_type = response.headers["Content-Type"]
        logger.info(f"recv content_type {content_type}")
        if format is None or format in content_type:
            with open(path, "wb") as f:
                if response.streaming:
                    for chunk in response.streaming_content:
                        f.write(chunk)
                else:
                    f.write(response.content)
                logger.info(f"recv {format} file {path}, size {f.tell()}")
                return True
        else:
            self.parse_return_info(response)
            return False
