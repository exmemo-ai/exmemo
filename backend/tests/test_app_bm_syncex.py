import unittest
from .support import BaseTestCase


class BmSyncexTestCase(BaseTestCase):
    def test_a_post(self):
        """
        Generate Bookmark
        """
        try:
            bookmarks = [
                {
                    "title": "XGBoost算法原理简介及调参_xg-boost怎么翻译-CSDN博客",
                    "url": "https://blog.csdn.net/ruding/article/details/78328835",
                    "add_date": "2024-06-25T03:15:52.000Z",
                    "path": "书签栏/论文相关/中文文献下载/github",
                }
            ]
            response = self.client.post("/api/bookmarks/", bookmarks, format="json")
            data = self.parse_return_info(response)
        except Exception as e:
            self.fail(f"POST request failed: {e}")


if __name__ == "__main__":
    unittest.main()
