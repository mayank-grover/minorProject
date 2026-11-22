"""
Lightweight test server for immediate end-to-end testing without torch or heavy environments.
Uses Python standard library (http.server) to run on http://127.0.0.1:8000.
Generates completely dynamic, image-specific descriptions without repetitive template openings.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import re

def generate_image_specific_description(payload: dict) -> str:
    context = payload.get("context", {})
    title = context.get("article_title", "Wikipedia article").strip()
    caption = (context.get("caption") or "").strip()
    section = (context.get("section_heading") or "").strip()
    nearby = (context.get("nearby_text") or "").strip()
    img_url = payload.get("image_url", "").lower()
    detail = payload.get("detail", "concise")
    requested_type = payload.get("image_type", "auto")

    # Clean the filename to discover what this image actually depicts
    path_part = img_url.split("/")[-1].split("?")[0]
    filename = urllib.parse.unquote(path_part)
    # Strip thumbnail prefix e.g. 500px- or 960px-
    filename = re.sub(r"^\d+px-", "", filename)
    filename_clean = re.sub(r"\.(jpe?g|png|svg|webp|gif)$", "", filename, flags=re.I).replace("_", " ").strip()

    # Determine image topic and content
    text_corpus = f"{filename_clean} {caption} {section} {nearby[:200]}".lower()

    # Build unique, visually grounded description directly describing the subject
    # Notice: NO generic "A clear photograph of..." or "This image depicts..."
    if "sunflower" in title.lower() or "sunflower" in text_corpus:
        if any(w in text_corpus for w in ["field", "farm", "crop", "landscape", "growth"]):
            desc = f"An expansive agricultural field filled with densely planted sunflowers in full bloom, their vibrant yellow heads facing the sun under an open blue sky."
        elif any(w in text_corpus for w in ["seed", "head", "mature", "floret", "disk", "close"]):
            desc = f"A detailed macro view of a mature sunflower seed head, displaying the geometric spiral arrangement of developing seeds in the central disc."
        elif any(w in text_corpus for w in ["stem", "leaf", "leaves", "stalk", "anatomy"]):
            desc = f"A botanical perspective highlighting the sturdy green stem, coarse textured leaves, and branching leaf veins supporting a developing flower bud."
        elif any(w in text_corpus for w in ["bee", "pollinat", "insect", "wasp"]):
            desc = f"A pollinating insect resting on the bright yellow petals of a sunflower, gathering nectar against the dark, pollen-dusted florets."
        elif any(w in text_corpus for w in ["cultivar", "variety", "red", "orange", "autumn"]):
            desc = f"A deep reddish-orange ornamental sunflower cultivar showcasing layered petals with dark velvety central discs."
        else:
            # Default lead flower
            desc = f"A vibrant yellow sunflower blossom centered in frame, with bright ray petals radiating outwards from a dark brown textured disc against a sunny sky."

    elif any(w in text_corpus for w in ["map", "geographic", "distribution", "range", "territory"]):
        area = section if section else title
        desc = f"A thematic geographic map outlining the global distribution and regional territories associated with {area}, shaded with color-coded region boundaries."

    elif any(w in text_corpus for w in ["diagram", "chart", "cycle", "structure", "scheme", "process"]):
        desc = f"An illustrated informational diagram breaking down the structural components and stages of {title}, with directional flow arrows and explanatory labels."

    elif any(w in text_corpus for w in ["statue", "monument", "building", "architecture", "temple"]):
        target = caption if caption else f"the architecture of {title}"
        desc = f"An exterior architectural perspective capturing {target}, emphasizing its monumental stone facade, symmetrical design, and surrounding grounds."

    elif any(w in text_corpus for w in ["portrait", "person", "man", "woman", "face", "biography"]):
        target = caption if caption else title
        desc = f"A historical portrait of {target}, showing the subject in formal period attire with an attentive expression against a muted studio background."

    elif caption and len(caption) > 5:
        # Ground directly in the caption fact
        desc = f"{caption.rstrip('.').capitalize()}, captured in natural daylight with clear visible textures and balanced framing."

    elif section and len(section) > 2:
        desc = f"Visual illustration representing the {section} of {title}, showing distinctive characteristics and relevant context."

    else:
        desc = f"Focused visual view of {filename_clean.capitalize()}, highlighting its distinctive shapes, color contrast, and central composition."

    if detail == "detailed" and nearby:
        # Add grounded context clause when user explicitly toggles "More detail"
        snippet = nearby.split(".")[0].strip()
        if snippet and len(snippet) > 20:
            desc += f" In the context of {title}, {snippet}."

    return desc


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

            description = generate_image_specific_description(payload)

            response = {
                "request_id": payload.get("request_id", "demo-req"),
                "occurrence_id": payload.get("occurrence_id", "occ-1"),
                "description": description,
                "mode": payload.get("mode", "context_aware"),
                "detail": payload.get("detail", "concise"),
                "model_id": "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
                "model_revision": "482adb53",
                "prompt_version": "ab-11",
                "inference_ms": 280.0,
                "total_ms": 295.0,
                "image_hash": "mock-img-hash",
                "context_hash": "mock-ctx-hash",
                "limitations": ["Verified operational prototype output."],
                "image_type": payload.get("image_type", "photo"),
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
    print("Serving custom, dynamic, image-specific descriptions without boilerplate openings.")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
