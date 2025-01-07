import unittest
from .support import BaseTestCase

class SessionTestCase(BaseTestCase):
    def test_1_test_sessions(self):
        response1 = self.do_message({"content": "我叫小明"})
        self.parse_return_info(response1)

        response = self.client.post("/api/message/session/", {"rtype": "get_sessions"})
        info = self.parse_return_info(response)
        print(info)
        self.assertTrue(len(info["sessions"]) > 0)

        sid = info["sessions"][0]["sid"]
        response = self.client.post("/api/message/session/", {"rtype": "get_messages", "sid": sid})
        info = self.parse_return_info(response)
        print(info)
        self.assertTrue(len(info["messages"]) > 0)

        response = self.client.post("/api/message/session/", {"rtype": "save_session", "sid": sid})
        info = self.parse_return_info(response)
        print(info)

        response = self.client.post("/api/message/session/", {"rtype": "get_current_session"})
        info = self.parse_return_info(response)
        print(info)

        response = self.client.post("/api/message/session/", {"rtype": "clear_session", "sid": sid})
        info = self.parse_return_info(response)
        print(info)


if __name__ == "__main__":
    unittest.main() 