# Image-specific descriptions and local OCR — 12 October 2026

Prompt ab-5 adds six strategies: photo, flag, chart, map, process/lifecycle and diagram. The extension offers an accessible Description style selector beside each image; Automatic is the default. A user override wins, then a direct caption hint, then a short real VLM classification of pixels. Classification is a routing aid, not verified identity. Names still come from attributed associated Wikipedia captions/labels.

Each strategy emphasizes different information: photographs prioritize appearance; flags stripe order and emblems; charts axes/units/readable values and comparisons; maps labels/legends/spatial relations; processes readable stages and visible arrows; diagrams labels/layout/highlighting. Focused prompts avoid giving every image all six instruction sets. Context-aware prompts use directly associated caption and section heading; image-only prompts exclude article context. The conservation-status definition reference remains in its special source-grounded prompt.

## OCR

The production engine uses [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html) locally with English language data. Tesseract 5.5.3 was installed using Homebrew on this Mac. There is no cloud OCR, extra API key or Python OCR dependency. A fresh Mac needs `brew install tesseract`; other machines need an equivalent installation on PATH. If the engine or language data is absent, fails or exceeds the deadline, generation continues and complex-image results explicitly report the text-recognition limitation.

Tesseract runs sparse-text and uniform-text passes (PSM 11 and 6). Results retain independent word boxes, filter low OCR scores and duplicate detections, and bound prompt evidence to 16 words/1200 characters. Each pass has a seven-second deadline. API images are safely decoded and resized to at most 1600 pixels for OCR; the model still receives the established 768-pixel raster. The model prompt receives approximate upper/middle/lower and left/center/right text locations; detailed normalized top-left boxes remain in generation records. OCR strings are untrusted evidence, never instructions. Positions/reading order do not establish arrows, causal relations or chart associations. Scores are not model confidence claims.

An Apple Vision implementation was tried locally, but recognition repeatedly exceeded the intended runtime deadline while local VLM inference was active. It was removed from the production code; Tesseract is the verified implementation. No Swift compilation is required.

## Verification

41 Python tests and 11 extension tests pass. They cover routing, article-context isolation, user overrides, OCR filtering/positions/deduplication/deadlines, safe missing-OCR behavior, API style validation and the selector's request payload. Existing inline results, source-name prefixes, keyboard focus and read-aloud tests still pass. These checks do not establish real screen-reader usability.

Five real API inferences were performed with SmolVLM2 on MPS. Four images were explicitly synthetic development checks (not Wikipedia images or evaluation ground truth); the photo used the existing local bee photograph. Final raw API responses are in ignored `artifacts/image-types/verification-final.json`. Earlier trials were retained separately.

| Case | Route | OCR | Observed result |
| --- | --- | --- | --- |
| Process | process | ok | Described seed, seedling and adult plant in the drawn order. OCR recovered some stage words; the VLM also read the visible seed label. |
| Chart | chart | ok | Correctly associated Jan/Feb/Mar with 10/20/30. |
| Flag | flag | no_text | Described top-to-bottom black/red/yellow stripes; final prompt removed a previously invented aspect ratio. |
| Map | map | ok | Improved top/bottom placement of names but still misstated line relationships; OCR read some names only partially. |
| Bee photo | photo | ok | Still produced a terse description despite appearance instructions. |

OCR checks on the generated chart and process diagram took roughly 0.2 seconds after first initialization. This is not a representative accuracy or latency benchmark. Dense labels, map relations and consistently rich photo detail remain unresolved model-quality issues. The ten-case historical ab-1 pilot is unchanged. New benchmark runs include routing/OCR evidence in prompt hashes and retain raw model output separately from attributed labels; benchmark OCR uses frozen 768-pixel images and differs from the API's 1600-pixel OCR path.

To try locally: start `python3 run.py`; reload Wikipedia Image Descriptions in `chrome://extensions`; reload the Wikipedia article and enable the extension. Leave Description style at Automatic, or select a type and click Describe/Refresh. The generated result and Read aloud contain the same description. Previously generated text does not change until refreshed.
