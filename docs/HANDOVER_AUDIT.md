# Implementation audit and complete handover

Audit date: 11 October 2026. Repository: `/Users/mayank/Documents/minorProject`.

## 1. Executive summary

A local, functioning prototype exists: Chrome Manifest V3 extension → bounded Wikipedia image/context extraction → authenticated loopback FastAPI → real SmolVLM2 → an in-page result. A separate runner produces image-only/context-aware comparisons. No training or paid hosted inference is involved.

**Verified during this audit:** 18 Python tests and 3 JavaScript tests pass; the existing backend responds to `/health` with HTTP 200 and `model_ready: true`; fresh real context-aware and image-only requests succeed; ten local prepared images match their manifest hashes; current prompts match all twenty saved attempts; report generation reproduces the saved counts and medians. Dependency compatibility was checked with uv: 52 packages compatible.

**Previously verified, with inspected records:** actual Chrome results on Common sunflower and Moon, keyboard selection with Tab/Enter, Read description focus movement, Escape return and busy-error/Retry UI. These are described in `docs/report.md`. This audit observed the extension toolbar action still present in Chrome, but did not repeat the entire browser workflow; the foreground tab was another page. Neither earlier records nor this audit establish spoken VoiceOver/NVDA behavior.

**Partially working:** generated text can be vague, copy article facts or fail identity-attribution instructions. The pilot has ten successful image-only outputs and nine successful context-aware outputs. One periodic-table output exceeded the word limit. Human ratings and image/context association audits are pending. Some infobox captions are missed.

**Incomplete:** complete screen-reader/reflow verification, independent human review, robust reproducibility configuration in the benchmark/feasibility CLIs, portable dataset packaging and Git history. Second model, C pipeline, training, databases and deployment are planned/out of scope.

The operational core of the agreed milestone is demonstrated. The credible checkpoint is not fully closed until accessibility and source/output review are recorded. There is no current hardware or live API blocker. The greatest evidence gaps are actual assistive-technology testing and blank quality reviews; the highest-priority engineering issue is the CLI configuration mismatch described below.

No application source, existing settings, original pilot outputs or Git commits were changed in this audit. New audit evidence is under `artifacts/audit`; this document is the handover deliverable. Substantial fixes await approval.

## 2. Repository audit

All paths below are relative to `/Users/mayank/Documents/minorProject`.

```text
minorProject/
├── backend/
│   ├── app.py                 FastAPI factory, lifespan, endpoints, inference lane
│   ├── schemas.py             strict Context/request/response models and URL rules
│   ├── settings.py            .env/environment settings for the server
│   ├── errors.py              typed ProjectError
│   ├── data/images.py         fetch, base64, image safety/preprocessing
│   ├── models/smolvlm.py       real model adapter and ModelOutput
│   └── engine/
│       ├── prompts.py         ab-1 prompts and baseline separation
│       └── generate.py        shared generation and output validation
├── extension/
│   ├── manifest.json          MV3 permissions and script entry points
│   ├── context_extractor.js   WikiContext eligibility/extraction
│   ├── content.js             page controls, state, focus and rendering
│   ├── service_worker.js      toolbar/messages, image fetch, local API transport
│   └── options.html/options.js local token form/storage
├── benchmark/
│   ├── build_dataset.py       public source collection and license metadata
│   ├── run.py                 paired inference, append/resume JSONL
│   ├── analyze.py             CSV/HTML/counts/latency report
│   ├── annotation_rubric.md   manual scoring instructions
│   ├── manifests/pilot.jsonl  ten source/image/context records
│   ├── manifests/pilot.exclusions.json collection exclusions
│   └── results/pilot/         recorded handover results, described below
├── scripts/
│   ├── configure.py           random local token, preserves existing token
│   ├── smoke.py               authenticated real API request on frozen image
│   └── feasibility.py         bee vs red-square real visual inference
├── tests/
│   ├── conftest.py            clearly named test-only model fixture
│   ├── test_api.py            API/auth/errors/deadline checks
│   ├── test_images_prompts.py image/prompt/output checks
│   ├── test_evaluation.py     paired logs/resume/failures/blank reviews
│   ├── extension.test.cjs     jsdom extraction and UI regressions
│   ├── browser_fixtures/article.html controlled DOM fixture
│   └── accessibility_checklist.md actual vs outstanding checks
├── docs/
│   ├── PRD.md                 supplied broader PRD preserved
│   ├── report.md              previous milestone evidence/limits
│   ├── contracts.md           API and transport contract
│   ├── decisions.md           scope/architecture decisions
│   ├── experiment_protocol.md fixed pilot protocol
│   ├── team.md                four-person ownership
│   ├── demo_script.md         presentation sequence
│   └── HANDOVER_AUDIT.md       this current audit
├── README.md                  existing installation/use overview
├── requirements*.in           direct dependencies; not exact locks
├── requirements*.txt          exact installed core/model dependency versions
├── package.json/pnpm-lock.yaml jsdom test dependency/scripts
├── .env.example               public configuration template
├── .env                       private local settings, ignored
├── .gitignore                 ignores secrets, dependencies, large artifacts
├── .venv/                     installed Python runtime, ignored
├── .cache/huggingface/         local checkpoint cache, ignored
├── node_modules/              installed JS dependencies, ignored
└── artifacts/                 frozen pixels/HTML, original runs, audit data, ignored
```

Application entry points: `backend.app:app`; extension manifest's worker/content scripts; `python -m benchmark.run`; `python -m benchmark.analyze`; `python -m benchmark.build_dataset`; the three scripts above. `__init__.py` files establish Python packages.

Git: branch `main`, **no commits**, zero tracked files. All public source/docs/dependency/result files are untracked. `git diff --stat` is empty because untracked files do not appear in a normal diff. There is no trustworthy historical baseline for per-file authorship or modifications. Existing files cannot be individually attributed from Git. The earlier milestone report says the repository began empty; that statement is a project record, not independently reconstructed Git history. Do not interpret untracked as unused.

Generated evidence: `benchmark/results/pilot/generations.jsonl`, `review.csv`, `comparison.html`, `summary.md`, `feasibility.json`, `api-smoke.json`; corresponding originals remain in ignored `artifacts`. Audit confirmed original and handover generation logs are byte-identical. Local prepared PNGs/source HTML are also ignored. Cache is 8.4 GB, `.venv` 809 MB, node_modules 16 MB, artifacts 17 MB as measured during audit.

Technical debt: benchmark and feasibility CLIs bypass Settings; collector and browser use separate extraction algorithms; report analyzer takes the last record per sample/mode but counts all attempts; private Starlette `request._body` is used to bound streaming JSON; `run_generation` hides original inference exception details behind a safe generic error; a few imports are unused. No second production captioner or database exists. The POST alias is intentional, not a duplicate model pipeline. Historical feasibility and handover copies are evidence snapshots, not live caches.

## 3. Exact setup and operation

### Prerequisites and audited versions

This Mac is arm64 Apple Silicon, macOS 27.0.1, Python 3.12.14. Installed: torch 2.14.1, torchvision 0.29.1, transformers 4.57.1, accelerate 1.15.0, FastAPI 0.143.0, Starlette 1.7.0, Pydantic 2.14.0, Pillow 12.3.0, httpx 0.28.1, pytest 9.1.1. Node 24.19.0, pnpm 11.25.0, uv 0.11.33. Full pins are in the two requirements TXT files. System macOS Python 3.9 is unsuitable. Exact installs on a fresh machine were not repeated in this audit; installed-package compatibility and execution were verified.

The model runs locally using the M2's Metal/MPS accelerator and shared RAM. A separate NVIDIA GPU and hosted API are unnecessary. Float16 weights for roughly 2.2B parameters alone imply roughly 4.4 GB before buffers/activations; that is an estimate, not a measured process peak. Peak RAM was not profiled. Operate one model process at a time and close memory-heavy applications if needed.

### Terminal 1 — Backend, using the prepared machine

Open Terminal and run these commands in sequence. Every block in this guide uses the repository root unless stated otherwise.

```sh
cd /Users/mayank/Documents/minorProject
source .venv/bin/activate
python --version
export HF_HOME="$PWD/.cache/huggingface"
export PYTORCH_ENABLE_MPS_FALLBACK=1
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

`python --version` should show the audited 3.12.14 here. Uvicorn loads the official processor/checkpoint before startup finishes. The successful startup indicator is Uvicorn's application startup completion; readiness must then be checked from Terminal 2. First startup may download model files. Do not use `--reload`, and do not start another backend while port 8000 is occupied. A backend is already running as of this audit; reuse it or deliberately stop it before starting another.

If activation fails, check that `.venv/bin/activate` exists and follow the fresh-install branch. If model loading fails, the server can start degraded: inspect Terminal 1 and `/health`; it will not substitute fake descriptions. If address-in-use occurs, stop the existing project server in its terminal with Control-C; do not kill unrelated processes.

### Fresh installation only when `.venv` is absent

On this prepared Mac the bundled Python and uv are available at the absolute paths below. These paths belong to this machine and may differ for teammates. Do not recreate or overwrite the existing environment during ordinary startup.

```sh
cd /Users/mayank/Documents/minorProject
/opt/homebrew/bin/uv venv --python /Users/mayank/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 .venv
UV_CACHE_DIR="$PWD/.cache/uv" /opt/homebrew/bin/uv pip install --python .venv/bin/python -r requirements.txt -r requirements-models.txt
source .venv/bin/activate
python -m scripts.configure
```

Creation/install success means the environment exists and dependencies install without an error; the subsequent tests and readiness checks are the operational verification. Internet and adequate disk space are needed. If a pin cannot be installed, preserve the error and check Python/arm64 compatibility before changing versions. The current uv-created environment **does not contain pip**: `python -m pip check` failed with `No module named pip`. Use uv here. A normally created Python venv may contain pip, but do not assume this one does.

`scripts.configure` reads existing `.env`, or uses `.env.example` when absent, replaces the placeholder token with a random value, writes `.env` with mode 600 and prints a configuration message without the token. Do not run `cp .env.example .env` over your current private settings.

Review `.env` locally in an editor. Required settings:

| Variable | Current/use |
|---|---|
| LOCAL_BACKEND_TOKEN | configured, intentionally redacted; must match Chrome options |
| ALLOWED_EXTENSION_ID | kddogmjgjgaloghnamkhpmpjoeeamhfi on this installation |
| MODEL_DEVICE | auto; chooses CUDA, then MPS, then CPU |
| MODEL_REVISION | 482adb537c021c86670beed01cd58990d01e72e4 |
| LOAD_MODEL | 1 for real generation; 0 gives a degraded API only |
| MAX_NEW_TOKENS | 192 |
| REQUEST_TIMEOUT_SECONDS | 120 |
| HF_HOME | export the absolute repository cache path before model commands |
| PYTORCH_ENABLE_MPS_FALLBACK | export 1 before model commands |
| WIKIMEDIA_USER_AGENT | currently still a contact placeholder; set a real team contact before collection |

Server Settings loads `.env`. Other model/collector entry points do not consistently do so; export shell variables and use the pinned evaluation wrapper below. Keep tokens out of screenshots, Git and shared documents. Local token storage in Chrome is not an encrypted credentials vault.

### Terminal 2 — Health, inference checks and tests

Open a second terminal; keep Terminal 1 running.

```sh
cd /Users/mayank/Documents/minorProject
source .venv/bin/activate
curl http://127.0.0.1:8000/health
python -m scripts.smoke
python -m pytest -q
UV_CACHE_DIR="$PWD/.cache/uv" /opt/homebrew/bin/uv pip check --python .venv/bin/python
```

Health was freshly observed as HTTP 200, `status: ok`, `model_ready: true`, `busy: false`, processing local, authentication/extension configured. Smoke should print HTTP 200 and actual generated JSON; exact description/time can differ. It reads the private token and first frozen manifest image, then writes `artifacts/api-smoke.json`, so use it only when intentionally updating that latest smoke record. This audit used separate filenames instead. If that image is missing, do not substitute invented results: restore the frozen dataset or collect a new one separately.

Observed test output: 18 passed in 0.55 seconds, one TestClient deprecation warning; dependency check: all 52 packages compatible. Test failure means inspect the reported assertion; do not declare the integration healthy based solely on these tests.

For JS tests, the installed Node works directly:

```sh
cd /Users/mayank/Documents/minorProject
/Users/mayank/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/extension.test.cjs
```

Observed: 3 passed, 0 failed, 0 skipped, about 0.42 seconds. If jsdom is missing, install from the lockfile using the bundled pnpm:

```sh
/Users/mayank/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node /Users/mayank/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs install --frozen-lockfile
```

That install is for dependency setup; it was not rerun during this audit because dependencies already existed. Success means the lockfile is accepted and jsdom resolves; rerun the JS tests afterward.

### Chrome — Extension

1. Open `chrome://extensions`. Enable Developer mode, choose Load unpacked and select `/Users/mayank/Documents/minorProject/extension`.
2. Read the new extension ID. Set `ALLOWED_EXTENSION_ID` in `.env` to that exact ID; restart the backend if it changed. IDs may differ on another machine.
3. Open Details → Extension options. Copy the private LOCAL_BACKEND_TOKEN value into the labelled field and save it. This installation already has the approved token saved; do not share it.
4. Open `https://en.wikipedia.org/wiki/Common_sunflower`, activate Toggle Wikipedia image descriptions, choose Go to image 1, then activate Describe. Native buttons support keyboard operation.
5. Wait for the short loading status. Read description focuses the generated result heading. More detail and Refresh trigger new inference. Cancel suppresses display but can leave GPU work running. Disable removes the injected interface. Original alt text remains intact.
6. Repeat on `https://en.wikipedia.org/wiki/Moon`. The existing recorded live outputs were a sunflower description at 5.2 seconds and a very brief Moon description at 4.6 seconds. Those are observations, not guaranteed future text.

After editing extension files, click Reload for this extension in `chrome://extensions`, then refresh the Wikipedia article and activate again. Reloading only the extension does not replace already-running content scripts in an old page.

### Stop/restart

Control-C in Terminal 1 stops the backend. Active compute may take time to finish; cancellation is not a GPU interrupt. Restart with the same backend block and verify health again. Closing a Wikipedia tab or disabling the extension removes its page controls; it does not stop the backend. Do not delete model caches or `.env` to restart.

### Common errors

| Symptom | Cause/action |
|---|---|
| Connection refused / fetch failed | Backend absent/wrong port; start Terminal 1 and check health |
| Health degraded, descriptions 503 | Weights/processor/MPS failed or LOAD_MODEL=0; inspect startup, cache and dependencies |
| 401 UNAUTHORIZED | Saved Chrome token differs from .env; correct it locally |
| 403 ORIGIN_DENIED | Wrong extension ID; edit backend setting and restart |
| 429 BACKEND_BUSY | Wait for actual compute to end; avoid repeated activation |
| 504 GENERATION_TIMEOUT | Caller timed out but lane can remain busy; wait, inspect server, then retry |
| 413/415/422 | Size, unsupported raster, malformed base64 or schema; choose a supported thumbnail/input |
| IMAGE_FETCH_FAILED | Source unavailable/redirect/network timeout; choose another thumbnail; do not bypass browser security |
| OUTPUT_REJECTED | Overlong/markup/confidence output; record failure, choose another example or retry transparently |
| No controls | Canonical English /wiki/ article required; refresh after extension load/reload |
| Generic/incorrect description | Real model limitation; compare pixels/context and report it, never replace it with canned success |
| No module named pip | Use repository-local-cache uv commands above |

## 4. End-to-end data trace

| Stage | Actual code/function | Data and behavior |
|---|---|---|
| Article opened | manifest content_scripts; WikiContext.supported | Only English /wiki/ pages; excludes decoded colon namespaces and action/diff requests |
| Enable/select | worker chrome.action.onClicked; content enable/scan | TOGGLE; eligible image buttons and navigator are inserted on demand |
| Image eligibility | WikiContext.eligible | Wikimedia src/currentSrc, at least 32×32, heuristic nav/icon filtering |
| Context extraction | WikiContext.extract; clean | Stable per-element occurrence UUID; fresh request UUID; title, own-container caption, heading, nearby paragraphs, alt, revision if meta exists |
| Request construction | content describe; worker onMessage | mode=context_aware, concise/detailed; article canonical URL; worker downloads selected image and adds base64 |
| API validation | limits_and_origin; DescribeRequest; describe | Origin/body limits first; strict JSON fields/URL/context limits; bearer auth/model readiness/lane check |
| Pixels and prompt | app work; prepare_image; run_generation/build_prompt | Safe RGB raster, max768 side; title/caption/heading/nearby only in context-aware prompt; alt excluded |
| Model inference | SmolVLM.generate | official chat template, actual pixel_values, greedy192tokens, synchronized measured generation |
| Response | DescribeResponse; project_error/validation_error | Generated text/IDs/model/revision/timings/hashes/limitations or safe typed error |
| Display | content describe/showResult | Rejects stale/cancelled/mismatched snapshots; textContent; short status and result heading |
| Evaluation recording | benchmark.run.run, separately | Browser requests are NOT persisted as experiment rows; benchmark directly invokes shared model/engine and writes JSONL |

Title is required; caption, section, nearby text, existing alt and revision may be null. Empty alt remains distinct from missing alt. Missing context is passed explicitly; no fabricated caption is added. Context-aware still receives the title and whatever fields exist. Image-only request schema still requires context metadata, but its prompt contains none of it. Image URL/file names are not supplied to the model. Worker downloads public image bytes without cookies and denies redirects. If bytes are present, backend validates URL provenance but does not refetch it or prove those bytes correspond to that URL.

Errors from the worker become `{error: message}` to the content script; typed backend JSON is converted to a readable error/status and Retry. A model error or validation reject never becomes fixture text. Cancellation discards the result locally; request deadlines retain the inference lock until actual work ends. Normal page links/alt attributes are not rewritten.

## 5. API and model

Explicit endpoints: GET `/health`; POST `/describe`; POST `/v1/descriptions` (same handler). FastAPI also supplies GET `/docs`, `/redoc`, `/openapi.json` and `/docs/oauth2-redirect`. Those automatic documentation/schema routes do not perform inference. No database/history/evaluation-upload endpoint exists.

GET health has no body/token requirement. It returns status, model_ready, model_id, model_revision, processing, busy, schema_version, authentication_configured, extension_configured and configuration_fingerprint. Example observed state is described above. A degraded health response is still HTTP 200; inspect model_ready, not just the HTTP code.

Both POST routes require `Authorization: Bearer <LOCAL_BACKEND_TOKEN>`. A browser Origin, if supplied, must equal the configured extension origin; CLI clients can omit Origin. Shared request fields:

| Field | Rules |
|---|---|
| schema_version | literal 1.0, default 1.0 |
| request_id / occurrence_id | required strings, 1–64 / 1–128 characters |
| article_url | required, ≤2048; HTTPS en.wikipedia.org canonical /wiki/, no query |
| revision_id | optional positive integer/null |
| image_url | required ≤2048; HTTPS exact upload/thumb.wikimedia.org, /wikipedia/ path, no credentials/fragment/other port |
| image_base64 | optional raw base64, no data-URL prefix; ≤11184812 characters; decoded ≤8MiB |
| context.article_title | required 1–300 characters |
| caption / section_heading / nearby_text / existing_alt | nullable, max1200/300/3200/600 characters |
| mode | image_only or context_aware; defaults context_aware |
| detail | concise or detailed; defaults concise |

Unknown fields rejected; aggregate context ≤800 words/8000 characters; JSON body ≤12,000,000 bytes; images ≤20MP. A concise output over120 words is rejected; detailed limit250.

Illustrative URL-only request (not a new observed request; the smoke script is the verified bytes path):

```json
{
  "request_id": "example-001",
  "occurrence_id": "image-1",
  "article_url": "https://en.wikipedia.org/wiki/Common_sunflower",
  "image_url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/40/Sunflower_sky_backdrop.jpg/960px-Sunflower_sky_backdrop.jpg",
  "context": {"article_title": "Common sunflower", "caption": null, "section_heading": null, "nearby_text": null, "existing_alt": ""},
  "mode": "context_aware",
  "detail": "concise"
}
```

Actual audit response for the frozen bytes is saved at `/Users/mayank/Documents/minorProject/artifacts/audit/live-api.json`:

```json
{
  "schema_version": "1.0",
  "request_id": "handover-audit-001",
  "occurrence_id": "pilot-01",
  "description": "A sunflower with yellow petals and a brown center is in front of a blue sky.",
  "mode": "context_aware",
  "detail": "concise",
  "model_id": "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
  "model_revision": "482adb537c021c86670beed01cd58990d01e72e4",
  "prompt_version": "ab-1",
  "inference_ms": 5659.308415997657,
  "total_ms": 5981.211292004446,
  "image_hash": "0b26feb48a993968c3fc5ddc9e4e6fd6465f780bfedc433ec6f2404fa47c198a",
  "context_hash": "925098bc72cccf3cd8f865d24ee678c617c4989231b440808a84b24fe9679e6a",
  "generated": true,
  "limitations": ["AI-generated; visual facts and contextual claims may be incorrect."]
}
```

Errors normally use `{"status":"error","error":{"code":"…","message":"…","retryable":true}}`; origin/body middleware omits the top-level status, so the error envelope is not completely uniform. Codes: 401 UNAUTHORIZED; 403 ORIGIN_DENIED; 413 REQUEST_TOO_LARGE/IMAGE_TOO_LARGE; 415 UNSUPPORTED_IMAGE; 422 INVALID_REQUEST/INVALID_IMAGE; 429 BACKEND_BUSY; 502 IMAGE_FETCH_FAILED/EMPTY_OUTPUT/OUTPUT_REJECTED; 503 MODEL_UNAVAILABLE/INFERENCE_FAILED; 504 GENERATION_TIMEOUT. TrustedHost can return400 independently. Unexpected unhandled exceptions can still produce500; no universal exception envelope is implemented.

The model is the published instruction checkpoint [HuggingFaceTB/SmolVLM2-2.2B-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct), Apache-2.0 as confirmed from its official card. This project performs pretrained-checkpoint inference, with no project-specific fine-tuning. SmolVLM.load uses AutoProcessor and AutoModelForImageTextToText, eager attention, eval mode, low_cpu_mem_usage, MPS float16 here. CPU uses float32 and would be slower; CPU speed was not measured. Processor splitting is enabled, longest edge768, patch384. Shared `ModelOutput` is text/inference_ms/tokens/finish_reason; replacement adapters must expose ready, IDs/revision, load, configuration and generate(image,prompt).

`backend/engine/prompts.py` version ab-1 holds common visible-evidence instructions plus either image-only instruction or serialized article context. Existing alt is withheld in both. Decoding and pixels are identical between conditions. Validation detects emptiness, excess length, HTML/code markup and certain confidence claims; it does not verify factual grounding. Inference timing covers synchronized model.generate, excluding load, image fetch and processor work. Total API time covers worker-side backend preprocessing/generation, excluding the extension's download/transit/UI time. Do not call either number end-to-end user latency.

## 6. Evaluation audit and reproduction

| Item | Current state | Evidence |
|---|---|---|
| Manifest | 10 real occurrences, development convenience sample | benchmark/manifests/pilot.jsonl |
| Frozen images | 10/10 present; recomputed hashes match | artifacts/dataset/pilot-01.png … pilot-10.png |
| Image-only | 10/10 successful, no context in current/recorded prompts | generations.jsonl + isolation tests |
| Context-aware | 9/10 successful; one length reject | pilot-08 OUTPUT_REJECTED |
| Paired experiment | 20 attempts, 9 complete successful pairs | generations.jsonl; recomputed summary |
| Human review | 10 rows, all rating fields blank | benchmark/results/pilot/review.csv |
| Latency | successful medians A3.65s, B4.78s | recorded inference_ms; analyzer rerun |
| Attribution | license/author/revision metadata recorded, human checks pending | manifest association_review fields |

Examples: sunflower, bridge, Einstein portrait, Moon, bicycle, butterfly, water-cycle diagram, periodic table, world map, solar-system diagram. Collector selects the first candidate with recognized license metadata from a fixed ordered list of twelve articles, stopping at limit10. It stores source HTML, prepared PNG, article revision/permanent link, file timestamp/SHA1/page, license URL/author/attribution, image category, context and prepared hash. A recognized string is not a completed legal/source audit; two samples have GFDL1.2 metadata and require careful fulfillment before redistribution. All association_review fields remain pending.

Runner calls the shared adapter directly, A then B per image, same pixels/settings; JSONL flushes each success/failure. Resume uses sample/mode/image/prompt/config hashes and includes failed cells. A fresh filename is required for an intentional retry/new experiment. Existing alt is retained as metadata, not ground truth. Model knowledge may identify a famous bridge even in image-only mode; isolation prevents contextual input leakage, not pretrained knowledge.

`review.csv` includes outputs, latencies/errors, reviewer_id, visual_factuality, contextual_relevance, usefulness, clarity_concision, unsupported_claims for each condition, and review_notes. Rubric: first four are1–5, unsupported claims is a count; reviewers save separate sheets. Blank is not zero.

### Terminal 2 — Recompute reports without loading another model

Safe while the backend remains running:

```sh
cd /Users/mayank/Documents/minorProject
source .venv/bin/activate
python -m benchmark.analyze --manifest benchmark/manifests/pilot.jsonl --runs benchmark/results/pilot/generations.jsonl --output artifacts/audit/recomputed
```

Actually run during audit: prints ten examples, twenty attempts, nine complete pairs, medians3.65/4.78s; creates comparison.html/review.csv/summary.md in that new directory. If input files are missing/mixed-config, preserve the error and use the original matching manifest/run. Do not fill review scores automatically.

### Terminal 2 — New pinned real inference run

First stop the backend in Terminal 1 to avoid loading a second model. Use a new output filename; the example below may append/resume if you reuse it. This wrapper explicitly sets checkpoint revision because **`python -m benchmark.run` currently constructs SmolVLM() with revision main and ignores .env model settings**.

```sh
cd /Users/mayank/Documents/minorProject
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
export PYTORCH_ENABLE_MPS_FALLBACK=1
python - <<'PY'
from backend.models.smolvlm import SmolVLM
from benchmark.run import run
model = SmolVLM(revision='482adb537c021c86670beed01cd58990d01e72e4', device='auto', max_new_tokens=192)
model.load()
run('benchmark/manifests/pilot.jsonl', 'artifacts/runs/pilot-audit-rerun.jsonl', model)
PY
python -m benchmark.analyze --manifest benchmark/manifests/pilot.jsonl --runs artifacts/runs/pilot-audit-rerun.jsonl --output artifacts/results/pilot-audit-rerun
```

This exact new run was not executed during the audit; original real runs were inspected instead of repeated. Success prints one line per attempted cell with status/time and writes actual JSONL. Failures remain valid evidence. If hashes fail, stop: do not alter the frozen manifest to conceal changed images. Restart Terminal 1 after the model command exits.

### New collection and visual feasibility

Do not recollect over the frozen pilot during an audit. `build_dataset` writes pilot-NN image filenames in a fixed artifacts/dataset directory even with a different manifest output. For a new dataset, copy the project to a separate development folder or archive the old dataset first with explicit coordination. From that separate project root, export a real WIKIMEDIA_USER_AGENT, run `python -m benchmark.build_dataset --limit 10`, and review metadata/images/context before freezing. Network/source failures are recorded separately.

`python -m scripts.feasibility` loads another real model and downloads bee.jpg, then generates on bee and a red-square fixture. It writes artifacts/feasibility.json and uses revision main by default; do not run it concurrently with the server or claim it reproduces a pinned checkpoint without addressing that issue. Previously saved final feasibility is inspected: load25.72s, bee5.47s, square3.64s with visually different outputs. The script's hardware label is hardcoded and must not be reused as hardware measurement on another computer.

Results interpretation: a bridge B output copies long article facts; Einstein B names Einstein without the requested caption attribution; water-cycle B leans on caption text; bicycle/butterfly pairs were identical. These are observations, not scores or evidence of benefit. The failed periodic-table B raw text/inference time was not retained by the initial logger; only failure/total16.07s exists. Current code retains raw validation failures for future runs. Fixed order, convenience selection, one run and no participant study prevent efficacy/significance claims.

## 7. Verification results

| Executed check | Result and limits |
|---|---|
| python -m pytest -q | 18 passed; 0 failed/skipped; 0.55s; one Starlette TestClient deprecation warning |
| bundled node --test tests/extension.test.cjs | 3 passed; 0 failed/skipped; 0.42s |
| python -m pip check | Failed: pip absent; no dependency incompatibility inferred |
| uv pip check with repository cache | 52 installed packages compatible |
| GET /health | Fresh200, model_ready true, busy false, correct pinned revision |
| Fresh context-aware API | 200; sunflower; 5.66s inference,5.98s total |
| Fresh image-only API | 200; sunflower; 4.33s inference,4.53s total; context hash of empty object |
| Manifest image/prompt verification | All10 hashes and all20 prompt strings match current implementation |
| Original vs handover JSONL | Byte-identical |
| benchmark.analyze rerun | Reproduced20 attempts/9 pairs/medians; blank ratings |
| Chrome current inspection | Extension action present; full live workflow not repeated during audit |

Local requests first failed within the execution sandbox with Operation not permitted. Approved execution outside that sandbox reached the existing backend and produced real responses; this was a tool execution constraint, not a confirmed application networking failure. No fresh model process was started during audit because an existing ready server was available. Backend start is supported by the earlier recorded demo and current functioning server, rather than an audit restart.

Unit tests substitute `unit-test-fixture` only in tests. They verify contracts and failure behavior, not SmolVLM.load/generate internals, service-worker networking, actual GPU memory, full browser navigation or spoken assistive technology. Real API and saved feasibility/pilot provide separate model evidence. The `test_paired_logging` test has one fixture pair and failure logging, not a real statistical experiment.

## 8. Ranked issues

| Priority/status | Impact | Recommended action |
|---|---|---|
| P1 confirmed quality failures | Article copying, missing caption attribution and vague descriptions reduce usefulness; one output rejected | Review outputs against pixels/context, then version prompt changes; no silent post-edits |
| P1 unverified accessibility | Native labels/status/focus do not prove spoken announcements/reflow | Person4 run actual VoiceOver + keyboard/reflow matrix and record failures |
| P1 confirmed CLI config gap | Benchmark/feasibility use main/defaults, so .env pin/device/token settings do not govern them | Person2 unify model settings; use explicit pinned wrapper meanwhile |
| P1 confirmed collector overwrite behavior | New manifest output still reuses artifacts/dataset/pilot-NN files, risking frozen pixels | Person1 isolate dataset output roots before future collection |
| P1 pending review | All ten context associations and human ratings remain unreviewed | Audit source associations/licenses, then independent ratings |
| P1 reproducibility gap | Git has no commits; ignored pixels/HTML won't travel with normal Git sharing | Agree on source baseline and permitted frozen-data packaging; commit only with permission |
| P1 confirmed extraction divergence | Offline collector searches arbitrary previous/next paragraphs; browser bounds sections; captions can differ | Person1 align semantics and add real frozen-HTML fixtures |
| P2 confirmed missed captions/heuristics | Separate-row infobox captions missed; conservation graphics can be eligible; stale labels possible after DOM edits | Add fixture-driven caption/eligibility/label refresh checks |
| P2 diagnostic gap | Generic INFERENCE_FAILED hides exception cause from app logs | Add sanitized server-side exception diagnostics without payload/token exposure |
| P2 error-envelope difference | Origin/size errors omit status; unexpected exceptions may be500 | Standardize documented errors after core review |
| P2 analyzer aggregation risk | Multiple records for one sample/mode select last output but count all attempts | Reject duplicates or explicitly report attempts vs selected pairs |
| P2 secret/storage risk | .env ignored and token redacted, but local Chrome storage isn't a secure vault | Keep loopback-only, don't publish token; define team credential procedure |
| P2 image/provenance risk | Bytes supplied by local clients need not match the validated provenance URL | Treat provenance as supplied metadata; do not assume cryptographic source authenticity |
| P2 namespace-validation risk | Backend colon check uses raw URL path while browser decodes it | Align validators; verify percent-encoded namespace cases |
| P2 dependency warning | TestClient httpx deprecation; code works now | Track supported migration, avoid blind dependency upgrades |
| P2 memory/network risk | 16GB/shared RAM and source timeouts can affect long requests; peak unmeasured | Profile one-process memory; keep current limits and don't parallelize models |

No confirmed current CORS/auth outage: live requests succeed, wrong origins/auth are rejected in tests. No comprehensive license compliance, browser-version coverage or universal Wikipedia DOM support is claimed. Deterministic output validation cannot solve hallucination. Current API permits only local client deployment; production hosting is outside this handover.

## 9. Four-person handover

| Owner | Own files | Implemented/verified | Next responsibility |
|---|---|---|---|
| Person1 | extension/context_extractor.js; backend/data/images.py; benchmark/build_dataset.py; manifests; DOM fixtures | bounded extraction/image safety, ten source examples, extraction tests | audit associations/licenses; fix dataset isolation and collector/browser divergence |
| Person2 | backend/models/smolvlm.py; scripts/feasibility.py; benchmark/run.py/analyze.py; results | real adapter, isolated baseline, paired logs, timing/reports | pin shared configuration, profile memory, preserve/reproduce logs; coordinate reviewer files |
| Person3 | backend/engine/prompts.py/generate.py; annotation_rubric.md | ab-1 branches, basic validation, actual failure records | inspect unsupported claims/copying; version changes after review |
| Person4 | backend/app.py/settings.py/schemas.py/errors.py; extension UI/worker/options; scripts/configure.py/smoke.py; setup/demo docs | functioning server/transport/UI, typed errors, recorded Chrome demo | VoiceOver/reflow/error workflow audit, integration fixes and final demo rehearsal |

Shared interfaces: Context and DescribeRequest/Response in schemas.py; schema_version1.0; worker messages TOGGLE/DESCRIBE → result/error; adapter load/configuration/generate and ModelOutput; rgb-768-v1 preprocessing; ab-1 prompt/config/image hashes and run-record schema. Person4 is the API steward; each owner coordinates changes affecting another consumer before editing. Person1 must not add context fields independently; Person3 must bump prompt version for semantic changes; Person2 must preserve failed rows and separate settings/run files. Unit fixtures need corresponding updates. Do not overwrite another reviewer's sheet.

Integration sequence: Person4 and2 agree on shared model settings; Person1 freezes audited input associations/data locations; Person3 reviews against that frozen input and proposes a new prompt; Person2 runs both modes into a new file; Person4 verifies the same build in Chrome/VoiceOver; reviewers complete separate sheets; combine evidence only after these gates.

## 10. Next intensive session

Estimates are planning estimates, not measured task durations.

| Priority/task | Owner | Dependencies | Effort | Objective done criterion |
|---|---|---|---|---|
| P0 pre-demo check | Person4 | existing build/cache | 15–30min | ready health, one new Chrome result, repeat on second article; record actual output/error |
| P1 spoken accessibility audit | Person4 | ready demo | 1–2h | VoiceOver reads result and announces loading/ready/error; keyboard/zoom failures documented and addressed |
| P1 shared pinned model configuration | Person2 | agreement with Person4 | 45–90min | backend/run/feasibility log same configured revision/device/token limit; test confirms propagation |
| P1 input/license audit | Person1 | existing frozen files | 1–2h | all10 associations reviewed and attribution obligations recorded; wrong associations marked explicitly |
| P1 preserve future dataset roots | Person1 | input inventory | 30–60min | new collection cannot overwrite frozenpilot files; distinct manifest/root verified |
| P1 independent reviews | Person3 coordinates; two team reviewers | Person1 audit | 1–2h/reviewer | separate completed sheets with claims/evidence, failures included; no scores invented |
| P1 prompt revision if justified | Person3 | reviews | 1–2h | ab-2 documented examples/acceptance checks; keep ab-1 evidence untouched |
| P1 new paired run/report | Person2 | audited inputs/newprompt/config | 30–60min | fresh20attempt matrix, rawfailures/timings, matching hashes and report |
| P1 final rehearsal/handover | Person4 | preceding evidence | 30–45min | live demo plus honest report; source/data backup agreed, no claims beyond evidence |
| P2 second VLM/C/larger set/cache | respective owners | allP1 gates | separate future sprint | protocol and measured benefit justify scope; do not start now |

**Single highest-priority next action:** perform and record the actual VoiceOver accessibility audit of the current working extension before presenting it as an accessibility milestone. It addresses the main unverified user-facing gate without changing prompts or hiding pilot failures. Substantial fixes discovered during it require approval under this handover request.

## 11. Final checklist

- [x] Backend starts successfully — prior startup/demo evidence plus currently running ready service; audit did not restart it.
- [x] Health endpoint works — fresh HTTP200/model_ready true.
- [x] Real model inference works — fresh genuine A and B API responses; saved real visual feasibility.
- [x] Extension loads in Chrome — prior live record; toolbar action observed in this audit.
- [x] Real Wikipedia context extracted — implementation/DOM tests/manifest and prior live demo; source associations still require human audit.
- [x] Context-aware description generated — fresh HTTP200 and recorded pilot9/10.
- [x] Description appears in extension — previous actual Chrome verification on sunflower/Moon; not replayed during this audit.
- [x] Image-only baseline works — fresh HTTP200, isolation tests and pilot10/10.
- [x] Paired evaluation can run — real20attempt records and unit runner checks; current CLI pin caveat remains.
- [ ] Results saved reproducibly — partially verified: hashes/prompts/logs match locally; portable frozen-data/config setup incomplete.
- [ ] Basic accessibility checks completed — partially verified keyboard/focus; spoken screen-reader/reflow not tested.
- [x] Setup instructions complete — audited paths, prepared/fresh setup, explicit CLI workaround and troubleshooting above; fresh reinstall not repeated.
- [ ] Demo ready to present — operational live demo evidenced; accessibility/review gates remain before claiming the full credible checkpoint.
