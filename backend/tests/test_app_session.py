"""
清空会话
新建会话
列出会话
取会话中的消息
会话中添加消息
"""

import unittest
from .support import BaseTestCase
from backend.common.llm import llm_hub
from loguru import logger

class SessionTestCase(BaseTestCase):
    def test_clear_sessions(self):
        """测试清空会话"""
        response = self.do_message({"content": "/clear"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("已清空") != -1)

    def test_new_session(self):
        """测试新建会话"""
        response = self.do_message({"content": "/new"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("新会话") != -1)

    def test_list_sessions(self):
        """测试列出会话"""
        # 先创建一个新会话
        self.do_message({"content": "/new"})
        response = self.do_message({"content": "/list"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("会话列表") != -1)

    def test_session_messages(self):
        """测试会话消息操作"""
        # 创建新会话并发送消息
        self.do_message({"content": "/new"})
        response = self.do_message({"content": "你好"})
        info = self.parse_return_info(response)
        self.assertTrue(len(info) > 0)

    def test_long_conversation(self):
        """测试长对话场景"""
        # 清空后开始新对话
        self.do_message({"content": "/clear"})
        self.do_message({"content": "/new"})
        
        # 进行多轮对话
        response1 = self.do_message({"content": "我叫小明"})
        self.parse_return_info(response1)
        
        response2 = self.do_message({"content": "你还记得我的名字吗?"})
        info = self.parse_return_info(response2)
        self.assertTrue(info.find("小明") != -1)

if __name__ == "__main__":
    unittest.main()