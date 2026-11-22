# Evaluation and changes, November 2026

**Status:** development evidence plus a small held-out comparison. The two held-out CSV sheets each contain ratings and preferences for 56 items. The evaluation notes describe the first-pass comparison as judged by one person with model assistance; the files do not document reviewer identity or establish that the ratings are independent. Do not treat them as a reviewer-scored study or independent validation without confirming provenance. Hardware: Apple M5 / 16 GB, macOS 27.0.1, Python 3.15.0, torch 2.15.0, transformers 4.57.1.

## 1. Why a new evaluation set

The ten-image pilot used 960 px images and a 5-field context built by `build_dataset.py`. The extension does something different. It sends the page thumbnail it displays (`img.currentSrc`): about 250 px wide, or about 500 px on a Retina display. It also sends a richer context from `extension/context_extractor.js`. The pilot therefore did not measure the product.

The **live set** (`benchmark/manifests/live-v2.jsonl`) is built from the live article pages with the extension's own extractor (`benchmark/collect_live.cjs`, jsdom):

- 28 articles, none in the pilot, across animals, landscapes, buildings, objects, biographies, diagrams, processes, maps, charts, flags, artworks and astronomy.
- Two occurrences per article, chosen by rule (the first and the middle eligible image), not by hand: 56 occurrences.
- Split **by article** into `dev` (28) and `test` (28) before any run (`benchmark/manifests/live_articles.txt`).
- Each occurrence has two frozen images: `extension`, the largest `srcset` candidate (what a Retina Mac sends), and `large`, Wikimedia's 960 px thumbnail. Hashes, licenses and authors are in the manifest. 55 images are freely licensed; one (Frida Kahlo #21) is fair use and must not be redistributed.
- `benchmark/run_api.py` sends every request through the real FastAPI app with the loaded model, as the extension does.

## 2. Changes, in order, and the evidence for each

| Version | Change | Evidence (dev unless stated) |
|---|---|---|
| ab-8 | OCR noise filter; context-copy retry; over-long outputs keep whole sentences instead of a "Try again" that Retry could never fix | Pilot diagnostic: `benchmark/results/pilot-ab8/diagnostic.md` |
| — | OCR runs in parallel with type classification | Water-cycle analysis time 2.4–2.9 s → 1.3–2.0 s |
| — | Extension requests the 960 px thumbnail (not GIFs), falling back to the displayed image on any failure | Description comparison 4 better / 2 worse / 8 tie on dev images where the input differs; OCR read 71 vs 55 real words, e.g. 24 labels vs 3 junk tokens on the citric acid cycle diagram |
| ab-9 | Extractor: strips inline CSS (`.mw-parser-output .legend{…}` appeared in a caption), honorifics ("The Right HonourableThe Countess…"), and false caption subjects ("The image shows Biodiversity."). Internal routing fields hidden from the model. A description cut off at the token limit keeps only complete sentences | Leaked text 4 → 0; the runaway "p1, p2 … p31" list is trimmed |
| ab-10 | Other images' captions (`image_overview`) withheld from the model | It had described a tectonic-plate map as "including a paleomap drawn by Wegener" (another image's caption). Clear wins on dev-06, -12, -17, -28; losses looked like noise. A "no background knowledge" prompt rule was also tried and **dropped**: 8 better / 8 worse |
| model | **Qwen3-VL-2B-Instruct** (`89644892…`, Apache-2.0, 4.3 GB) replaces SmolVLM2-2.2B | Dev: Qwen better in about 45 of 56 outputs, about 8 ties, about 3 worse. Median latency 5.1/5.4 s vs 7.6/8.7 s (image-only/context); 95th percentile 8.0 s vs 20.8 s |
| ab-11 | The article's person is offered to the model only when the caption associates them with this image. Captions such as "Painting of Lovelace…" or "Mandela casting…" now resolve the subject | Found on the **test** set (a Frida Kahlo still life described as "Frida Kahlo is depicted…" by both systems); the fix was checked on dev only. See §4 |

## 3. Held-out result (test split, 56 requests per system)

**Before** is the handover code exactly (commit `7db426f`, ab-7, SmolVLM2), with the image the extension sent then and the old extractor's context. **After** is ab-10 with Qwen3-VL-2B, the 960 px image and the new extractor.

| | Before | After |
|---|---|---|
| Successful descriptions | 52/56 (4 "word limit" errors that Retry cannot fix) | **56/56** |
| Image-only latency, median / 95th percentile / max | 4.9 / 7.7 / 10.9 s | 4.9 / 5.9 / 6.4 s |
| Context-aware latency, median / 95th percentile / max | 8.2 / 9.5 / 12.1 s | **5.0 / 6.4 / 8.0 s** |
| First-pass pairwise judgement against the images | — | after better in about 44 of 56, about 9 ties, about 3 worse |

Examples (test split):

- **Mandela, lead image:** before, "The image shows His ExcellencyNelson MandelaOMP SBG SBS CLS DMG MMS MMB OM…"; after, "Nelson Mandela is shown in a close-up portrait… light blue shirt and a patterned tie".
- **Normal distribution:** before, an invented "α₂(x)" chart, and a repetition loop in context mode; after, it reads all four curves with their parameters.
- **Violin sizes:** before, "a violin and a cello"; after, "two violins, the larger behind the smaller".
- **Flag of Japan:** before, the article recited (Nisshōki, customs); after, it describes the flag.

Where *after* is worse or still wrong:

- The mitochondrion context-aware output puts ATP synthase in the matrix (the image-only output is correct).
- The Sagittarius A* image is not identified from its caption.
- Chart numbers can still be invented (the Ecuador pyramid's axes).

This is a first-pass, sighted judgment. Although the two saved sheets contain ratings and preferences, reviewer identity, independence, and agreement have not been established. Treat the result as exploratory.

## 4. Known limitations

- ab-11 has not been measured on the test split. Its fix came from reading test outputs, so measuring it there would be contaminated. It needs a fresh set.
- After ab-11, the 2B model will not name the Mona Lisa from the article title. It treats a painted person under the rule against identifying people. The handover's rule on people takes priority.
- Qwen3-VL-2B still invents some chart values and map details, and can misread small text ("EXERCITO BRASILEIRO" read as "ELIZABETE BRASIL"). OCR is still the weak point on dense diagrams.
- All judgements are a sighted proxy. No screen-reader user has evaluated these descriptions.
- On a 16 GB machine, do not run a benchmark or a second model process while the backend is serving. Memory pressure tripled latency in one measurement.
- A larger model (Qwen3-VL-4B, 8.9 GB) was not tried: on 16 GB with Chrome open, memory pressure is the main latency risk. It is worth testing on a 24 GB+ machine.

## 5. Files

- Manifests: `benchmark/manifests/live.jsonl` (v1 extractor contexts) and `live-v2.jsonl` (current extractor; the same frozen images).
- Dev runs: `benchmark/results/live-dev/*.jsonl`. Held-out runs: `benchmark/results/live-test/generations-{before,after}.jsonl`.
- Review artifacts: `benchmark/results/live-test/review_blind_reviewer_{1,2}.csv` contain ratings and preferences. The untracked local mapping key is `blind_key_DO_NOT_OPEN_BEFORE_REVIEW.csv`; keep it out of shared results until review and analysis are finalized. Rubric: `benchmark/annotation_rubric.md`.
- Images and article HTML are local only (`artifacts/live/`). Rebuild them with the commands in README.md.
