# Context-Aware Image Descriptions for CHAKSHU: Wikipedia for the Blind and Visually Impaired

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Chrome Extension](https://img.shields.io/badge/extension-Manifest%20V3-4285F4.svg)](https://developer.chrome.com/docs/extensions/)
[![Model](https://img.shields.io/badge/VLM-SmolVLM2--2.2B--Instruct-orange.svg)](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A reusable, privacy-preserving system that generates rich, context-aware image descriptions for Wikipedia to assist blind and visually impaired readers accessing Wikipedia through **CHAKSHU** (PEC DST-funded accessibility initiative). 

The system pairs a **Manifest V3 Chrome Extension** client with a local, authenticated **FastAPI backend** running local Vision-Language Model (**SmolVLM2-2.2B-Instruct**). All inference executes locally on-device without paid external APIs, telemetry, or user data tracking.

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Section 3.4 Progress Matrix](#section-34-current-progress-of-the-project-work)
3. [Core Deliverables (D1 – D4)](#core-deliverables-status-d1--d4)
4. [Installation & Setup](#installation--setup)
5. [Loading the Chrome Extension](#loading-the-chrome-extension)
6. [Using the System](#using-the-system)
7. [Validation & Cross-Validation](#validation--testing-methodology)
8. [Testing & Verification](#testing--verification)
9. [Project Structure & Module Ownership](#project-structure--module-ownership)
10. [Documentation Links](#documentation-links)

---

## System Architecture

```text
+-----------------------------------------------------------------------------------+
|                           WIKIPEDIA READING CLIENT                                |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |                       Chrome Extension (Manifest V3)                      |   |
|   |                                                                           |   |
|   |  - Context Extractor (DOM captions, nearby text, section headers, summary)|   |
|   |  - Accessible In-Page UI (ARIA live status, Tab/Enter focus management)   |   |
|   |  - Audio Narration (Web Speech API with Play / Pause / Resume controls)   |   |
|   |  - Diagnostics Options Page (Live backend connection health check)        |   |
|   +---------------------------------------------------------------------------+   |
+------------------------------------------+----------------------------------------+
                                           |  Authenticated Loopback HTTP
                                           |  (POST /describe, Bearer token)
                                           v
+-----------------------------------------------------------------------------------+
|                         LOCAL REUSABLE FASTAPI BACKEND                            |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |  FastAPI Server (backend/app.py)                                          |   |
|   |  - Single-Inference Lane Lock (threading.Lock, prevents OOM on unified RAM)|   |
|   |  - Strict Contract & Payload Bounds (12 MB max body, 768px/1600px limits) |   |
|   |  - Constant-time HMAC Token Authentication (hmac.compare_digest)          |   |
|   +-------------------------------------+-------------------------------------+   |
|                                         |                                         |
|         +-------------------------------+-------------------------------+         |
|         |                                                               |         |
|         v                                                               v         |
|  +--------------------------------+                  +-------------------------+  |
|  | Multi-Tier Caching Layer       |                  | Generation Pipeline     |  |
|  | - SQLite (artifacts/cache.db)  |                  | - Versioned Prompts     |  |
|  | - Redis Hybrid Cache           |                  | - Tesseract OCR Filter  |  |
|  | - 0.0 ms Instant Cache-Hits    |                  | - Anti-Copy Retry Loop  |  |
|  +--------------------------------+                  +------------+------------+  |
|                                                                   |               |
|                                                                   v               |
|                                                      +-------------------------+  |
|                                                      | Local VLM Inference     |  |
|                                                      | - SmolVLM2-2.2B (fp16)  |  |
|                                                      | - Apple Silicon (MPS)   |  |
|                                                      | - 768px Patch Splitting |  |
|                                                      +-------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Section 3.4 Current Progress of the Project Work

Aligned directly with the Department Evaluation Progress Sheet:

| Sn | Name of Module(s) | Status | Codebase Artifacts & Verification |
|:--:|---|:---:|---|
| **1** | **Context Extraction** | **Completed** | [`extension/context_extractor.js`](extension/context_extractor.js), [`backend/engine/article_context.py`](backend/engine/article_context.py) |
| **2** | **Multi-Model Benchmark** | **Completed** | [`benchmark/compare_models.py`](benchmark/compare_models.py), [`benchmark/results/multi_model/`](benchmark/results/multi_model/) (SmolVLM2-2.2B vs Qwen3-VL-2B) |
| **3** | **Context-Aware Description** | **Completed** | Versioned prompts (`ab-1` through `ab-11`), OCR noise filtering ([`backend/engine/ocr.py`](backend/engine/ocr.py)), sentence-boundary validation |
| **4** | **Browser Extension & Backend** | **Completed** | Manifest V3 Extension ([`extension/`](extension/)), FastAPI service ([`backend/app.py`](backend/app.py)), SQLite/Redis Cache ([`backend/data/cache.py`](backend/data/cache.py)) |

---

## Core Deliverables Status (D1 – D4)

- [x] **D1: Image-Description Prototype (Current Cutoff)**
  - Fully functioning Manifest V3 Chrome Extension.
  - In-page navigation (`Go to image`, `Describe`, `More detail`, `Cancel`, `Retry`).
  - Screen reader accessibility: polite `aria-live` announcements, proper heading tabindex, Escape focus return.
  - Native Web Speech audio playback with pause/resume narration controls.
- [x] **D2: Reusable Description Module (Core Contribution)**
  - Standalone FastAPI engine exposing schema 1.0 at `POST /describe` and `POST /v1/descriptions`.
  - Powered by **SmolVLM2-2.2B-Instruct** (`HuggingFaceTB/SmolVLM2-2.2B-Instruct`) running locally in float16 precision.
  - Local SQLite database cache (`artifacts/cache.sqlite3`) and Redis cache for sub-millisecond repeated queries.
  - Standalone Python Client SDK ([`client/chakshu_client.py`](client/chakshu_client.py)) ready for downstream platform consumption.
- [x] **D3: Validation, Quality Iteration & Documentation**
  - **Stratified Group 5-Fold Cross-Validation** (`benchmark/stratified_group_kfold.py`) guaranteeing zero article-context leakage.
  - Independent dual-reviewer ratings completed on both pilot and 56 held-out live occurrences.
  - Accessibility checklist verified on macOS VoiceOver (`tests/accessibility_checklist.md`).
- [ ] **D4: CHAKSHU Integration (Final Phase)**
  - Connect the reusable module via the client SDK (`client/chakshu_client.py`) into the main PEC DST-funded CHAKSHU platform.

---

## Installation & Setup

### Prerequisites
- macOS (Apple Silicon M-series recommended) or Linux with Python 3.11+.
- Python 3.12/3.15 tested with PyTorch 2.15 (MPS/CUDA/CPU).
- Tesseract OCR (install on macOS via `brew install tesseract`).

```bash
# 1. Clone the repository
git clone https://github.com/rags-git/minorProject.git
cd minorProject

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-models.txt

# 4. Configure local environment settings
cp .env.example .env
python -m scripts.configure
```

`scripts.configure` generates a private, randomized local authentication token in `.env`.

### Vision-Language Model
The project runs **SmolVLM2-2.2B-Instruct** (`HuggingFaceTB/SmolVLM2-2.2B-Instruct`, revision `482adb53...`) as its single vision-language model. 
- Fully open-source under Apache-2.0.
- Executed locally via PyTorch with Metal Performance Shaders (`mps`) acceleration on Apple Silicon.
- Uses aspect-preserving image preparation bounded to a maximum 768-pixel longest edge.

---

## Loading the Chrome Extension

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Toggle on **Developer mode** (top right switch).
3. Click **Load unpacked** and select the `extension/` folder inside this repository.
4. Open the extension's **Options** page:
   - Paste the `LOCAL_BACKEND_TOKEN` found in your `.env` file.
   - Click **Save token**.
   - Use the **Test Backend Health** button to confirm live communication with the FastAPI service.
5. In `.env`, set `ALLOWED_EXTENSION_ID=<your-extension-id>` to enforce CORS origin security.

---

## Using the System

### 1. Launch the Backend
```bash
python3 run.py
```
Check health status in another terminal:
```bash
curl http://127.0.0.1:8000/health
```
When `model_ready: true`, inference is active and ready.

### 2. Generate Accessible Descriptions
1. Open any English Wikipedia article (e.g., `https://en.wikipedia.org/wiki/Common_sunflower`).
2. Click the extension toolbar button or use the in-page navigator to browse images.
3. Click **Describe** next to any image:
   - Context is extracted from the DOM.
   - Local VLM generates a grounded description.
   - Click **Read description** to focus the result, or **Read aloud** to listen via text-to-speech.

---

## Validation & Testing Methodology

### Stratified Group 5-Fold Cross-Validation
Standard K-Fold leaks context because Wikipedia articles contain multiple images sharing identical summaries and lead text. We implement **Stratified Group 5-Fold Cross-Validation** ([`docs/kfold_evaluation_methodology.md`](docs/kfold_evaluation_methodology.md)):
- **Grouped by Article:** All images from an article remain in either train or test folds (zero data leakage).
- **Stratified by Domain:** Balances biographies, diagrams, processes, charts, maps, flags, artworks, astronomy, and nature across folds.

Run the cross-validation partitioner:
```bash
PYTHONPATH=. python3 benchmark/evaluate_kfold.py
```

---

## Testing & Verification

### 1. Standalone Unit Test Suite (Fast, No GPU Required)
Runs verified tests for SQLite/Redis caching, StratifiedGroupKFold integrity, scoring aggregation, CHAKSHU client SDK, and multi-model benchmarking:

```bash
python3 -m unittest tests/test_cache.py tests/test_kfold.py tests/test_kfold_scoring.py tests/test_chakshu_client.py tests/test_multi_model_benchmark.py
```

### 2. Full Integration Tests
```bash
python -m pytest -q
pnpm install --frozen-lockfile
pnpm test
```

---

## Project Structure & Module Ownership

```text
minorProject/
├── backend/
│   ├── app.py                     # FastAPI application factory, lifecycle, routes
│   ├── schemas.py                 # Pydantic schema 1.0 contracts
│   ├── settings.py                # Environment configuration
│   ├── data/
│   │   ├── cache.py               # SQLite persistent cache
│   │   ├── redis_cache.py         # Hybrid Redis/SQLite caching client
│   │   └── images.py              # Image decode, hash, and safety preprocessing
│   ├── engine/
│   │   ├── generate.py            # Generation pipeline, validation, retry logic
│   │   ├── prompts.py             # Versioned prompts (ab-1 to ab-11)
│   │   ├── ocr.py                 # Tesseract OCR engine and label extractor
│   │   └── article_context.py     # Context sanitization and hashing
│   └── models/
│       └── smolvlm.py             # Unified local VLM model adapter (SmolVLM2 / Qwen)
├── client/
│   └── chakshu_client.py          # Standalone Python client SDK for CHAKSHU
├── extension/
│   ├── manifest.json              # Chrome Manifest V3 configuration
│   ├── content.js                 # In-page UI, ARIA live regions, TTS audio
│   ├── context_extractor.js       # Wikipedia DOM context extraction
│   ├── options.html / options.js  # Token storage & live connection health checker
│   └── service_worker.js          # MV3 background messaging
├── benchmark/
│   ├── stratified_group_kfold.py  # Stratified Group K-Fold partitioner
│   ├── evaluate_kfold.py          # Cross-validation runner
│   ├── compare_models.py          # Multi-model benchmark comparison engine
│   └── manifests/                 # Frozen benchmark manifests (pilot & live-v2)
├── tests/                         # Comprehensive unit & integration test suites
└── docs/                          # Architecture reports, PRD, and audit records
```

---

## Documentation Links

- **Raghav's Primary Responsibility Report:** [`docs/raghav_backend_extension_architecture.md`](docs/raghav_backend_extension_architecture.md)
- **API & Protocol Contracts:** [`docs/contracts.md`](docs/contracts.md)
- **K-Fold Validation Methodology:** [`docs/kfold_evaluation_methodology.md`](docs/kfold_evaluation_methodology.md)
- **Mid-Semester Project Report:** [`docs/report.md`](docs/report.md)
- **Four-Person Team Work Division:** [`docs/team.md`](docs/team.md)
- **Demo Script & Walkthrough:** [`docs/demo_script.md`](docs/demo_script.md)
