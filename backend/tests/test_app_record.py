import unittest
from django.utils.translation import gettext as _
from .support import BaseTestCase


class RecordTestCase(BaseTestCase):
    def inner_add(self):
        """
        Record Exercise
        """
        response = self.do_message(
            {"content": _("record_exercise_running_5_kilometers")}
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
