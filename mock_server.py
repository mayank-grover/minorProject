"""
Lightweight mock server for immediate end-to-end testing without torch or heavy environments.
Uses Python standard library (http.server) to run on http://127.0.0.1:8000.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class MockBackendHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "ok",
                "model_ready": True,
                "model_id": "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
                "processing": "local",
                "busy": False,
                "schema_version": "1.0"
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ("/describe", "/v1/descriptions"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            title = payload.get("context", {}).get("article_title", "Wikipedia")
            caption = payload.get("context", {}).get("caption") or "An image"

            # Realistic simulated context-aware description
            desc = f"A clear, centered photograph of a {title.lower()}. The visible subject displays characteristic natural features matching '{caption}', set against a softly blurred background."

            response = {
                "request_id": payload.get("request_id", "demo-req"),
                "occurrence_id": payload.get("occurrence_id", "occ-1"),
                "description": desc,
                "mode": payload.get("mode", "context_aware"),
                "detail": payload.get("detail", "concise"),
                "model_id": "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
                "model_revision": "482adb53",
                "prompt_version": "ab-11",
                "inference_ms": 320.0,
                "total_ms": 340.0,
                "image_hash": "mock-img-hash",
                "context_hash": "mock-ctx-hash",
                "limitations": ["Verified operational prototype output."],
                "image_type": "photo",
                "ocr_status": "ok",
                "analysis_ms": 15.0
            }

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), MockBackendHandler)
    print("Zero-dependency testing server running at http://127.0.0.1:8000")
    print("Supports /health and /describe for immediate Chrome extension testing!")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
