# Mid-semester milestone evidence

Implementation and measurements recorded on 11 October 2026. The repository began empty. The supplied PRD was read completely and preserved in PRD.md; the user’s sprint request governs the smaller implementation scope.

## Implemented

MV3 Chrome extension, bounded Wikipedia context extraction, local image-byte transport, strict FastAPI contract, real replaceable VLM adapter, versioned image-only/context-aware prompts, output validation, typed errors, single inference lane, loading/cancellation/retry/result controls, paired evaluation runner, frozen source manifest, comparison HTML and blank human-review CSV. Existing image alt text and links are preserved. Four-person ownership and next work are in team.md.

## Hardware and model

Apple M2 MacBook Air, 16 GB unified RAM, arm64 macOS 27.0.1; Python 3.12.14. Actual model: HuggingFaceTB/SmolVLM2-2.2B-Instruct, revision 482adb537c021c86670beed01cd58990d01e72e4, MPS float16, eager attention, greedy decoding. Official model card/license: https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct (Apache-2.0). Qwen3-VL-2B-Instruct was considered from its official card; a second large model was not installed after SmolVLM proved viable.

Prepared RGB images retain composition with a maximum 768-pixel side. Official processor uses image splitting, longest_edge 768, patch size 384. Pilot maximum output is 192 new tokens; feasibility used 128. One model process should run at a time on this machine. Model download occupies approximately 9 GB. Network download required retries; inference itself runs locally without paid credentials. MPS/network access required execution outside this app’s sandbox during setup and live execution.

Final feasibility load took 25.72 seconds. A real bee photograph produced “A bee is on a pink flower. There are other flowers in the background.” in 5.47 seconds; swapped red-square pixels produced “A red square is on a white background.” in 3.64 seconds. This demonstrates actual image-conditioned generation. Historical initial feasibility used a larger default processor setting and is retained separately in artifacts/feasibility-initial.json; it is not used for the final latency comparison.

## Actual preliminary experiment

Ten real Wikipedia images: Common sunflower, Golden Gate Bridge, Albert Einstein, Moon, Bicycle, Monarch butterfly, Water cycle, Periodic table, World map and Solar System. Source article/file revisions, image hashes, authors and license metadata are in ../benchmark/manifests/pilot.jsonl. Frozen prepared PNGs and source HTML are local in artifacts/dataset and ignored by Git. Rebuilding from live Wikipedia may select newer revisions; copy permitted prepared files for exact reproduction.

Twenty genuine generation attempts: image-only 10/10 successful; context-aware 9/10 successful; nine complete successful pairs. Successful inference medians: image-only 3.65 seconds, context-aware 4.78 seconds. The periodic-table context-aware generation exceeded the concise 120-word bound and was rejected. Its failure and total elapsed time (16.07 seconds) are retained. That initial runner did not preserve the rejected raw output or its separate inference time; the logging code now captures these for future validation failures. The original run is unchanged and no silent retry replaced it.

Reviewable results are in ../benchmark/results/pilot/: generations.jsonl, comparison.html, review.csv, summary.md, feasibility.json and api-smoke.json. Original artifacts/runs/pilot.jsonl is preserved. Both conditions used identical image bytes/model/decoding settings. Image-only prompts contain no article context; existing alt text is withheld from both conditions. Fixed A-then-B ordering and a single run mean latency is descriptive, not a controlled performance claim.

Qualitative observations from the actual text: bicycle and butterfly pairs were identical; the context-aware bridge output repeated surrounding article facts instead of prioritizing visual detail; the water-cycle output leaned heavily on its caption; the Einstein output named the person without the requested explicit attribution to the caption. These examples motivate grounding and concision improvements. They are not human quality scores. All ratings remain blank, extraction associations await human audit, and no statistical significance or blind-user benefit is claimed.

## Verification

Python: `python -m pytest -q` — 18 passed in 0.56 seconds; one Starlette TestClient deprecation warning. Node: `node --test tests/extension.test.cjs` — 3 passed, 0 failed in 0.40 seconds. Tests cover missing context, invalid requests, auth/origin, image limits, errors/deadlines, prompt separation, paired logging, caption association, alt/link preservation, safe result rendering, focus and cancellation. Test-only inference fixtures are never used by the production adapter.

Real HTTP smoke: POST /describe returned 200 with a context-aware sunflower description, model/revision identifiers, hashes and 6.00 seconds inference (6.10 seconds total), recorded in api-smoke.json. Backend is bound to 127.0.0.1:8000. Extension was loaded in actual Google Chrome with ID kddogmjgjgaloghnamkhpmpjoeeamhfi; the generated local token was saved with explicit user approval. Native Chrome exposed the labelled navigator and Describe buttons; overlapping requests displayed the expected busy error and Retry control. Live display verified after reloading the latest extension: on Common sunflower, Tab/Tab/Enter activated Go to image 1, then Enter on Describe started genuine inference. Chrome displayed “A sunflower with yellow petals and a brown center is in front of a blue sky.” with 5.2 seconds inference and the actual model identifier. Request focus stayed on the image button; Read description moved focus to the result heading; Escape returned focus to the image trigger. A genuine screenshot was observed through the native computer-use tool. The initial black capture/input inconsistency cleared when the user kept the Mac awake and unlocked. A second real article, Moon, also completed the extension-to-backend workflow: “The moon is shown in this image.” displayed with 4.6 seconds inference. This short output is operational evidence, not evidence of useful lunar detail.

## Remaining work and boundaries

This is an experimental prototype. Short prompts and deterministic output validation do not prevent hallucinations, article copying, unattributed identities or inaccurate diagram text. English Wikipedia canonical article URLs and Wikimedia raster thumbnails are supported; namespace/edit/diff pages are excluded. SVG sources must have a raster thumbnail; animated images use their first frame. Dense charts/maps and small labels need further work. Infobox captions in separate rows can be missed deliberately rather than guessed. Image eligibility is heuristic; some conservation-status graphics remain eligible.

Actual spoken VoiceOver/NVDA announcements, full screen-reader reading, 200%/400% reflow and a blind/low-vision participant review remain outstanding. Accessibility-tree exposure and DOM tests do not certify accessibility. See ../tests/accessibility_checklist.md. No training, second VLM, full C pipeline, database/cache, formal study or production deployment is included.

Next milestone: audit each image/context association and license, have two independent reviewers fill separate sheets with the rubric, verify spoken screen-reader behavior, improve attribution/concision based on failure cases, freeze a new prompt version, and collect a separate evaluation set before adding a second model.
