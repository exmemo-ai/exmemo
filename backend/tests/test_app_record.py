import unittest
from django.utils.translation import gettext as _
from .support import BaseTestCase


class RecordTestCase(BaseTestCase):
    def inner_add(self):
        """
        Record Exercise
        """
        response = self.do_message(
            {"content": "记录 锻炼 跑步5公里"}
        )
        self.parse_return_info(response)

    def test_export(self):
        """
        Export Record Table
        """
        self.inner_add()

        response = self.client.get("/api/record/", {"rtype": "export"})
        ret = self.parse_return_file(
            response, "application/octet-stream", "/tmp/record.xlsx"
        )
        self.assertEqual(ret, True)


if __name__ == "__main__":
    unittest.main()
