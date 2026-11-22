# Wikipedia Image Accessibility Prototype

A Chrome extension and local Python service that generate image descriptions for Wikipedia pages. The service uses a locally run vision-language model and optional OCR. It can use article captions and nearby page text as context.

This is a research prototype. Generated descriptions can omit or misstate visual details. The held-out evaluation files contain two completed rating sheets, while the accompanying report describes a first-pass judgment by one person with model assistance. The files do not establish who reviewed them or whether the reviewers were independent. Treat all results as exploratory, not as proof of accuracy or accessibility benefit.

## Run the real model

### First-time setup

Requirements: Python 3.11 or 3.12, a supported local model setup, and Tesseract OCR. On Apple Silicon, allow several gigabytes for model files and memory. The setup below uses the repository's pinned dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-models.txt
cp .env.example .env
python -m scripts.configure
```

In `.env`, set `ALLOWED_EXTENSION_ID` to the ID shown for the unpacked extension at `chrome://extensions/`. Keep `.env` private. The configure script creates a local token; copy that token into the extension options.

### Start the backend

From the repository folder, run:

```bash
python3 run.py
```

Keep the terminal open. The first launch may download model files. Wait for “Application startup complete”, then check `http://127.0.0.1:8000/health` for `"status":"ok"` and `"model_ready":true`.

### Load and use the extension

1. In Chrome, open `chrome://extensions/` and enable **Developer mode**.
2. Choose **Load unpacked** and select this repository’s `extension/` folder.
3. Open the extension’s **Options** page. Enter the `LOCAL_BACKEND_TOKEN` from `.env` and save it.
4. Set `ALLOWED_EXTENSION_ID` in `.env` to this extension’s ID and restart the backend.
5. Open a Wikipedia article, reload the page, and use **Describe** beside an image.

The extension’s backend health button checks that the local service is reachable. A green health check does not verify model quality.

## Demo mode (no model required)

Demo mode returns sample descriptions based on the image filename and article text. It does not inspect image pixels and is only for checking the extension flow.

Stop the real backend with **Control+C**, then run in a separate terminal:

```bash
python3 mock_server.py
```

The mock server uses the same address, `http://127.0.0.1:8000`. Reload the Wikipedia tab and try **Describe**. Stop the demo with **Control+C** before restarting the real backend with `python3 run.py`.

## Tests

Activate the project environment and run:

```bash
python -m pytest -q
```

Install the extension test dependency from the lockfile, then run the tests:

```bash
corepack pnpm install --frozen-lockfile
pnpm test
```

The model is not needed for the automated tests. A live model request is a separate manual check.

## Evaluation and integration notes

- `benchmark/results/` contains saved development and comparison artifacts. The live comparison is small and sighted; reviewer independence and agreement have not been established, and no screen-reader users took part.
- `benchmark/manifests/` contains frozen metadata. Local image downloads and runtime artifacts are ignored by Git.
- `client/chakshu_client.py` is an example client interface; it does not mean this module has been integrated into the CHAKSHU service.
- `docs/evaluation_2026-11.md` describes evaluation details and known limitations. Do not make stronger claims without verifying reviewer provenance and evaluating on a fresh set.

## Project files

- `extension/` — Chrome extension
- `backend/` — API, local model, prompts, image processing, and cache
- `benchmark/` — dataset tools and evaluation artifacts
- `client/` — CHAKSHU interface example
- `docs/` — architecture, methodology, and project reports
