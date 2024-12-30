import json
from .support import BaseTestCase
from rest_framework.test import APIClient
from django.utils.translation import gettext as _


class UserManagerTestCase(BaseTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_3_login(self):
        response = self.do_message(
            {"content": "登录：xieyan, 1234567", "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        if isinstance(ret, dict):
            dic = ret
        else:
            dic = json.loads(ret)
        self.assertEqual(dic["user_id"] == "xieyan", dic["password"] == "1234567")

    def test_2_register(self):
        response = self.do_message(
            {"content": "注册：xieyan, 1234567", "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        if isinstance(ret, dict):
            dic = ret
        else:
            dic = json.loads(ret)
        self.assertEqual(dic["user_id"] == "xieyan", dic["password"] == "1234567")
        response = self.do_message(
            {"content": "注册：xieyan, 1234567", "user_name": "anyone"}
        )
        ret = self.parse_return_info(response) # ret is a string

    def test_4_change_password(self):
        response = self.do_message(
            {
                "content": "修改密码：xieyan, 原密码 1234567 新密码 123456",
                "user_name": "anyone",
            }
        )
        ret = self.parse_return_info(response)

        response = self.do_message(
            {"content": _("registration_colon__xieyan_comma__1234567"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        response = self.do_message(
            {
                "content": "修改密码：xieyan, 原密码 1234567 新密码 123456",
                "user_name": "anyone",
            }
        )
        ret = self.parse_return_info(response)

        response = self.do_message(
            {"content": "修改密码：xieyan, 2314", "user_name": "anyone"}
        )
        ret = self.parse_return_info(response) # ret is a string

    def test_1_others(self):
        response = self.do_message(
            {
                "content": "化学什么时候用烧杯，什么时候用试管",
                "user_name": "anyone",
            }
        )
        # response = self.do_message({'content':'你好', 'user_name':'anyone'})
        ret = self.parse_return_info(response)
        print(ret)


# ret = chat('xieyan', '你好')
