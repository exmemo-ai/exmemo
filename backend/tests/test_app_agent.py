import unittest
from .support import BaseTestCase

class AgentTestCase(BaseTestCase):
    def test_basic_tool_call(self):
        response = self.do_message({"content": "/help"})
        info = self.parse_return_info(response)
        print(info)
        self.assertTrue(info.find("请选择") != -1)
        response = self.do_message({"content": "1"})
        info = self.parse_return_info(response)
        print(info)
    
    def test_note_creation(self):
        response = self.do_message({"content": "记录 今天学习了Python测试"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("记录成功") != -1)

        response = self.do_message({"content": "/找数据 测试"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("测试") != -1)

    def test_web_collect(self):
        response = self.do_message({"content": "http://www.baidu.com"})
        info = self.parse_return_info(response)
        print(info)
        response = self.do_message({"content": "2"})
        info = self.parse_return_info(response)
        print(info)

if __name__ == "__main__":
    unittest.main()

