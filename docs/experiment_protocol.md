# Development pilot protocol — ab-1

Frozen scope: ten real Wikipedia image occurrences, deliberately selected for category diversity. This is a convenience sample and development pilot; no held-out or formal efficacy claims. Each occurrence's prepared PNG is hashed and reused unchanged in both modes. Source revision/file metadata and licenses are stored in the manifest.

One SmolVLM2-2.2B adapter, greedy decoding, 192 maximum new tokens, concise maximum 120 words, eager attention, image splitting enabled at a 768-pixel longest edge, batch size one. Image only gets pixels and neutral instructions only. Context aware additionally gets title, caption, section and nearby text. Neither mode gets existing alt, image URL, file name or human reference/ratings. Prompt and configuration hashes plus the resolved checkpoint revision accompany each attempt.

Order is A then B for each sample, so timing is subject to warm-up/order effects. No best-of-N selection, hidden repairs or cache reuse. Model loading is excluded from inference time and separately measured by feasibility. Validation failures count as failures and need raw-output inspection. Resource and latency results are conditional on this machine/runtime. Multiple reviewers retain separate ratings; blanks are not zero scores. No scores have been manufactured.

Sampling/extraction and image quality need human audit before a future frozen held-out study. Review outputs against both pixels and source context. Record unsupported material claims explicitly. No participant study, statistical significance or general Wikipedia coverage claim follows from this pilot.
