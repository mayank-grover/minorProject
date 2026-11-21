"""Unit tests for SQLite and Hybrid Redis caching layer."""

import unittest
import os
import shutil
from backend.data.cache import DescriptionCache
from backend.data.redis_cache import HybridDescriptionCache

class TestCache(unittest.TestCase):
    def setUp(self):
        self.test_db = "artifacts/test_cache.sqlite3"
        self.cache = DescriptionCache(self.test_db)
        self.hybrid = HybridDescriptionCache(sqlite_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_sqlite_put_and_get(self):
        self.cache.put("img_abc", "ctx_123", "context_aware", "concise", "A beautiful sunflower.", {"model": "qwen"})
        res = self.cache.get("img_abc", "ctx_123", "context_aware", "concise")
        self.assertIsNotNone(res)
        self.assertEqual(res["description"], "A beautiful sunflower.")
        self.assertTrue(res["cached"])
        self.assertEqual(res["metadata"]["model"], "qwen")

    def test_sqlite_miss(self):
        res = self.cache.get("nonexistent", "ctx", "context_aware", "concise")
        self.assertIsNone(res)

    def test_hybrid_fallback_to_sqlite(self):
        self.hybrid.put("img_xyz", "ctx_456", "image_only", "detailed", "A red bicycle.", {"model": "smolvlm"})
        res = self.hybrid.get("img_xyz", "ctx_456", "image_only", "detailed")
        self.assertIsNotNone(res)
        self.assertEqual(res["description"], "A red bicycle.")
        self.assertEqual(res["source"], "sqlite")

if __name__ == "__main__":
    unittest.main()
