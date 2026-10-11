# Inline results and explanatory descriptions — 11 October 2026

The extension now places loading, errors, generated prose and result controls directly below the selected image's Describe button. Each image retains its own result. Read description focuses that result's heading; Escape returns to its Describe button. The article-top panel only contains navigation and page controls.

Prompt ab-2 asks for the legible message, relationships and ordered stages of text-heavy graphics, and explicitly prohibits inventing unreadable stages. Same-row infobox labels are associated with the correct image and exclude extension-generated text.

## Exact reported image: live verification

Tested in the installed Chrome extension on `https://en.wikipedia.org/wiki/Common_sunflower`, with the real local SmolVLM2-2.2B-Instruct backend, MPS/float16, prompt ab-2. The reported image is `Status_iucn3.1_LC_WCAG.svg`, a conservation-status graphic. Extracted caption: `Conservation status: Least Concern (IUCN 3.1)`.

Earlier trial prompts confused the sunflower lead text with this graphic or made an unsupported abundance claim. The final conservation-specific prompt excludes unrelated lead text and supplies an [IUCN definition reference](https://portals.iucn.org/library/efiles/documents/rl-2001-001-2nd.pdf). The model still receives the actual image and generates the response.

Final live output, approximately 5.0 seconds inference:

> Least Concern is a conservation status that means the species is not threatened or endangered. It is the lowest risk category on the IUCN 3.1 scale.

The live Chrome accessibility tree and screenshot confirmed the result beneath the graphic, inside the same infobox row. Read description focused its local heading. The backend was restarted with the final source; the installed extension and article had already been reloaded with the extension changes.

## Verification and limits

20 Python tests and 5 extension tests passed. Extension tests cover source-row association without leakage, independently retained inline results, cancellation, text-only rendering and keyboard focus. JavaScript syntax checks passed.

This is a targeted live regression check, not a broad accuracy evaluation. The small local model may still misread dense or small text and invent details despite the prompt. No OCR engine or larger model was added. Historical ab-1 pilot artifacts remain unchanged and do not evaluate ab-2. If another lifecycle image is involved, its exact image has not been tested here.
