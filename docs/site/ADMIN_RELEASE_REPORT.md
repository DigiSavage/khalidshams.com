# Admin, inquiries, measurement and mobile release

## Release state

Enterprise Studio is already published at https://khalidshams.com/architect/agent-studio/ through [PR #9](https://github.com/DigiSavage/khalidshams.com/pull/9), merge `7b48126f989fc7f6bd19f968f2c729a9b19731c9`, successful [deployment 38298640673](https://github.com/DigiSavage/khalidshams.com/actions/runs/38298640673). Its live browser acceptance passed 231/231 checks.

This follow-up branch is `codex/site-admin-mobile`. It preserves the original `codex-brief.patch` untracked file (SHA256 `9f2f057406c2ea524bf65a3d4b96cde5d64c011a93e1b4e2d96f9b7927e70bfe`), existing desktop/compact/thumb artwork, all three other studies, interactive scene IDs and progress storage. Workflows and LinkedIn publisher metadata were not modified.

The repository implementation is complete enough for deployment and integration testing. **The admin application is not yet declared operational:** a signed-in Safari session was inspected, but its AWS account did not contain the site's CloudFront distribution. No resources were created in that other account. The exact remaining infrastructure action is to use an authorized session in the account owning `E14OT21V7ATYP1`, run the reviewed deployment package, then let the owner complete Cognito password setup and MFA. Live authorization, persistence, logging configuration and test-data exclusion must then be verified.

The mobile improvements and public shells are published through [PR #10](https://github.com/DigiSavage/khalidshams.com/pull/10), merge `6eca9154df470a7e097bd6005f3a41f1ba017696`, successful [deployment 38302607517](https://github.com/DigiSavage/khalidshams.com/actions/runs/38302607517) at 2026-10-12 20:12 UTC. Public shells remain honest when the API is unavailable: no fake dashboard data, no telemetry collection, no false contact success.

Live release acceptance: 518/518 art checks and 231/231 Enterprise Studio checks. Every one of the ten mobile WebPs matched the repository bytes by SHA256. `/login`, `/login/`, `/admin/` and `/contact/` return 200; login/admin have noindex. `/api/config` returns 404 because the new API has not been provisioned. Browser checks confirm the private dashboard stays locked and contact submission stays disabled with working direct-contact alternatives. This is a verified static release, not a claim of operational backend completion.

A final source safeguard bounds query response data to 1.5 MB and total inquiry notes to 20,000 characters, with explicit partial/error states. The Linux ARM64 Python 3.12 dependency package also built successfully. Backend live acceptance remains blocked solely on the correct provisioning account and subsequent owner authentication setup.

## Implemented behavior

- Private `/login/` and `/admin/` shells, noindex and excluded from sitemap/search. Cognito code + PKCE/state/nonce, required MFA, live owner authorization on every private request, short opaque HttpOnly sessions, mutation CSRF, no-store API responses and zero-TTL CloudFront API routing.
- Branded overview, page details, journeys, inquiry inbox with notes/history, health and settings; empty/partial states, date ranges in Phoenix, explicit measurement denominators, filtered separate exports and deliberate deletion controls.
- `/contact/` stores validated inquiries before acknowledging success; duplicate protection, challenge/honeypot/rate limits, inert text rendering and email reply drafts. Existing email and LinkedIn contact options remain.
- Optional consented telemetry with bounded visible activity timing, hidden/idle pauses, random first-party IDs, retry deduplication, owner/GPC/local/test exclusions, retention and privacy disclosures.
- Five authored portrait light/dark pairs at `static/art/<scene>/mobile-<theme>.webp`, each 1024x1536. `<picture>` separates composition from desktop width selection; manual themes and no-JavaScript reading work. Exporting the old source series preserves the authored mobile variants.
- Isolated AWS serverless infrastructure and deployment script, private artifact storage, bounded tables/queries, maintenance sweep, recovery/rollback and operating-cost documentation. Existing GitHub static deploy credentials are neither extracted nor broadened.

## Validation on the integrated local build

| Gate | Result |
| --- | --- |
| Build | Passed; 490 search entries |
| Atlas + Enterprise Node suites | 28 passed |
| Existing registry/structure/art/Enterprise Python suites | 43 passed |
| Enterprise browser matrix | 231/231 |
| Atlas browser matrix | 95/95 |
| Learn browser matrix | 186/186 |
| Menu navigation | 103/103 |
| Delivery playbook checks | 96/96 |
| Auth, API persistence, metrics, retention, infrastructure unit tests | 22 passed |
| Engagement timing and referrer Node tests | 4 passed |
| Admin/contact/consent browser integration | 54/54 |
| Extended mobile art matrix | 518/518 |
| Reserved image geometry and manual-theme stability | 12/12 |
| CloudFormation/SAM lint | Passed |

Browser checks use Playwright 1.63.0 Chromium. The existing `tests/site/run_cached.py` supplies cached, unmodified Google Fonts responses; application HTML, scripts, artwork and API assertions are real. Admin integration runs the production handler with isolated in-memory AWS fixtures, not a mocked UI. No fixture route or record is shipped to `dist` or Lambda. Test deliberately induced storage failures produce a generic failure-category log, and do not report success.

Checks caught and corrected a DynamoDB reserved-word expression, Decimal handling after retention settings were persisted, a missing Home measurement-choice entry, and a retry-test timer setup issue. Visual review corrected the admin heading font and unavailable-value wrapping. An initial judgment illustration with misleading sliders was replaced by blank comparison records before export.

Commands and evidence are in `tests/admin/`, `tests/analytics/`, `tests/site/art_check.py` and `docs/site/evidence/admin-mobile/`. Full local screenshots remain under `/tmp/art-ui` and `/tmp/admin-ui`; selected evidence is committed. New dependencies for optional backend tests are in `tests/admin/requirements.txt`; the static build still uses the existing requirements.

## Mobile acceptance

360, 390 and 430px phones at DPR 1, 2 and 3 selected the mobile composition in both themes without desktop/compact/thumb network requests. Tablet 768px and desktop 1440/1920px retained the original wider compositions. Manual theme changes and no-JavaScript phone rendering passed. All eight studies still decode. The original Atlas scene and its step controls remain available alongside the illustration. The HTML/SVG explanations remain the source of labels and technical relationships.

## Pending live backend evidence

Correct-account resource inspection, stack creation, cache/header checks, Cognito owner bootstrap/MFA, unauthorized and non-owner live denial, marked inquiry persistence visible only in the owner inbox, controlled test-event exclusion, existing infrastructure log inventory and retention, logout/expiry and backend rollback verification remain pending until the correct AWS session is available. Fixture passes do not replace those checks.
