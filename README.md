# Context-Aware Image Descriptions for CHAKSHU: Wikipedia for the Blind and Visually Impaired

A lightweight, privacy-preserving tool that generates helpful image descriptions on Wikipedia to assist blind and visually impaired readers accessing content through **CHAKSHU** (PEC DST-funded project).

It connects a **Chrome Extension** to a local **FastAPI backend** running a local Vision-Language Model (**SmolVLM2-2.2B**). Everything runs on your machine without external paid APIs, cloud uploads, or privacy risks.

---

## Why We Chose These Technologies

Here is a straightforward explanation of why each technology was specifically chosen for this problem:

- **SmolVLM2-2.2B-Instruct (Vision-Language Model):**  
  *Why:* It is an open-source multimodal model that runs directly on device (like an Apple Silicon Mac with unified memory) in float16 precision, producing fast descriptions without requiring expensive cloud GPUs or sending user data to third parties.

- **Stratified Group 5-Fold Cross-Validation (Evaluation Model):**  
  *Why:* Standard K-Fold causes "data leakage" because multiple images from the same Wikipedia article share the same summary text. Grouping by article guarantees zero leakage, while stratification ensures every fold has a balanced mix of charts, maps, diagrams, and photos.

- **FastAPI (Backend Framework):**  
  *Why:* It is lightweight, executes asynchronous requests with high throughput, and allows strict input validation to prevent invalid data or out-of-memory crashes on unified RAM.

- **SQLite & Redis (Caching Layer):**  
  *Why:* Wikipedia readers frequently visit the same popular pages. Caching generated descriptions using image and context hashes gives instant (0.0 ms inference) responses and avoids redundant compute.

- **Chrome Extension (Manifest V3):**  
  *Why:* It integrates directly into the user's browser, reading surrounding captions and paragraphs from the live Wikipedia page and announcing descriptions using accessible screen-reader standards (`aria-live`).

- **Tesseract OCR (Text Extraction):**  
  *Why:* VLMs often struggle to read small text in charts, maps, and diagrams. Running local OCR alongside the vision model extracts text labels so the model can ground its descriptions accurately.

---

## System Overview

```text
+-----------------------------------------------------------------------------------+
| 1. Chrome Extension (Browser Client)                                              |
|    - Extracts the selected image, surrounding caption, and nearby text.           |
|    - Provides screen-reader accessible controls (Tab/Enter, polite aria-live).    |
|    - Features built-in Text-to-Speech audio narration (Play/Pause/Resume).        |
+------------------------------------------+----------------------------------------+
                                           | Local HTTP (POST /describe)
                                           v
+-----------------------------------------------------------------------------------+
| 2. FastAPI Backend (Local Server)                                                 |
|    - Verifies token security and single-lane concurrency to prevent crashes.      |
|    - Checks SQLite / Redis cache: if previously described, returns immediately.   |
|    - If new: runs Tesseract OCR and SmolVLM2 locally to generate description.     |
+-----------------------------------------------------------------------------------+
```

---

## Current Project Progress (Module Breakdown)

Aligned with the Minor Project Evaluation Progress:

| Module | Status | What Was Built |
|---|:---:|---|
| **1. Context Extraction** | **Completed** | DOM extractor (`extension/context_extractor.js`) collecting captions, section headings, and lead paragraphs. |
| **2. Multi-Model Benchmark** | **Completed** | Benchmark runner (`benchmark/compare_models.py`) measuring completion rates and latency across VLM architectures. |
| **3. Context-Aware Description** | **Completed** | Prompt generation pipeline with anti-copying retries and OCR text filtering (`backend/engine/`). |
| **4. Browser Extension & Backend** | **Completed** | Manifest V3 Extension (`extension/`), FastAPI service (`backend/app.py`), and SQLite cache (`backend/data/cache.py`). |

---

## Quick Setup & How to Run

### Step 1: Install Dependencies
```bash
# 1. Clone repository
git clone https://github.com/rags-git/minorProject.git
cd minorProject

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt
pip install -r requirements-models.txt

# 4. Create local config
cp .env.example .env
python -m scripts.configure
```

### Step 2: Start the Backend Server
```bash
python3 run.py
```
Confirm it is online:
```bash
curl http://127.0.0.1:8000/health
```

### Step 3: Load the Chrome Extension
1. Open Google Chrome and go to `chrome://extensions/`.
2. Turn on **Developer mode** (top-right toggle).
3. Click **Load unpacked** and select the `extension/` folder in this repo.
4. Click **Details → Extension options**:
   - Paste the `LOCAL_BACKEND_TOKEN` generated in your `.env` file.
   - Click **Save token**, then click **Test Backend Health** to verify connection.

### Step 4: Use on Wikipedia
Open any Wikipedia article (e.g., https://en.wikipedia.org/wiki/Common_sunflower). Click **Describe** next to an image to view or listen to the generated description.

---

## Verification & Tests

You can run the verified standalone test suite without needing a GPU:

```bash
python3 -m unittest tests/test_cache.py tests/test_kfold.py tests/test_kfold_scoring.py tests/test_chakshu_client.py tests/test_multi_model_benchmark.py
```

---

## Project Documentation
- **Architecture Documentation:** [`docs/backend_extension_architecture.md`](docs/backend_extension_architecture.md)
- **K-Fold Validation Details:** [`docs/kfold_evaluation_methodology.md`](docs/kfold_evaluation_methodology.md)
- **API Contracts:** [`docs/contracts.md`](docs/contracts.md)
- **Milestone Report:** [`docs/report.md`](docs/report.md)
