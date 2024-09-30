import json
from .support import BaseTestCase
from rest_framework.test import APIClient
from django.utils.translation import gettext as _


class UserManagerTestCase(BaseTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login(self):
        response = self.do_message(
            {"content": _("login_colon__xieyan_comma__1234567"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        dic = json.loads(ret)
        self.assertEqual(dic["user_id"] == "xieyan", dic["password"] == "1234567")

    def test_register(self):
        response = self.do_message(
            {"content": _("registration_colon__xieyan_comma__1234567"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        dic = json.loads(ret)
        self.assertEqual(dic["username"] == "xieyan", dic["password"] == "1234567")
        response = self.do_message(
            {"content": _("registration_colon__xieyan_comma__1234567"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        self.assertEqual(ret, _("username_already_exists"))

    def test_change_password(self):
        response = self.do_message(
            {
                "content": _(
                    "change_password_colon__xieyan_comma__old_password_1234567_new_password_123456"
                ),
                "user_name": "anyone",
            }
        )
        ret = self.parse_return_info(response)
        self.assertEqual(ret, _("user_does_not_exist"))

        response = self.do_message(
            {"content": _("registration_colon__xieyan_comma__1234567"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        response = self.do_message(
            {
                "content": _(
                    "change_password_colon__xieyan_comma__old_password_1234567_new_password_123456"
                ),
                "user_name": "anyone",
            }
        )
        ret = self.parse_return_info(response)
        self.assertEqual(ret, _("successfully_set"))

        response = self.do_message(
            {"content": _("change_password_colon__xieyan_comma__2314"), "user_name": "anyone"}
        )
        ret = self.parse_return_info(response)
        self.assertEqual(
            (ret == _("original_password_error") or ret == _("old_password_is_empty")),
            True,
        )

    def test_others(self):
        response = self.do_message(
            {
                "content": _(
                    "when_to_use_a_beaker_and_when_to_use_a_test_tube_in_chemistry"
                ),
                "user_name": "anyone",
            }
        )
        # response = self.do_message({'content':'你好', 'user_name':'anyone'})
        ret = self.parse_return_info(response)
        print(ret)


# ret = chat('xieyan', '你好')
