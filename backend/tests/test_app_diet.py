import unittest
from .support import BaseTestCase
from django.utils.translation import gettext as _


class DietTestCase(BaseTestCase):
    def inner_add(self):
        """
        Record Diet
        """
        response = self.do_message({"content": _("diet_log_colon__apple_100g_comma__milk_100g")})
        info = self.parse_return_info(response)
        self.assertEqual(info.find(_("total_calories")) != -1, True)

    def inner_del(self):
        """
        Delete Diet
        """
        response = self.do_message({"content": _("delete_diet_apple")})
        info = self.parse_return_info(response)
        self.assertEqual(info.find(_("success")) != -1, True)

    def inner_analysis(self):
        """
        Statistics of Diet
        """
        response = self.do_message({"content": _("diet_statistics")})
        info = self.parse_return_info(response)
        self.assertEqual(info.find(_("total_calories")) != -1, True)

    def test_all(self):
        self.inner_add()
        self.inner_analysis()
        self.inner_del()


if __name__ == "__main__":
    unittest.main()
