# Four-person work division

| Member | Owned modules | Immediate follow-up |
|---|---|---|
| Person 1 | extension/context_extractor.js; backend/data; benchmark/build_dataset.py; manifests | Audit ten caption/nearby associations; add difficult infobox/gallery fixtures and license attribution checks |
| Person 2 | backend/models; scripts/feasibility.py; benchmark/run.py and analyze.py | Reproduce real visual feasibility, resource/latency measurements and paired logs; coordinate independent ratings |
| Person 3 | backend/engine; benchmark/annotation_rubric.md | Audit unsupported identities/claims and unreadable labels; refine prompts only on development data with new versions |
| Person 4 | backend API/settings/schemas; extension UI/worker/options; setup/demo | Complete Chrome + VoiceOver keyboard/status/focus/error/reflow matrix; fix integration defects |

Each member reviews another workstream and independently rates an assigned balanced share of the pilot. Preserve their rating files separately. Shared contracts require coordinated schema, consumer and fixture updates. No hosted credentials or provider keys belong in browser assets.

Next milestone: finish human/context/accessibility audits, lock a ten-to-twenty-case development protocol, then add a second feasible VLM and a held-out grouped dataset. Introduce C and larger statistical comparisons only after these gates are evidenced. Record negative findings rather than tuning on held-out outputs.
