# Article context and image emphasis

Prompt ab-6 applies to any supported English Wikipedia article. It does not contain artist-specific names, features or example descriptions.

The extension collects a compact overview when an image is selected: the opening paragraph, short extracts from up to five major sections, up to twelve headings (major sections first), and up to eight image captions. The selected image supplies its own caption, local section, nearby prose, zero-based position and lead/contextual role. This is a bounded snapshot rather than the entire article text. Extension-generated results are removed from the extracted text.

A biography infobox establishes the article's subject and supplies explicit aliases from the opening bold names and labelled infobox name rows. Country infoboxes are not treated as biographies. The primary biography infobox image, or the first eligible article image before the sections, receives appearance emphasis. Later photos receive action/setting emphasis. A later image whose caption or section explicitly indicates a portrait, close-up, face, tattoos or hairstyle receives appearance emphasis instead. Non-photo images keep their chart/map/flag/process guidance.

Appearance instructions prioritize visible hair, face/expression, skin tone, clothing, accessories and discernible tattoos before briefly describing pose/background. Activity instructions prioritize visible action, posture, interaction and scene, with appearance details that matter in that image. These are general editorial rules; they cannot perfectly distinguish every portrait from every event photo.

Full explicit alias matches and captions beginning with a source-attested surname can resolve the article subject's name. A caption naming someone else does not inherit the biography identity simply because it appears on that page. An uncaptioned main biography infobox image can use its explicit infobox association. For monuments, flags and other subjects, an associated caption link or image-specific infobox label supplies identity. A title or filename alone is insufficient.

The model is instructed to integrate that name into its first sentence. If it still starts with a generic subject, the engine substitutes the source-associated name; otherwise it adds a short identifying sentence. It does not prepend the entire caption. Read aloud uses the resulting prose. Raw model output and the resolved subject/focus remain separately available in generation records.

Ethnicity must not be inferred from appearance. The prompt allows an ethnic identity only when explicitly stated by source text; visible skin tone can be described without assigning ethnicity. Obscured facial details, unreadable tattoos, emotions and actions suggested only by the article must not be invented.

Image-only mode excludes all article-derived context and identity. Existing alt text remains unchanged and is excluded from model prompts in both modes. All supplied article and OCR text is treated as untrusted content, not instructions. The optional API fields and aggregate limits are specified in [contracts.md](contracts.md).

After updating, stop the old backend with Control+C, start `python3 run.py`, reload the unpacked extension in `chrome://extensions`, and reload the Wikipedia article. Generate fresh descriptions or use Refresh description; existing rendered descriptions do not update automatically.

Validation uses fictional biography fixtures to check alias resolution, different-person isolation, lead/later/close-up emphasis, source-free baseline behavior and context hashes, plus DOM tests for real Wikipedia-shaped biography and country markup. Real model tests use downloaded public Wikipedia images; results and remaining factual errors are recorded in [decisions.md](decisions.md).
