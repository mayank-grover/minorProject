# Wikipedia Image Accessibility — mid-semester prototype

A Manifest V3 Chrome extension and local FastAPI service generate real Wikipedia image descriptions with SmolVLM2. Both image-only and context-aware conditions use the same model and prepared pixels. There are no hardcoded production descriptions and no paid API requirement.

See [milestone evidence](docs/report.md), [API contract](docs/contracts.md), [demo walkthrough](docs/demo_script.md), and [team ownership](docs/team.md). The supplied full PRD is preserved in docs/PRD.md; the user's smaller sprint scope governs this prototype.

## Installation

Python 3.12 was tested on an Apple M2 MacBook Air with 16 GB RAM. Use Python 3.11 or 3.12 (system macOS Python 3.9 is unsuitable).

```sh
git clone https://github.com/mayank-grover/minorProject.git
cd minorProject
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-models.txt
cp .env.example .env
python -m scripts.configure
```

On this prepared machine `.venv` already exists; activate it directly. `scripts.configure` creates a random local token without printing it; it never overwrites an existing token. Read your local `.env` to copy the token into the extension options. Keep this file private. Model files are in `.cache/huggingface` and are ignored. First download needs about 9 GB; the environment/cache also needs disk space. The default model revision is pinned to the verified revision in docs/report.md for reproduction.

## Load the Chrome extension

1. Open `chrome://extensions`, enable Developer mode and choose **Load unpacked**.
2. Select the `extension` folder inside your cloned `minorProject` folder.
3. Copy the generated extension ID into `ALLOWED_EXTENSION_ID` in `.env`.
4. Open this extension's **Details → Extension options**. Save the same `LOCAL_BACKEND_TOKEN` from `.env`.
5. Start the backend:

```sh
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
export PYTORCH_ENABLE_MPS_FALLBACK=1
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Model loading precedes service readiness. Do not use `--reload` for the live demo; it reloads large weights when files change. In a second terminal:

```sh
curl http://127.0.0.1:8000/health
```

`model_ready: true` is required for generation. `degraded` means inference is unavailable; the service never substitutes fixture text. Bind only to loopback. A missing/incorrect token returns 401; an unconfigured extension origin returns 403. `LOAD_MODEL=0` starts the API without weights for health/schema checks but descriptions return 503.

The repository includes source, dependency lock files, tests, project documentation and historical pilot text/metadata. It excludes `.env`, virtual environments, model weights, downloaded images/article HTML, generated local artifacts and `node_modules`. A fresh clone needs the installation steps above and its own local token and Chrome extension ID. The machine-specific audit documents record the original development setup; the commands in this README are the portable setup instructions.

## Use

Open https://en.wikipedia.org/wiki/Common_sunflower in Chrome, click the extension's toolbar action, then choose a **Go to image** control or a **Describe** button beside an image. A result surface directly beneath the selected image shows a short loading status, genuine model output with an AI label, measured latency, and limitations. Use **Read description** to move focus to the result; **More detail**, **Refresh description**, **Retry**, and **Cancel request** are native buttons. **Disable for this page** removes the controls. Existing Wikipedia alt text is never overwritten. Only selected public image bytes and bounded article context go to the local backend.

The navigator remains above the article; each image keeps its own inline result. Escape inside a result returns focus to that image’s Describe button. Selecting another image or navigating away discards late results. Cancellation stops display, not necessarily ongoing GPU computation.

Prompt ab-3 asks photograph descriptions to convey framing, color, shape, texture, patterns and spatial arrangement, rather than only naming the subject. Diagrams should include both visible layout and readable meaning. Previously generated results keep their old text until you choose **Refresh description**. Model errors and omissions remain possible.

**Read aloud** beside every completed description starts speech. The button becomes **Stop reading**, and **Pause reading** / **Resume reading** appears during playback. Starting another image's audio stops the previous reading. Refreshing that description, disabling the extension or leaving the page stops its audio. Speech starts only when you click; it reads the description, without model metadata. **Read description** still moves keyboard/screen-reader focus to the text.

Playback uses Chrome's built-in [speech synthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), preferring an installed English voice, with enhanced voices preferred and a slightly relaxed rate. If no local English voice is listed yet, Chrome chooses its default voice. Naturalness and offline availability depend on the available device/browser voices. No new API key, backend service or audio package is required. After updating the extension code, reload this extension in `chrome://extensions`, reload Wikipedia and enable the controls again.

## Reproduce inference and pilot

```sh
export HF_HOME="$PWD/.cache/huggingface"
export PYTORCH_ENABLE_MPS_FALLBACK=1
python -m scripts.feasibility
python -m benchmark.build_dataset --limit 10
python -m benchmark.run --manifest benchmark/manifests/pilot.jsonl --output artifacts/runs/pilot.jsonl
python -m benchmark.analyze --manifest benchmark/manifests/pilot.jsonl --runs artifacts/runs/pilot.jsonl --output artifacts/results/pilot
```

The feasibility test compares an actual bee photograph with a red-square visual fixture, saving outputs and timings. The collector makes bounded public Wikimedia reads, saves revision-specific article HTML, image license/author/file metadata and prepared image hashes. Configure a contact-bearing `WIKIMEDIA_USER_AGENT` for team use. Do not redistribute an image until you have checked its source license and fulfilled attribution/share-alike requirements. Wikipedia text carries its own license, independently of each image.

The ten-example manifest is a development pilot, not a representative or held-out benchmark. Images span photographs, a portrait, astronomy, a bicycle, diagrams and a map. All extraction associations await human audit. Existing alt is retained as reference metadata and withheld from model prompts. Each example receives both modes with greedy decoding, 192 maximum new tokens, the same 768-pixel prepared raster and the same adapter. JSONL is append-only and resumes completed configuration/image/prompt cells (including failures). Use a fresh output filename to intentionally rerun. Do not run benchmark and server inference simultaneously on this 16 GB machine.

The recorded handoff copies are in `benchmark/results/pilot/`. New run outputs: `artifacts/runs/pilot.jsonl`, `artifacts/results/pilot/review.csv`, `comparison.html`, `summary.md`. Copy the CSV separately for each human reviewer; ratings remain blank until actual review. HTML displays real paired text for inspection. No factuality/usefulness gain or statistical significance is inferred from blank ratings.

For exact reproduction on another machine, copy legally permitted prepared PNGs plus the frozen manifest; live rebuilding may capture newer article/file revisions. Local prepared images/HTML are ignored rather than committed unnecessarily.

## Tests

```sh
python -m pytest -q
pnpm install --frozen-lockfile
pnpm test
```

Python tests use a clearly named test-only adapter, require no GPU/network and cover contracts, errors, auth/origin, image safety, deadlines, prompt isolation and evaluation logging. Node/jsdom tests cover extraction, safe UI states and unchanged original semantics. They do not establish real model quality or screen-reader usability. See tests/accessibility_checklist.md for actual/manual coverage.

## Layout and boundaries

- `backend/data`: bounded image fetch/decode/preprocessing.
- `backend/models`: replaceable real VLM adapter and input/output contract.
- `backend/engine`: versioned A/B prompts, shared generation, basic output checks.
- `backend/app.py`, `schemas.py`, `settings.py`: single API, limits, authentication and inference lane.
- `extension/context_extractor.js`: selected-image context extraction.
- `extension/content.js`, `service_worker.js`, `options.*`: accessible controls, MV3 transport, local token settings.
- `benchmark`: real source manifest collection, paired generation, reporting and blank human review sheet.
- `docs` and `tests`: evidence, limitations, ownership, regression tests.

Out of sprint scope: second VLM, full A/B/C study, training, caching/database, deployment, Web Store publishing and formal user study. Deterministic validation checks empty/overlong/markup outputs; it cannot determine whether every claim or identity is supported. Dense diagrams, tiny text, context contamination and hallucinations remain research problems. Full NVDA/VoiceOver and zoom/reflow checks must be recorded honestly before claiming those gates passed.
