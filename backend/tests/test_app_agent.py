"""
使用关键字匹配工具
是否能正确定位工具("/"开头)
调用工具是否引发死循环
几个重要使用场景是否能正常使用(记录，帮助，网页)
llm_tool 设置错误时是否能正常返回
"""

import unittest
from .support import BaseTestCase
from backend.common.llm import llm_hub
from backend.common.agent import agent_tools
from loguru import logger

class AgentTestCase(BaseTestCase):
    def test_basic_tool_call(self):
        """测试基本的工具调用"""
        response = self.do_message({"content": "/help"})
        self.parse_return_info(response)
        self.assertTrue(response.find("帮助信息") != -1)

    def test_note_creation(self):
        """测试笔记创建场景"""
        response = self.do_message({"content": "记录一下：今天学习了Python测试"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("已保存") != -1)

    def test_web_query(self):
        """测试网页查询场景"""
        response = self.do_message({"content": "查看最近保存的网页"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("网页列表") != -1)

    def test_invalid_tool(self):
        """测试无效工具调用"""
        response = self.do_message({"content": "/invalidtool"})
        info = self.parse_return_info(response)
        self.assertTrue(info.find("错误") != -1)

    def test_recursive_prevention(self):
        """测试防止工具递归调用"""
        response = self.do_message({"content": "递归调用/help"})
        info = self.parse_return_info(response)
        self.assertFalse(info.find("最大递归深度") == -1)

if __name__ == "__main__":
    unittest.main()

