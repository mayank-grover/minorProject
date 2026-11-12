# ab-8 diagnostic on the frozen pilot (vs ab-7)

**Status: development diagnostic.** These changes were chosen using failures seen on this same pilot, so this run cannot show they generalise. A fresh, frozen set is needed for any claim. The tags are a first pass by one person (with model assistance) after inspecting the pixels. The reviewer sheets in this folder are blank.

Same machine, runtime, model, images and context as `../pilot-ab7/` (Apple M5 / 16 GB, Python 3.15.0, torch 2.15.0).

## What changed from ab-7

The prompt text is unchanged. Three changes were made to the pipeline:

1. **OCR noise filter** (`backend/engine/ocr.py`). The word-confidence floor rises from 0.50 to 0.75, and each word must contain a digit or at least two letters. Up to 24 words are kept instead of 16. Before, Tesseract fragments (`Lyi,`, `=`, `aN`) filled the slots from the top of the image and pushed out real labels. In the 768 px run the Solar System lost every planet name and the water cycle lost its title.
2. **Context-copy retry** (`backend/engine/generate.py`). A context-aware output that shares at least 12 consecutive words with the supplied article text is regenerated once without `nearby_text`, `page_summary` and `image_overview`; title and caption stay. The first output is kept in the record's `repair` field. If the retry still repeats article text, the limitation "Parts of this description repeat the article text." is added. On the pilot, the verbatim copies shared 44–97 words with the context; no other output shared more than 8.
3. **Sentence-boundary shortening** (`backend/engine/generate.py`). An output over the word limit keeps its whole leading sentences up to the limit, and the record stores `shortened_from_words`. Before, it was rejected with "Try again", but decoding is greedy, so Retry produced the same output and failed every time. If even the first sentence is too long, the output is still rejected.

## Numbers (descriptive, n = 10)

| | Success | Median words | Median inference (benchmark) |
|---|---|---|---|
| ab-7 image-only | 10/10 | 39.5 | 3.50 s |
| ab-7 context-aware | 10/10 | 91.5 | 5.77 s |
| ab-8 image-only | 10/10 | 69 | 4.30 s |
| ab-8 context-aware | 10/10 | 71 | 5.31 s |

Repairs: two copy retries (02 CA, 08 CA; 08's retry still repeats caption wording and carries the limitation) and two shortenings (07 IO from 132 words, 08 IO from 159). Without shortening, both would have been failures. That happened in a first ab-8 run before shortening was added.

## Per-sample comparison with ab-7

| Sample | Verdict | Notes |
|---|---|---|
| 01 IO | same | Both accurate (stem, leaves, sky, clouds). |
| 01 CA | mixed | More detail (stem, leaves, clouds), but "vibrant yellow center" is wrong and "healthy and well-maintained" is padding. |
| 02 IO | same/better | Drops the doubtful "small island"; adds the foreground building, with a speculative purpose. |
| 02 CA | **better** | ab-7 copied the article lead word for word. ab-8's retry describes the visible red towers, cables, water, hills and sky. |
| 03 IO | identical | — |
| 03 CA | same | Still adds "renowned theoretical physicist" and an unattributed name. "Seated" is uncertain. |
| 04 IO | same | "State of rotation" persists. |
| 04 CA | better | Names the dark maria and drops the triple repetition. Adds a general-knowledge clause about volcanic origin. |
| 05 IO | mixed | Adds the basket, other parked bicycles, cars and trees (visible), but also the false "leaning against a pole". |
| 05 CA | better | Drops the false "leaning against a pole"; adds the white vehicle in the background. |
| 06 IO | **better** | ab-7 had 8 words. ab-8 has orange wings with black and white spots, a pink flower and a blurred green background. |
| 06 CA | **better** | Same detail. "Appears to be a type of milkweed" is speculative. |
| 07 IO | mixed | Now a success (shortened) where it would have failed. ab-7 quoted real labels (snowpack, evapotranspiration); ab-8 lists general terms (transpiration, infiltration) that are not printed labels. |
| 07 CA | same | Both mostly paraphrase the caption. ab-8 credits USGS and says there is a legend (the Pools/Fluxes box). |
| 08 IO | same | Both open with a textbook definition. Both invent a legend; ab-8 also gets the number/symbol position wrong. |
| 08 CA | better | Drops ab-7's wrong "dash-block marks transition metals" and the invented legend. Correctly notes colour coding, transition metals and noble gases. Still repeats caption wording, which is flagged. |
| 09 IO | **better** | Drops the wrong "Asia on the left", the invented "aN" labels and the invented scale bar. Still invents a legend. |
| 09 CA | mixed | Drops the invented "aN/aO" labels and the projection legend, but adds "3D perspective" and illegible country labels that are not there. |
| 10 IO | identical | Still 11 generic words. |
| 10 CA | slightly better | Drops "Mounts are not shown" and the invented legend and numbers. Still wrong about layout ("Sun in the center, orbiting"). |

Tally (qualitative): better 8, same 7, mixed 5, worse 0. The mixed cases each gain correct detail and add one unsupported claim, or lose real quoted labels (07 IO).

## Extension-path checks

- **OCR at extension resolution.** The API runs OCR on a copy of up to 1600 px built from the original bytes; the pilot thumbnails are 960 px. With the new filter, photo junk drops from 3–12 words per image to 0, apart from `V4` (03) and `ie` (09). The Solar System now passes Mars, Venus, Earth, Mercury, Neptune, Uranus and Ceres; the periodic table adds "Noble gases", "Group" and "Period".
- **Live API, ab-7 vs ab-8.** Same machine; the requests are built like the extension's, with `page_summary` filled from the lead for 02.

| Request | ab-7 | ab-8 |
|---|---|---|
| 06 image-only | 10.5–11.8 s, 8 words | 12.7–13.9 s, 32 words of accurate detail |
| 10 context-aware | 24.4 s | 9.1 s |
| 02 context-aware (lead in `page_summary`) | 26.6 s, verbatim article copy | 14.0 s, visual description |

- **Pre-existing, not changed here:** live requests spend 4.5–6 s on analysis (type classification and OCR), and server-side inference is about 2–3× slower than in the benchmark process for the same output. The benchmark's `total_ms` does not include classification or OCR, so benchmark latencies understate what extension users see.
- In one live ab-8 run, 10 CA invented image credits ("Cassiopeia", "Lars Lindberg Christensen"). Credits are a remaining hallucination risk.

## Still open

- Unsupported additions in longer outputs (05 IO pole, 04 IO rotation, invented legends in 08/09). The next prompt candidate could tell the model to leave out a detail rather than guess, and not to mention a legend unless one is visible.
- 10 IO is still generic. Routing sends it to `chart`; `diagram` may suit it better.
- The caption is not credited when it supplies a name (03).
