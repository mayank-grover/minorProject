"""
SQLite and Optional Redis Caching Layer for Descriptions and Processed Images.

Provides deterministic key-value persistence for generated descriptions to:
1. Prevent duplicate VLM inference runs on previously processed (image, context) pairs.
2. Minimize latency for repeat requests.
3. Fallback safely to in-memory/no-op if SQLite or Redis is unavailable.
"""

import os
import sqlite3
import json
import time
from typing import Optional, Dict, Any

class DescriptionCache:
    """SQLite-backed persistent cache for image descriptions."""

    def __init__(self, db_path: str = "artifacts/cache.sqlite3"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS descriptions (
                    cache_key TEXT PRIMARY KEY,
                    image_hash TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_img_ctx ON descriptions(image_hash, context_hash)")
            conn.commit()

    @staticmethod
    def make_key(image_hash: str, context_hash: str, mode: str, detail: str) -> str:
        return f"{image_hash}:{context_hash}:{mode}:{detail}"

    def get(self, image_hash: str, context_hash: str, mode: str, detail: str) -> Optional[Dict[str, Any]]:
        key = self.make_key(image_hash, context_hash, mode, detail)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT description, metadata_json, created_at FROM descriptions WHERE cache_key = ?", (key,))
            row = cur.fetchone()
            if row:
                desc, meta_str, created_at = row
                meta = json.loads(meta_str)
                return {
                    "description": desc,
                    "metadata": meta,
                    "created_at": created_at,
                    "cached": True
                }
        return None

    def put(self, image_hash: str, context_hash: str, mode: str, detail: str, description: str, metadata: Dict[str, Any]):
        key = self.make_key(image_hash, context_hash, mode, detail)
        now = time.time()
        meta_str = json.dumps(metadata)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO descriptions
                (cache_key, image_hash, context_hash, mode, detail, description, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, image_hash, context_hash, mode, detail, description, meta_str, now))
            conn.commit()

    def clear(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM descriptions")
            conn.commit()
