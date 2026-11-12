# ab-7 diagnostic on the frozen ab-1 pilot

**Status: diagnostic only.** First-pass failure tags by one person (with model assistance) after inspecting the frozen pixels. These are not reviewer scores, not rates, and not evidence that ab-7 is better or worse than ab-1. The two reviewer sheets in this folder are blank and must be completed independently.

## What was run

| | ab-1 (historical, `../pilot/`) | ab-7 (this folder) |
|---|---|---|
| Date | 2026-10-11 | 2026-11-13 |
| Hardware | Apple M2, 16 GB | Apple M5, 16 GB |
| Runtime | Python 3.12, torch 2.14.1 (not recorded per run) | Python 3.15.0, torch 2.15.0, transformers 4.57.1, Pillow 12.3.0 (in each record's `runtime`) |
| Model | SmolVLM2-2.2B-Instruct @ `482adb5…`, MPS fp16, greedy, 192 max tokens | same |
| Pipeline additions | — | Tesseract OCR (5.5.4) + image-type routing (`types-v1`), recorded in `configuration` |
| Prompt hash (first record) | — | `359dd690018a…`; config hash `a975cb40dced…` |
| Inputs | 10 frozen prepared PNGs + 5-field context | identical PNGs (all 10 hashes verified) + identical 5-field context |

- pilot-10's Commons file was re-uploaded after the pilot. Its pixels were recovered from the archived version whose `file_sha1` matches the manifest (`benchmark/fetch_manifest_images.py`).
- The frozen context has only `article_title`, `caption`, `section_heading`, `nearby_text` and `existing_alt`. The ab-6 article-overview and biography fields are therefore empty here, so this run does **not** exercise them.
- Hardware and runtime differ from ab-1, so latency differences are not attributable to the prompt.

## Headline numbers (descriptive, n = 10)

| | Success | Median words | Median inference |
|---|---|---|---|
| ab-1 image-only | 10/10 | 9 | 3.65 s (M2) |
| ab-1 context-aware | 9/10 | 16 | 4.78 s (M2) |
| ab-7 image-only | 10/10 | 39.5 | 3.50 s (M5) |
| ab-7 context-aware | 10/10 | 91.5 | 5.77 s (M5) |

ab-7 outputs are much longer. Length is not quality: several added sentences are unsupported (see below).

## Per-sample tags (tags from `docs/output_failure_taxonomy.md`)

IO = image-only, CA = context-aware. "Verify" means a reviewer must confirm against the image.

| Sample | Routed type | ab-7 vs ab-1, observed | Tags (ab-7) |
|---|---|---|---|
| 01 Sunflower | photo | IO now adds stem, large leaves, blue sky with clouds (all visible). CA is shorter and drops the stem/leaves. | CA `SCENE_OMISSION` |
| 02 Golden Gate | photo | IO now describes red paint, two towers, water, hills (visible); misses foreground brick fort and the left-side arch. "small island" is doubtful. **CA is a verbatim copy of the article lead, identical to ab-1.** | IO `UNSUPPORTED_VISUAL` (verify "island"); CA `CONTEXT_COPY`, `OVERLONG` |
| 03 Einstein | photo | IO adds tweed jacket (visible). CA names him and adds "a renowned physicist" (general knowledge, not pixels), without attributing the name to the caption. | CA `SOURCE_ATTRIBUTION` |
| 04 Moon | photo | Both now give centered, craters, black background. IO: "appears to be in a state of rotation" is not visible. CA repeats "craters" three times; ignores caption (north pole at top). Neither mentions dark maria vs bright highlands or the rayed crater. | IO `UNSUPPORTED_VISUAL`; both `SCENE_OMISSION`; CA `OVERLONG`, `CONTEXT_UNDERUSE` |
| 05 Bicycle | photo | IO unchanged (11 words). CA adds front basket and rear rack (correct) but says "leaning against a pole" — it stands on its kickstand. Ignores caption (Flying Pigeon; name is printed on the frame). | IO `GENERIC`; CA `UNSUPPORTED_VISUAL`, `CONTEXT_UNDERUSE` |
| 06 Monarch | photo | **Unchanged from ab-1 in both modes** (8 words). No wing colour/pattern, spread wings, pink flower or blurred green background. The detail rule had no effect. | both `GENERIC`, `SCENE_OMISSION` |
| 07 Water cycle | process | No longer called a "map". IO quotes real labels (snowpack, evapotranspiration, groundwater recharge) but also "condensation", which is not a label; "atmosphere/ocean circulation" is a merged misquote. CA cites "Pools and Fluxes" and the USGS logo (both visible), rest paraphrases caption. | IO `TEXT_RELATION_ERROR` (verify); CA partial `CONTEXT_COPY` (verify) |
| 08 Periodic table | chart (IO) / diagram (CA) | **ab-1 CA failure is now a success.** IO opens with a textbook definition (atomic numbers, electron configurations); 18 groups / 7 periods is correct. Both claim a "legend explaining symbols" — none exists. CA correctly names four blocks but says the dashed line indicates transition metals (it marks metals/nonmetals). Neither mentions the colour coding. | IO general-knowledge padding, `UNSUPPORTED_VISUAL`; CA `UNSUPPORTED_VISUAL`, `TEXT_RELATION_ERROR`; both `SCENE_OMISSION`; inconsistent routing |
| 09 World map | map | IO: "Asia on the left and Africa on the right" is wrong (Americas left); quotes labels "aN", "a" and a scale bar — none exist. CA gets orientation right but invents a projection legend and the same "aN"/"aO" labels. The "aN"/"ao" strings are Tesseract noise passed in the prompt's OCR block. Neither uses the caption's Equal Earth projection or describes the oval outline. | IO `UNSUPPORTED_VISUAL`, `TEXT_RELATION_ERROR`; CA `UNSUPPORTED_VISUAL`, `TEXT_RELATION_ERROR`, `CONTEXT_UNDERUSE` |
| 10 Solar System | chart | **IO regressed to 11 words** ("diagram … with planets and their names"). CA reads the title, horizontal layout and labels, but says "Sun at the top" (it is the right edge), invents size numbers and a legend, and misreads "Moons that are not shown" as "Mounts are not shown". | IO `GENERIC`; CA `UNSUPPORTED_VISUAL`, `TEXT_RELATION_ERROR` |

## Cross-case findings

1. **The detail rule helps some photos (01, 02, 03, 04 IO) but not reliably.** 05 IO and 06 (both modes) are unchanged; 10 IO got shorter.
2. **Longer outputs bring new unsupported claims.** 04 ("rotation"), 05 ("leaning against a pole"), 08 ("legend"), 09 (orientation, scale bar), 10 ("Sun at the top", numbers). This is the main new risk.
3. **OCR noise is turned into fake labels.** OCR runs on every image, including photos, and passes words with ≥ 0.5 confidence into the prompt. On photos and the map these are junk fragments (`Lyi,`, `EER`, `CNS`, `aN`, `ao`). In 09 the model quoted them as map labels.
4. **Verbatim context copying is not prevented by instructions alone.** 02 CA reproduces the article lead word for word, exactly as in ab-1. Nothing after generation checks for overlap with the supplied context.
5. **Context is under-used where the caption would help.** 04 (orientation), 05 (Flying Pigeon), 09 (Equal Earth projection) ignore informative captions.
6. **Routing is inconsistent.** 08 is routed `chart` for IO and `diagram` for CA; 10 is routed `chart`.
7. **The ab-1 validation failure (08 CA) did not recur.**

## Candidate fixes (not applied, for team decision)

These come from the development pilot, so they can be tried here. Any claim must come from a fresh, frozen set.

- **OCR gating:** skip OCR text for `photo`; raise the word-confidence floor; drop tokens shorter than 3 letters or with no vowel.
- **Copy guard:** reject or flag context-aware outputs with long verbatim overlap with `nearby_text`/`caption` (e.g. any shared run of 12+ words), as a recorded failure.
- **Grounding rule for added detail:** the detail rule should say "omit a detail rather than guess"; also look at why 06 and 10 IO ignore it.
- **Caption use:** when a caption names the subject or projection, ask for it to be stated with attribution ("captioned as …").

## Files

- `generations.jsonl`: all 20 raw ab-7 records, including prompt, OCR lines, routing and runtime.
- `review.csv`, `review_reviewer_1.csv`, `review_reviewer_2.csv`: blank sheets for independent review (rubric: `benchmark/annotation_rubric.md`).
- `comparison.html`, `summary.md`: generated by `benchmark/analyze.py`.
