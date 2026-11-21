"""
CHAKSHU Reusable Description Client SDK.

Provides clean programmatic access to the D2 image description API,
supporting both remote HTTP mode and structured responses for easy CHAKSHU integration.
"""

from typing import Dict, Any, Optional
import json
import urllib.request
import urllib.error

class ChakshuClientError(Exception):
    """Base exception for Chakshu client operations."""
    pass

class ChakshuImageDescriber:
    """Client for querying the context-aware image description module."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", token: Optional[str] = None, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        """Check status and readiness of the description backend."""
        url = f"{self.base_url}/health"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ChakshuClientError(f"Health check failed: {e}")

    def describe(
        self,
        image_url: str,
        article_title: str,
        caption: Optional[str] = None,
        nearby_text: Optional[str] = None,
        section_heading: Optional[str] = None,
        image_base64: Optional[str] = None,
        mode: str = "context_aware",
        detail: str = "concise",
        image_type: str = "auto"
    ) -> Dict[str, Any]:
        """Request an accessible, context-aware description for an image occurrence."""
        url = f"{self.base_url}/describe"
        payload = {
            "schema_version": "1.0",
            "request_id": f"chakshu-{crypto_id()}",
            "occurrence_id": "occ-1",
            "article_url": f"https://en.wikipedia.org/wiki/{article_title.replace(' ', '_')}",
            "image_url": image_url,
            "context": {
                "article_title": article_title,
                "caption": caption,
                "section_heading": section_heading,
                "nearby_text": nearby_text,
                "existing_alt": None
            },
            "mode": mode,
            "detail": detail,
            "image_type": image_type
        }
        if image_base64:
            payload["image_base64"] = image_base64

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise ChakshuClientError(f"API request failed with HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise ChakshuClientError(f"Failed to connect to backend: {e}")

def crypto_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8]
