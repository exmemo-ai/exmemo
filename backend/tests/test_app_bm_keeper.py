import unittest
from .support import BaseTestCase
from app_dataforge.models import StoreEntry
from django.utils import timezone
from app_bm_syncex.views import SOURCE
import json
import uuid
from django.contrib.auth.models import User as SystemUser


class BMKeeperBaseTestCase(BaseTestCase):
    """Abstract base test case for bookmark tests"""
    def setUp(self):
        super().setUp()
        self.test_user = SystemUser.objects.get(username="testuser")


class BMKeeperNavigationTestCase(BMKeeperBaseTestCase):
    """Test cases for navigation related features"""
    def setUp(self):
        super().setUp()
        self._create_navigation_test_data()
    
    def _create_navigation_test_data(self):
        """Create test data specific to navigation tests"""
        self.nav_bookmarks = []
        self.bookmark_ids = []  # 新增：存储书签ID的列表
        current_time = timezone.now()
        
        nav_data = [
            {   
                "title": "Navigation Test 1",
                "addr": "https://nav1.com",
                "meta": {"custom_order": True, "clicks": 15},
            },
            {
                "title": "Navigation Test 2",
                "addr": "https://nav2.com",
                "meta": {"custom_order": True, "clicks": 8}
            },
            {
                "title": "Navigation Test 3",
                "addr": "https://nav3.com",
                "meta": {"custom_order": False, "clicks": 3}
            }
        ]
        
        for data in nav_data:
            bookmark = StoreEntry.objects.create(
                idx=str(uuid.uuid4()),
                user_id=self.test_user.username,
                title=data["title"],
                addr=data["addr"],
                source=SOURCE,
                is_deleted="f",
                status="collect",
                created_time=current_time,
                meta=data["meta"]
            )
            self.nav_bookmarks.append(bookmark)

    def test_a_navigation_get(self):
        """Test getting navigation bookmarks"""
        try:
            # Test default limit
            response = self.client.get("/api/keeper/", {"type": "navigation"})
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 3)
            
            # Test custom limit
            response = self.client.get("/api/keeper/", {
                "type": "navigation",
                "param": "2"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 2)
        except Exception as e:
            self.fail(f"GET navigation request failed: {e}")

    def test_b_custom_order_get(self):
        """Test getting custom ordered bookmarks"""
        try:
            response = self.client.get("/api/keeper/custom-order/")
            data = self.parse_return_info(response)
            
            # Verify response structure and data
            self.assertIn("data", data)
            self.assertEqual(len(data["data"]), 2)
            
            if len(data["data"]) > 0:
                bookmark = data["data"][0]
                self.assertIn("id", bookmark)
                self.assertIn("title", bookmark)
                self.assertIn("url", bookmark)
                self.assertIn("created_at", bookmark)
                self.assertIn("meta", bookmark)
                self.assertTrue(bookmark["meta"]["custom_order"])
                
        except Exception as e:
            self.fail(f"GET custom-order request failed: {e}")

    def test_c_custom_order_post_single(self):
        """Test updating custom order for a single bookmark"""
        try:
            # update custom order for a single bookmark
            response = self.client.post("/api/keeper/custom-order/", {
                "singleBookmark": True,
                "bookmarkId": self.nav_bookmarks[2].idx,
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # test if the bookmark's custom_order has been set to True
            bookmark = StoreEntry.objects.get(idx=self.nav_bookmarks[2].idx)
            self.assertTrue(bookmark.meta.get("custom_order"))
            
        except Exception as e:
            self.fail(f"POST single custom-order request failed: {e}")

    def test_d_custom_order_post_remove(self):
        """Test removing a bookmark from custom order"""
        try:
            response = self.client.post("/api/keeper/custom-order/", {
                 "removeId": self.nav_bookmarks[0].idx
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # test if the bookmark's custom_order has been set to False
            bookmark = StoreEntry.objects.get(idx=self.nav_bookmarks[0].idx)
            self.assertFalse(bookmark.meta.get("custom_order"))
            
        except Exception as e:
            self.fail(f"POST remove custom-order request failed: {e}")


class BMKeeperSearchTestCase(BMKeeperBaseTestCase):
    """Test cases for search features"""
    def setUp(self):
        super().setUp()
        self._create_search_test_data()
    
    def _create_search_test_data(self):
        """Create test data specific to search tests"""
        self.search_bookmarks = []
        
        search_data = [
            {
                "title": "Python Programming Guide",
                "addr": "https://python.org/guide",
                "ctype": "programming,python,guide",
            },
            {
                "title": "Django Web Framework",
                "addr": "https://djangoproject.com",
                "ctype": "programming,web,django",
            },
            {
                "title": "Machine Learning with Python",
                "addr": "https://ml-python.com",
                "ctype": "programming,ml,python",
            }
        ]
        
        for data in search_data:
            bookmark = StoreEntry.objects.create(
                idx=str(uuid.uuid4()),
                user_id=self.test_user.username,
                title=data["title"],
                addr=data["addr"],
                source=SOURCE,
                is_deleted="f",
                status="collect",
                created_time=timezone.now(),
                ctype=data["ctype"],
            )
            self.search_bookmarks.append(bookmark)

    def test_a_search_by_keyword(self):
        """Test search by keyword in title or URL"""
        try:
            response = self.client.get("/api/keeper/", {
                "type": "search",
                "param": "Python"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 2)
            titles = [bm["title"] for bm in data["data"]]
            self.assertTrue("Python Programming Guide" in titles)
            self.assertTrue("Machine Learning with Python" in titles)

            response = self.client.get("/api/keeper/", {
                "type": "search",
                "param": "django"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["title"], "Django Web Framework")
        except Exception as e:
            self.fail(f"Search by keyword test failed: {e}")

    def test_b_search_by_tag(self):
        """Test search by tag"""
        try:
            response = self.client.get("/api/keeper/", {
                "type": "search",
                "param": "programming"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 3)  # 所有条目都有programming标签
            
            response = self.client.get("/api/keeper/", {
                "type": "search",
                "param": "ml"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 1)
            self.assertEqual(data["data"][0]["title"], "Machine Learning with Python")
        except Exception as e:
            self.fail(f"Search by tag test failed: {e}")


    def test_c_search_no_results(self):
        """Test search with no matching results"""
        try:
            response = self.client.get("/api/keeper/", {
                "type": "search",
                "param": "nonexistent"
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 0)
        except Exception as e:
            self.fail(f"Search no results test failed: {e}")


class BMKeeperTreeTestCase(BMKeeperBaseTestCase):
    """Test cases for tree view features"""
    def setUp(self):
        super().setUp()
        self._create_tree_test_data()
    
    def _create_tree_test_data(self):
        """Create test data specific to tree view tests"""
        self.tree_bookmarks = []
        
        tree_data = [
            {
                "title": "Root Bookmark",
                "addr": "https://root.com",
                "path": "chrome/书签栏/Root Bookmark",
                "meta": {"resource_path": "chrome/书签栏/Root Bookmark", "update_path": "chrome/书签栏/Root Bookmark"}
            },
            {
                "title": "Tech Bookmark",
                "addr": "https://tech.com",
                "path": "chrome/书签栏/技术/Tech Bookmark",
                "meta": {"resource_path": "chrome/书签栏/技术/Tech Bookmark", "update_path": "chrome/书签栏/技术/Tech Bookmark"}
            },
            {
                "title": "Python Doc",
                "addr": "https://python-doc.com",
                "path": "chrome/书签栏/技术/Python/Python Doc",
                "meta": {"resource_path": "chrome/书签栏/技术/Python/Python Doc", "update_path": "chrome/书签栏/技术/Python/Python Doc"}
            }
        ]
        
        for data in tree_data:
            bookmark = StoreEntry.objects.create(
                idx=str(uuid.uuid4()),
                user_id=self.test_user.username,
                title=data["title"],
                addr=data["addr"],
                source=SOURCE,
                is_deleted="f",
                status="collect", 
                created_time=timezone.now(),
                path=data["path"],
                meta=data["meta"]
            )
            self.tree_bookmarks.append(bookmark)

    def test_a_edit_title(self):
        """Test editing bookmark title in tree view"""
        try:
            bookmark = self.tree_bookmarks[0]
            original_path = bookmark.path
            new_title = "Updated Root Bookmark"
            
            response = self.client.put("/api/keeper/", {
                "id": bookmark.idx,
                "title": new_title
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # Verify database changes
            updated_bookmark = StoreEntry.objects.get(idx=bookmark.idx)
            self.assertEqual(updated_bookmark.title, new_title)
            
        except Exception as e:
            self.fail(f"Tree edit title test failed: {e}")

    def test_b_edit_url(self):
        """Test editing bookmark URL in tree view"""
        try:
            bookmark = self.tree_bookmarks[1]
            new_url = "https://updated-tech.com"
            
            response = self.client.put("/api/keeper/", {
                "id": bookmark.idx,
                "url": new_url
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # Verify database changes
            updated_bookmark = StoreEntry.objects.get(idx=bookmark.idx)
            self.assertEqual(updated_bookmark.addr, new_url)
            
        except Exception as e:
            self.fail(f"Tree edit URL test failed: {e}")

    def test_c_edit_folder(self):
        """Test editing bookmark folder in tree view"""
        try:
            bookmark = self.tree_bookmarks[2]
            new_folder = "chrome/书签栏/技术/JavaScript/Python Doc"
            
            response = self.client.put("/api/keeper/", {
                "id": bookmark.idx,
                "folder": new_folder
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # Verify database changes
            updated_bookmark = StoreEntry.objects.get(idx=bookmark.idx)
            expected_path = f"{new_folder}"
            self.assertEqual(updated_bookmark.path, expected_path)
            self.assertEqual(updated_bookmark.meta["update_path"], expected_path)
            
        except Exception as e:
            self.fail(f"Tree edit folder test failed: {e}")

    def test_d_edit_multiple(self):
        """Test editing multiple fields simultaneously in tree view"""
        try:
            bookmark = self.tree_bookmarks[1]
            new_title = "Updated Tech Doc"
            new_url = "https://updated-tech-doc.com"
            new_folder = "chrome/书签栏/Documentation/Updated Tech Doc"
            
            response = self.client.put("/api/keeper/", {
                "id": bookmark.idx,
                "title": new_title,
                "url": new_url,
                "folder": new_folder
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            # Verify database changes
            updated_bookmark = StoreEntry.objects.get(idx=bookmark.idx)
            expected_path = new_folder
            self.assertEqual(updated_bookmark.title, new_title)
            self.assertEqual(updated_bookmark.addr, new_url)
            self.assertEqual(updated_bookmark.path, expected_path)
            self.assertEqual(updated_bookmark.meta["update_path"], expected_path)
            
        except Exception as e:
            self.fail(f"Tree edit multiple fields test failed: {e}")


class BMKeeperReadLaterTestCase(BMKeeperBaseTestCase):
    """Test cases for read later features"""
    def setUp(self):
        super().setUp()
        self._create_readlater_test_data()
    
    def _create_readlater_test_data(self):
        """Create test data specific to read later tests"""
        self.readlater_bookmarks = []
        current_time = timezone.now()
        
        readlater_data = [
            {   
                "title": "Read Later Test 1",
                "addr": "https://readlater1.com",
                "etype": "web",
                "status": "todo",
                "path": "chrome/书签栏/待读/Read Later Test 1"
            },
            {
                "title": "Read Later Test 2",
                "addr": "https://readlater2.com",
                "etype": "note",
                "status": "todo",
                "path": "chrome/书签栏/待读/Read Later Test 2"
            },
            {
                "title": "Read Later Test 3",
                "addr": "https://readlater3.com",
                "etype": "web",
                "status": "todo",
                "path": "chrome/书签栏/待读/Read Later Test 3"
            }
        ]
        
        for data in readlater_data:
            bookmark = StoreEntry.objects.create(
                idx=str(uuid.uuid4()),
                user_id=self.test_user.username,
                block_id=0,
                title=data["title"],
                addr=data["addr"],
                source=SOURCE,
                is_deleted="f",
                status=data["status"],
                etype=data["etype"],
                created_time=current_time,
                path=data["path"]
            )
            self.readlater_bookmarks.append(bookmark)

    def test_a_readlater_get(self):
        """Test getting read later bookmarks"""
        try:
            # Test default pagination
            response = self.client.get("/api/keeper/", {"type": "readlater"})
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 2)
            self.assertEqual(data["total"], 2)
            self.assertEqual(data["current_page"], 1)
            
            # Test custom pagination
            response = self.client.get("/api/keeper/", {
                "type": "readlater",
                "page": 1,
                "page_size": 2
            })
            data = self.parse_return_info(response)
            self.assertEqual(len(data["data"]), 2)
            self.assertEqual(data["total"], 2)
            self.assertEqual(data["current_page"], 1)
        except Exception as e:
            self.fail(f"GET readlater request failed: {e}")

    def test_d_readlater_edit(self):
        """Test editing read later bookmark title and tags"""
        try:
            bookmark_id = self.readlater_bookmarks[0].idx
            original_bookmark = StoreEntry.objects.get(idx=bookmark_id)
            newer_title = "Updated Both Title and Tags"
            tags = "test,readlater,important"
            response = self.client.put("/api/keeper/", {
                "type": "readlater",
                "id": bookmark_id,
                "title": newer_title,
                "tags": tags
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            final_bookmark = StoreEntry.objects.get(idx=bookmark_id)
            self.assertEqual(final_bookmark.title, newer_title)
            self.assertEqual(final_bookmark.ctype, tags)
        except Exception as e:
            self.fail(f"PUT readlater edit request failed: {e}")

    def test_e_readlater_move(self):
        """Test moving read later bookmark to a folder"""
        try:
            # Test moving from readlater folder to root folder
            bookmark_id = self.readlater_bookmarks[0].idx
            original_path = self.readlater_bookmarks[0].path
            original_status = self.readlater_bookmarks[0].status
            
            response = self.client.post("/api/keeper/move/", {
                "id": bookmark_id,
                "folder": "/"
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            moved_bookmark = StoreEntry.objects.get(idx=bookmark_id)
            self.assertEqual(moved_bookmark.path, f"chrome/书签栏/{moved_bookmark.title}")
            self.assertEqual(moved_bookmark.status, "collect")
            self.assertNotEqual(moved_bookmark.path, original_path)
            self.assertNotEqual(moved_bookmark.status, original_status)
            
            # Test moving from readlater folder to a new subfolder
            bookmark_id = self.readlater_bookmarks[1].idx
            original_path = self.readlater_bookmarks[1].path
            original_status = self.readlater_bookmarks[1].status
            
            target_folder = "书签栏/技术/Python"
            response = self.client.post("/api/keeper/move/", {
                "id": bookmark_id,
                "folder": target_folder
            })
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
            
            moved_bookmark = StoreEntry.objects.get(idx=bookmark_id)
            expected_path = f"chrome/{target_folder}/{moved_bookmark.title}"
            self.assertEqual(moved_bookmark.path, expected_path)
            self.assertEqual(moved_bookmark.status, "collect")
            self.assertNotEqual(moved_bookmark.path, original_path)
            self.assertNotEqual(moved_bookmark.status, original_status)
            
            # Verify response data structure
            self.assertIn("data", data)
            self.assertEqual(data["data"]["id"], bookmark_id)
            self.assertEqual(data["data"]["folder"], expected_path)
            
            # Verify all paths are properly formatted
            self.assertTrue(moved_bookmark.path.startswith("chrome/书签栏/"))
            
        except Exception as e:
            self.fail(f"POST move request failed: {e}")

    def test_c_readlater_delete(self):
        """Test deleting read later bookmark"""
        try:
            bookmark_id = self.readlater_bookmarks[0].idx
            response = self.client.delete(f"/api/keeper/?id={bookmark_id}")
            data = self.parse_return_info(response)
            self.assertEqual(data["code"], 200)
                        # Verify bookmark is marked as deleted
            deleted_bookmark = StoreEntry.objects.get(idx=bookmark_id)
            self.assertTrue(deleted_bookmark.is_deleted)
        except Exception as e:
            self.fail(f"DELETE readlater request failed: {e}")

if __name__ == "__main__":
    unittest.main()
