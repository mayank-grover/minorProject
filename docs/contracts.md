# API 1.0

Prompt ab-5 accepts optional request `image_type`: `auto` (default), `photo`, `flag`, `chart`, `map`, `process`, or `diagram`. Responses add `image_type`, `ocr_status` (`ok`, `no_text`, `failed`, `unavailable`) and `analysis_ms`; existing fields and schema version remain compatible. `/health` also exposes `ocr_engine`. Image-analysis time includes classification/OCR and is separate from description-only `inference_ms`; `total_ms` includes the full pipeline. Actual OCR words/boxes and engine are stored in generation records, not the public response. OCR confidence scores are only used to filter recognition results, never presented as model confidence.

OCR uses local English Tesseract, modes 11 and 6, with normalized top-left word boxes, duplicate filtering, a 16-word/1200-character prompt bound and a seven-second deadline per pass. API OCR input is safely decoded to at most 1600 pixels; vision-model pixels and their returned image hash remain 768 pixels. Image-only mode may use pixel-derived OCR/classification, but does not use article text or source identity. Focused context-aware prompts use the bounded article overview and selected-image fields listed below, reflected in the context hash. The existing conservation prompt continues to use caption only. Benchmark runs use their frozen 768-pixel prepared image for both vision and OCR and therefore are not identical to the API's higher-resolution OCR path.

Prompt ab-6 integrates source-supported subject names into generated prose. Explicit biography aliases can resolve abbreviated captions; a main biography infobox image supplies a subject association when uncaptioned. Associated caption links identify other subjects. Titles, alt text and filenames alone do not establish identity. A generic opening noun may be replaced with the resolved name; otherwise a short “The image shows …” introduction is added. `raw_output` remains the unmodified model response. The 120/250-word validation applies to model prose; a name introduction can add a few words. Names may still be wrong if Wikipedia's association or the generated prose is wrong.

Optional context fields added without changing schema 1.0: `page_summary` (1200 characters), `section_outline` (12 items), `image_overview` (8 items), `article_kind` (`general`/`biography`), `subject_name` and `caption_subject` (200 characters each), `subject_aliases` (8 items), `image_position` (nonnegative zero-based index), `image_role` (`lead`/`contextual`), and `lead_subject_association` (boolean). Aggregate context remains limited to 800 words/8000 characters, including nested lists. Older snapshots still work with reduced context. Image-only prompts and identity handling exclude these source fields. Internal generation records include `description_focus` and `resolved_subject`; public response fields are unchanged. Existing alt is never supplied to the model.

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
