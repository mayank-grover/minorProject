# Five-minute live demonstration

Prepare: activate `.venv`; confirm token/extension ID in `.env` and saved extension options; start the loopback backend with the README command. Wait for `/health` to report model_ready true. Keep the model weights local. Do not run the benchmark concurrently. Live outputs can vary and may be wrong; no fixture or replay path replaces inference.

1. Open a real Chrome Wikipedia article such as Common sunflower. Activate the toolbar extension action. Navigate the labelled image controls with keyboard focus; choose **Go to image 1**, then the native **Describe** button.
2. Observe the loading status. When complete, use **Read description** to focus the result heading. Show the AI label, model identifier, inference latency and limitations. Explain that existing Wikipedia alt/captions remain intact.
3. Choose a second image, including a diagram/map if practical. Repeat, and use **More detail** only if useful. Do not promise exact chart values or complete transcription.
4. Demonstrate **Cancel request** or an unavailable-backend error and **Retry**. Cancellation suppresses the result; compute may continue. **Disable for this page** removes all injected controls.
5. Open artifacts/results/pilot/comparison.html and summary.md. Show genuine A/B outputs from the frozen manifest, complete pair/attempt counts, latency and any failure records. Show review.csv's blank independent rating fields. Explain that this development pilot does not establish a statistically significant gain or blind-user benefit.

For screen-reader verification, perform the checklist with VoiceOver (macOS) or NVDA (Windows), including actual spoken loading/ready/error announcements and heading/region result reading. Record versions and failures before marking it passed. Accessibility-tree exposure alone does not establish correct spoken interaction.

Fallback: disclose model/network failure openly. `/health` and typed errors remain testable, and stored pilot outputs can be inspected as explicitly recorded experiment evidence. Stored outputs do not satisfy the live inference gate.
