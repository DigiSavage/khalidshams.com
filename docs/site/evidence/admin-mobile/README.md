# Admin and mobile verification evidence

Captured from the built site on 2026-10-12. Artwork checks use the real local build. Admin screenshots use the actual application and API handler with isolated moto DynamoDB and signed fixture JWTs; the synthetic inquiry demonstrates inert rendering of submitted markup. These are test fixtures, not production visitors, inquiries or a claim that AWS deployment has completed.

`checks.json`: 518 art checks across phone DPR 1/2/3, tablet and desktop, both themes, manual override, no JavaScript, real decoded currentSrc, no unnecessary desktop-art requests and preserved Atlas interactions.

`admin-checks.json`: 54 browser checks covering the locked shell, responsive owner views, keyboard section activation, persistence, stored XSS, expiry clearing, consent, exclusion and retry behavior. Backend and infrastructure unit tests are reported separately.

`layout-checks.json`: 12 checks verify reserved portrait geometry before download, after decode, and across manual theme changes.

Live evidence after deployment 38302607517: `live-art-checks.json` (518/518), `live-enterprise-checks.json` (231/231), `live-http.json` (route status and exact image bytes), and `live-shells.json` (honest unavailable states before backend provisioning).
