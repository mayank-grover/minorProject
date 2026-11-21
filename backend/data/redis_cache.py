"""
Redis caching client with seamless fallback to SQLite.
"""

import os
import json
from typing import Optional, Dict, Any
from backend.data.cache import DescriptionCache

class HybridDescriptionCache:
    """Uses Redis if available; automatically falls back to SQLite."""

    def __init__(self, redis_url: Optional[str] = None, sqlite_path: str = "artifacts/cache.sqlite3"):
        self.sqlite = DescriptionCache(sqlite_path)
        self.redis_client = None
        redis_host = redis_url or os.getenv("REDIS_URL")
        if redis_host:
            try:
                import redis
                self.redis_client = redis.from_url(redis_host, decode_responses=True, socket_connect_timeout=1)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None

    def get(self, image_hash: str, context_hash: str, mode: str, detail: str) -> Optional[Dict[str, Any]]:
        key = f"desc:{image_hash}:{context_hash}:{mode}:{detail}"
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    data = json.loads(val)
                    data["source"] = "redis"
                    return data
            except Exception:
                pass
        # Fallback to SQLite
        res = self.sqlite.get(image_hash, context_hash, mode, detail)
        if res:
            res["source"] = "sqlite"
        return res

    def put(self, image_hash: str, context_hash: str, mode: str, detail: str, description: str, metadata: Dict[str, Any]):
        key = f"desc:{image_hash}:{context_hash}:{mode}:{detail}"
        # Store in SQLite
        self.sqlite.put(image_hash, context_hash, mode, detail, description, metadata)
        # Store in Redis if connected
        if self.redis_client:
            try:
                payload = json.dumps({"description": description, "metadata": metadata, "cached": True})
                self.redis_client.setex(key, 86400 * 7, payload) # 7-day TTL
            except Exception:
                pass
