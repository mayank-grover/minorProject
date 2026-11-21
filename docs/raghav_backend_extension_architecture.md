# Primary Responsibility: Extension and FastAPI Backend (Raghav Bhardwaj, SID 24106017)

This document provides complete technical evidence and architectural documentation for **Extension, FastAPI Backend, and Data Caching** as submitted on the PEC Minor Project Verification Table (Part B).

---

## 1. System Components & Architecture

### A. Chrome Extension (Manifest V3)
- **Manifest:** [`extension/manifest.json`](../extension/manifest.json)
  - Uses Manifest V3 standards with service worker architecture (`extension/service_worker.js`).
  - Active Tab and storage permissions strictly scoped to Wikipedia (`https://en.wikipedia.org/*`).
- **In-Page Accessible UI (`extension/content.js`):**
  - Injects keyboard-navigable controls beside eligible Wikipedia images (`Describe`, `Read description`, `Read aloud`, `More detail`, `Cancel request`, `Retry`).
  - Implements W3C WAI-ARIA standards: live polite regions (`role="status"`), `aria-controls`, and heading focus shifts.
  - Features integrated client-side Text-to-Speech via Web Speech API (`SpeechSynthesisUtterance`) with play, pause, and stop narration controls.
- **Options Management & Health Check (`extension/options.html`, `options.js`):**
  - Secure storage of local bearer token in `chrome.storage.local`.
  - Added live one-click health diagnosis querying `http://127.0.0.1:8000/health`.

### B. High-Performance FastAPI Backend (`backend/app.py`)
- **Strict Schema & Validation (`backend/schemas.py`):**
  - Endpoints: `POST /describe` (and alias `/v1/descriptions`), `GET /health`.
  - Enforces body bounds (12 MB max) and streaming body size caps to prevent denial-of-service.
  - Rejects untrusted origins via CORS whitelist (`chrome-extension://<EXTENSION_ID>`).
- **Single-Inference Concurrency Lane:**
  - Uses `threading.Lock` and `concurrent.futures.ThreadPoolExecutor(max_workers=1)` to ensure the local VLM is never overloaded by concurrent requests on unified memory.
  - Immediate `429 BACKEND_BUSY` with client retry protocol if an inference job is already in flight.
- **Security & Authorization:**
  - Constant-time HMAC token verification (`hmac.compare_digest`) preventing timing attacks.

### C. Persistent Caching Layer: SQLite & Redis (`backend/data/`)
- **SQLite Database Cache (`backend/data/cache.py`):**
  - Location: `artifacts/cache.sqlite3`
  - Automatically caches successful model descriptions using composite keys (`image_hash:context_hash:mode:detail`).
  - Instant cache-hits with 0.0 ms inference latency for repeated requests.
- **Hybrid Redis Cache (`backend/data/redis_cache.py`):**
  - Provides in-memory sub-millisecond lookups via Redis with transparent, seamless fallback to SQLite.

---

## 2. Evidence & Verification

1. **Unit Test Coverage:**
   - [`tests/test_cache.py`](../tests/test_cache.py): Validates SQLite and Redis caching, cache-hits, and fallback.
   - [`tests/test_chakshu_client.py`](../tests/test_chakshu_client.py): Validates client SDK communication with backend.
   - [`tests/test_kfold.py`](../tests/test_kfold.py): Validates cross-validation data-leakage prevention.
2. **Interactive UI Verification:**
   - Chrome accessibility tree confirmed with full Tab/Enter keyboard navigation.
   - Options UI connection test confirms live backend handshake.
