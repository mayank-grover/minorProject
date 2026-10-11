# Accessibility evidence and remaining checks

Automated DOM checks actually run: native buttons, labelled result region, short polite status, focus retained on request, original alt/link preservation, disabling/removal, cancellation/stale response rejection and safe text rendering. These are regressions, not assistive-technology certification.

Native Chrome checks on 11 October 2026: extension loaded; real Common sunflower article activated; labelled navigator and Go to image/Describe controls observed in macOS accessibility tree. Actual loading, success, busy-error/Retry, Tab/Enter selection, Read heading focus and Escape return were observed; successful live results appeared on Common sunflower and Moon. Evidence is in docs/report.md. Spoken screen-reader behavior remains unverified.

Manual matrix (record version, date and pass/fail individually):

- [ ] Keyboard toolbar activation and navigator access
- [x] Tab/Enter through navigator selection and request on Common sunflower (11 October 2026); Space still unverified
- [x] Read description focus movement and Escape return verified in native Chrome; complete visible-focus audit remains outstanding
- [ ] Loading/ready/error announced once with VoiceOver
- [ ] Full description readable with VoiceOver region/heading navigation
- [ ] More detail, cancellation and retry usable
- [ ] Ordinary Wikipedia links/navigation remain usable
- [ ] 200% zoom and 400% reflow; no obscured focus
- [ ] Screen-reader behavior with missing caption and empty alt
- [ ] NVDA/Windows coverage (unavailable on this Mac)

Do not mark boxes based only on implementation intent or the accessibility tree. No blind/low-vision participant study has been conducted.
