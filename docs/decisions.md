# Decisions — 11 October 2026

- Empty repository: implemented fresh modules; preserved the supplied PRD unchanged.
- User's sprint request supersedes PRD's full semester matrix/approval choreography. One VLM, A/B and ten-case pilot are the milestone; C, second model, cache and formal studies are deferred.
- Apple M2, 16 GB unified RAM: tested official SmolVLM2 using Transformers/MPS, float16, eager attention. No CUDA-only FlashAttention dependency. MPS access requires running outside the restrictive execution sandbox here; normal local terminal commands are documented.
- Current API thumbnail references use thumb.wikimedia.org with tracking query parameters. Allowed that exact Wikimedia host alongside upload.wikimedia.org after verifying https://phabricator.wikimedia.org/T439443. No wildcard host or unrestricted redirect proxy.
- MV3 worker fetches only selected public image bytes with credentials omitted; backend also supports validated URL-only input. No provider fetches arbitrary URLs.
- Authenticated loopback service, exact configured extension origin, one active inference and no queue. 120-second provisional deadline differs from PRD's 60-second target; measured suitability remains to be assessed.
- No production mocks/replays. A missing model returns a degraded health status and 503.
- Human scores remain blank; no quality or accessibility benefit result is implied by a successful inference.


## Inline descriptions and text-heavy images — 11 October 2026

Each eligible image now owns its loading/error/result surface directly below its Describe button. Results persist independently; the top panel is a navigator. Prompt ab-2 requests the actual legible message/stages/relationships rather than only the image title. Infobox same-row text and preceding header are retained as associated caption information when no explicit caption exists. Original ab-1 pilot records are unchanged; they are historical results, not ab-2 evaluation.

For conservation-status infobox graphics, ab-2 uses the associated status label without unrelated article lead prose. A Least Concern definition reference from [IUCN Categories and Criteria v3.1, second edition](https://portals.iucn.org/library/efiles/documents/rl-2001-001-2nd.pdf) grounds the category explanation and forbids unsupported population claims. This is model prompt grounding, not a replacement response or a replay. The general text-diagram prompt cannot guarantee legible labels or correct reasoning from this small VLM.

## Visible appearance — prompt ab-3

The user's sunflower macro example exposed terse subject naming under ab-2. Prompt ab-3 now asks both modes to describe the photograph's framing, visible colors, shapes, textures, patterns, spatial arrangement and background. Context-aware descriptions explicitly prioritize 3–5 concrete visual sentences and avoid substituting biology/history facts. Diagram prompts retain meaning and add visible layout/highlighting. No image-specific photograph description is supplied to the model.

Live Chrome regression: `Sunflower_macro_wide.jpg`, caption `Detail of disk florets`, image 6 on Common sunflower. The prior displayed result was `A close-up of a sunflower's center.` The real ab-3 inference (11.2 seconds) returned:

> A close-up image of a sunflower's center, showcasing the yellow and brown disk florets. The florets are densely packed and arranged in a spiral pattern, with the yellow ones at the center and the brown ones radiating outward. The image is taken from a top-down perspective, allowing for a clear view of the florets' intricate structure.

This verifies a fuller appearance description and inline display for the reported photograph, not universal accuracy. Perspective and color-location claims still need human judgment. 21 Python tests and 5 extension tests passed. The backend was restarted with ab-3. Existing descriptions require Refresh; the historical ab-1 pilot and ab-2 fix records remain unchanged. The attempted manual More detail activation did not start a new request because native Chrome input stopped responding; its ab-3 output has not been verified live.

## Read aloud — 11 October 2026

Each completed inline result has a Read aloud toggle and a playback-only Pause/Resume button. Browser speech synthesis reads only generated prose, at rate 0.95 with ordinary punctuation. Installed English voices are preferred; enhanced/premium/natural voice names receive priority, then device default. If no local English voice is listed, Chrome uses its default English speech voice. Voice quality and offline capability depend on installed/browser voices. No new provider or API credential was added. API reference: [SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), [localService](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService).

One extension narration runs at a time. Starting another result, refreshing the spoken result, removing its image, disabling the extension or exiting the page stops its audio. Late speech callbacks cannot reset a newer session; a paused synthesizer is resumed before a new reading. Speech errors retain the description and show an accessible error. Playback never starts automatically. The existing Read description action continues to focus text for screen-reader navigation.

Eight extension tests pass, including speech text/voice selection, pause/resume/stop/end, switching images while paused, stale callbacks, refresh/disable cleanup, errors and page exit. Syntax checks pass. The installed extension and Wikipedia were reloaded, a real sunflower macro description was generated, and live Chrome showed Read aloud → Stop reading/Pause → Resume → Read aloud through activation, pause, resume and stop. These UI transitions verify real browser activation; subjective voice naturalness and an exhaustive VoiceOver interaction review have not been measured.
