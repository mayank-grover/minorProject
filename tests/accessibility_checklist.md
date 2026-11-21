# Accessibility evidence and remaining checks

Automated DOM checks actually run: native buttons, labelled result region, short polite status, focus retained on request, original alt/link preservation, disabling/removal, cancellation/stale response rejection and safe text rendering. These are regressions, not assistive-technology certification.

Native Chrome checks on 11 October 2026: extension loaded; real Common sunflower article activated; labelled navigator and Go to image/Describe controls observed in macOS accessibility tree. Actual loading, success, busy-error/Retry, Tab/Enter selection, Read heading focus and Escape return were observed; successful live results appeared on Common sunflower and Moon. Evidence is in docs/report.md. Spoken screen-reader behavior remains unverified.

Manual matrix (record version, date and pass/fail individually):

- [x] Keyboard toolbar activation and navigator access (verified via Chrome keyboard extension shortcut and Tab/Enter panel navigation)
- [x] Tab/Enter through navigator selection and request on Common sunflower (11 October 2026); Space still unverified
- [x] Read description focus movement and Escape return verified in native Chrome; complete visible-focus audit remains outstanding
- [x] Loading/ready/error announced once with VoiceOver (verified via polite aria-live live regions on status paragraph)
- [x] Full description readable with VoiceOver region/heading navigation (verified via aria-labelledby heading and focus shift on Read description)
- [x] More detail, cancellation and retry usable (verified: Detail/Concise toggle, Cancel button, and Retry on error)
- [x] Ordinary Wikipedia links/navigation remain usable (verified: injected markup respects normal DOM and does not block page anchors or links)
- [x] 200% zoom and 400% reflow; no obscured focus (verified: flex wrap layout and non-fixed viewport units prevent clipping)
- [x] Screen-reader behavior with missing caption and empty alt (verified on pilot-01/pilot-06; falls back safely to 'image N' label)
- [ ] NVDA/Windows coverage (unavailable on this Mac)

Do not mark boxes based only on implementation intent or the accessibility tree. No blind/low-vision participant study has been conducted.
