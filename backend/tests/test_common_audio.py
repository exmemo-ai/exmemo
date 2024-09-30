from loguru import logger
from django.core.files.uploadedfile import SimpleUploadedFile
from .support import BaseTestCase


class AudioTestCase(BaseTestCase):
    def test_1_tts_xunfei(self):
        """
        Simple to speech: iFLYTEK
        """
        response = self.do_message({"content": "设置语音合成 讯飞"})
        self.parse_return_info(response)

        response = self.do_message({"content": "转音频 你好我是测试"})
        ret = self.parse_return_file(response, "audio/mpeg", "/tmp/audio_1.mp3")
        self.assertEqual(ret, True)

    def test_2_tts_mine(self):
        """
        Simple text-to-speech: Custom
        """
        response = self.do_message({"content": "设置语音合成 caicai"})
        self.parse_return_info(response)

        response = self.do_message({"content": "转音频 你好我是测试"})
        ret = self.parse_return_file(response, "audio/mpeg", "/tmp/audio_2.mp3")
        self.assertEqual(ret, True)

    def test_3_asr(self):
        """
        Speech to Text
        """
        with open("/tmp/audio_1.mp3", "rb") as f:
            file = SimpleUploadedFile("audio.mp3", f.read())
        response = self.do_message(
            {"rtype": "file", "from": "others", "file": file}, format="multipart"
        )
        self.parse_return_info(response)

        response = self.do_message({"content": "语音识别"})
        ret = self.parse_return_file(
            response, "application/octet-stream", "/tmp/file.txt"
        )
        self.assertEqual(ret, True)

        with open("/tmp/file.txt", "r") as f:
            content = f.read()
            logger.warning(f"recv {content}")
            self.assertEqual(content.find("你好我是测试") != -1, True)
