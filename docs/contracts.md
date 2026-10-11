# API 1.0

`GET /health` is read-only and returns status (`ok`/`degraded`), model readiness/ID/revision, local processing, busy state, whether auth and extension origin are configured, and a hash of non-secret inference settings.

`POST /describe` and its alias `/v1/descriptions` accept JSON and `Authorization: Bearer <LOCAL_BACKEND_TOKEN>`. Browser Origin must be the configured `chrome-extension://<ID>`; command-line clients may omit Origin but still require the token. No arbitrary prompt/model paths are accepted. FastAPI's `/docs` exposes the actual generated schema.

```json
{
  "schema_version": "1.0",
  "request_id": "demo-001",
  "occurrence_id": "image-1",
  "article_url": "https://en.wikipedia.org/wiki/Common_sunflower",
  "revision_id": null,
  "image_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/40/Sunflower_sky_backdrop.jpg/960px-Sunflower_sky_backdrop.jpg",
  "context": {
    "article_title": "Common sunflower",
    "caption": null,
    "section_heading": null,
    "nearby_text": null,
    "existing_alt": ""
  },
  "mode": "context_aware",
  "detail": "concise"
}
```

This is an example request, not an observed output. Add `image_base64` for decoded raster bytes; the extension does this in its service worker. With bytes present, `image_url` is provenance and is still validated but never fetched by the backend. URL-only requests use the same bounds and deny redirects. SVG originals are rejected: use Wikimedia-rendered PNG thumbnails. Allowed hosts are exactly `upload.wikimedia.org` and `thumb.wikimedia.org` over HTTPS, no embedded credentials/other ports. Article URLs use the English canonical `/wiki/` read form; query/read-revision support is intentionally narrower than the full PRD.

Image limit: 8 MiB compressed; 20 MP before decode resize; aspect-preserving RGB/white transparency composite to a maximum 768-pixel side. Request body limit: 12 MB, including streamed/chunked bodies. Individual context bounds: title 300, caption 1200, section 300, nearby 3200, alt 600 characters; aggregate 800 words/8000 characters. Missing context is null, deliberately empty alt remains `""`. Unknown fields are rejected. Context and dimensions are validated independently of model readiness.

Success contains nonempty `description`, matching IDs, `mode`, `detail`, `model_id`, `model_revision`, `prompt_version`, measured `inference_ms` and `total_ms`, prepared `image_hash`, actually supplied `context_hash`, `generated: true`, and textual limitations. Real samples are saved in artifacts after a successful smoke run; there is no fake success mode.

Errors: `{"status":"error","error":{"code":"MODEL_UNAVAILABLE","message":"…","retryable":true}}`. HTTP codes: 401 auth, 403 origin, 413 oversized body/image, 415 unsupported decode, 422 schema/invalid base64, 429 busy, 502 source/output errors, 503 inference unavailable/failure, 504 deadline. Bodies do not echo tokens or full image/context payloads. The one-inference lane stays occupied after an HTTP timeout until actual compute completes; no unbounded queue is admitted.

Extension messages: `TOGGLE`, `DESCRIBE {payload}` → `{result}` or `{error}`. IDs, article URL, source/context snapshot, connection and cancellation generation are rechecked before attaching text. All model results use textContent.
