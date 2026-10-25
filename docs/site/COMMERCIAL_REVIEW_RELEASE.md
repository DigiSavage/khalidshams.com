> Superseded on 2026-10-25 by COMMUNITY_RESOURCES_RELEASE.md. The paid offer described below is historical and is no longer offered.

# Architecture Decision Review

The owner approved a $950 USD, fixed-scope Architecture Decision Review and asked for a premium presentation grounded in his existing principal architecture work. The public library remains free. Stripe connection is explicitly deferred by the owner.

The home page now offers one decision review with a 90-minute working session, a written decision brief and a 30-minute handoff. The brief is due within three business days of the working session and receipt of agreed inputs. An illustrative database placement decision demonstrates the output without inventing a customer result or savings figure. The offer includes scope limits, a free fit check and confirmation of availability before payment. Production credentials, implementation, incident response and security certification are outside the review.

The home hero, Work menus and shared footer expose the offer. A known `offer=architecture-review` value opens editable inquiry context. Unknown query values are ignored; query text never becomes markup. The normal contact form remains available. The request uses existing fields and source `/`, so the deployed backend's public-page allowlist remains valid. Existing MFA owner access, same-origin validation, challenge, rate limits, duplicate protection and private inquiry storage are unchanged. No payment details are collected and the site does not claim a charge or booking occurred.

## Validation

- Site build passes with 493 search entries, including the offer's heading anchors.
- 26 backend unit tests pass.
- 68 real-handler browser integration checks pass, including editable offer context and persisted `/` source.
- 52 focused commercial checks pass at 390 and 1380 pixels in light and dark modes. These intercept API requests and validate the payload against the existing backend contract; they are not live payment tests.
- 103 menu regression checks pass.
- Screenshots inspected for mobile/desktop layout, both themes, contact and the keyboard-operable sample brief. No horizontal overflow or script errors found in the checked flows.

Evidence lives in `evidence/commercial-review/`. Deployment and live public verification are recorded in the pull request. Workflows, LinkedIn metadata and the owner's pre-existing `codex-brief.patch` were not modified. No money was spent or outbound prospect messages sent.

## Operating boundary

This release accepts inquiries, not payments. The owner checks the private inbox; no new email notification or automated reply is configured. Before a client pays, confirm fit, scope, timing, business/invoice identity, cancellation terms and the actual payment method. Stripe hosted payment/invoice setup remains future work at the owner's request. No guarantee of client acquisition, savings or revenue is made.
