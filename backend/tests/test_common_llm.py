import unittest
from .support import BaseTestCase
from django.test import TestCase
from backend.common.llm import llm_hub
from backend.common.llm import llm_tools
from loguru import logger


class LLMTestCase(BaseTestCase):
    def test_message_chat(self):
        """
        chatgpt conversation
        """
        response = self.do_message({"content": "你好，你是什么模型"})
        self.parse_return_info(response)

    def test_message_chat_gemini(self):
        """
        gemini conversation
        """
        response = self.do_message({"content": "gemini 你好，你是什么模型"})
        self.parse_return_info(response)

    def test_message_chat_gpt4(self):
        """
        gpt4 conversation
        """
        response = self.do_message({"content": "gpt4 你好，你是什么模型"})
        self.parse_return_info(response)

    def test_message_long_chat(self):
        response = self.do_message({"content": "你好，我是王小明"})
        self.parse_return_info(response)
        response = self.do_message({"content": "今天天气怎么样"})
        self.parse_return_info(response)
        response = self.do_message({"content": "你知道我的名字吗"})
        info = self.parse_return_info(response)
        self.assertEqual(info.find("王小明") != -1, True)


class AllLLMTestCase(TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        self.user_id = "testuser"
        super().__init__(methodName)

    def test_1_query(self):
        role = "Assistant"
        question = "Who model are you?"
        app = "test"
        debug = False

        llms = llm_tools.get_llm_list()
        for llm in llms:
            # print(type(result), isinstance(result, tuple))
            print("@@@@@@@@@@@@@@@@@@@@")
            print("llm:", llm["label"], llm["value"])
            ret, answer, dic = llm_hub.llm_query(
                self.user_id, role, question, app, llm["value"], debug
            )
            print("q:  ", question)
            if ret:
                print(
                    "a:  ",
                    ret,
                    answer[:50].replace("\n", " ").replace("\r", " "),
                    "... tokens:",
                    dic["token_count"],
                    "duration:",
                    dic["duration"],
                )
            else:
                print("a:  ", ret, answer)
            if not ret:
                logger.warning(f"return wrong")

    def get_note_type(
        self,
        note,
        types=["待办", "想法", "阅读", "网页", "技术", "心情", "引用", "摘录"],
        default_type="unknown",
        debug=False,
    ):
        if note is None or len(note) == 0 or types is None or len(types) == 0:
            return default_type
        sys_info = "You are a private secretary"
        json_str = "{'type':'" + types[0] + "unknown'}"
        text = f'请给下文归类: {note}, 类别范围：{",".join(types)}。请用json串回答，例如：{json_str}，不要返回其他内容。'
        return sys_info, text

    def test_2_json(self):
        role, question = self.get_note_type("穷查理宝典，这本书的组织结构还挺有意思的")
        app = "test"
        debug = False

        llms = llm_tools.get_llm_list()
        for llm in llms:
            ret, answer, dic = llm_hub.llm_query_json(
                self.user_id, role, question, app, llm["value"], debug
            )
            # print(type(result), isinstance(result, tuple))
            print("@@@@@@@@@@@@@@@@@@@@")
            print("llm: ", llm["label"], llm["value"])
            print("q:   ", question)
            print(
                "a:   ",
                ret,
                answer,
                "token",
                dic["token_count"],
                "dur",
                dic["duration"],
            )
            right = answer == {"type": "阅读"}
            if ret == False or not right:
                logger.warning(f"return wrong")
            else:
                print("right:", right)

    def test_3_chat(self):
        sid = "session_id_tmp"
        content1 = "I'm Xieyan, a software engineer."
        content2 = "What's my name? Please give a simple answer."

        llms = llm_tools.get_llm_list()
        for llm in llms:
            ret, result = llm_hub.chat(
                self.user_id, sid, content1, engine_type=llm["value"]
            )
            ret, result = llm_hub.chat(
                self.user_id, sid, content2, engine_type=llm["value"]
            )
            print("@@@@@@@@@@@@@@@@@@")
            print(llm["label"], result[:50].replace("\n", " ").replace("\r", ""), "...")
            right = result.find("Xieyan") != -1
            if ret == False or not right:
                logger.warning(f"return wrong, length {len(result)}")
            else:
                print("right:", right, ", length", len(result))

        # self.assertTrue(result[0])
        # self.assertIsInstance(result[1], str)


if __name__ == "__main__":
    unittest.main()
