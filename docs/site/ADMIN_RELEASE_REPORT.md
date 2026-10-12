## Cognito setup response correction, 12 October 2026

The live setup-key request failed with a sanitized `KeyError` in the enrollment handler. Cognito's access-token-authorized `AssociateSoftwareToken` response can contain only `SecretCode`; the implementation incorrectly required a challenge `Session`. Association now records only that setup started, and verification uses the same server-held access token. Neither the secret nor the submitted code is stored. Existing owner, MFA, CSRF, expiry and attempt-limit checks still apply.

Regression fixtures now use the documented response without `Session`, and assert that verification uses `AccessToken`. The corrected fixture reproduced the production failure before the implementation change. Verification before association and incorrect codes remain denied. The backend unit suite passes 26 tests, the integrated browser suite passes 65 checks at 390 and 1380 pixels, and the site build passes with 490 search entries. Deployment results are recorded in the correction PR. Real owner enrollment remains pending the owner's private setup and code entry.

Reference: [AWS AssociateSoftwareToken](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AssociateSoftwareToken.html) and [VerifySoftwareToken](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_VerifySoftwareToken.html).

## Owner enrollment correction, 12 October 2026

Live attempts returned from Cognito to the site callback, but the directory still reported no enabled software MFA factor. The previous implementation discarded the valid first-factor login and displayed a generic expired-session error. The OAuth client also lacked the reserved self-service scope used by Cognito authenticator enrollment.

The correction introduces a ten-minute enrollment-only HttpOnly cookie following validated PKCE/state/nonce, matching token subjects and live owner-group checks. It grants no dashboard, inquiry or analytics access. The owner explicitly requests a setup key and verifies a six-digit code. The server verifies the factor with Cognito, enables its preference, rechecks live owner/MFA state, consumes the setup session, then issues the normal private session. Setup keys and codes are not logged or persisted by the application. CSRF, same-origin validation, source and session attempt limits, and private/no-store responses apply. An already enrolled owner cannot use this flow to rotate their authenticator.

The client requests `aws.cognito.signin.user.admin` for self-service MFA operations on the signed-in Cognito account. This does not grant AWS account administration or alter the Lambda IAM role. Callback validation failures return to a usable sign-in page instead of raw expired-session JSON. The UI clearly distinguishes the setup key, rotating code and sign-in session.

Validation and post-deployment results are recorded with the correction PR. Live owner acceptance is still required; fixture success is not a claim that the owner's real factor is enrolled.

# Admin, inquiries, measurement and mobile release

## Release state

Enterprise Studio is already published at https://khalidshams.com/architect/agent-studio/ through [PR #9](https://github.com/DigiSavage/khalidshams.com/pull/9), merge `7b48126f989fc7f6bd19f968f2c729a9b19731c9`, successful [deployment 38298640673](https://github.com/DigiSavage/khalidshams.com/actions/runs/38298640673). Its live browser acceptance passed 231/231 checks.

This follow-up branch is `codex/site-admin-mobile`. It preserves the original `codex-brief.patch` untracked file (SHA256 `9f2f057406c2ea524bf65a3d4b96cde5d64c011a93e1b4e2d96f9b7927e70bfe`), existing desktop/compact/thumb artwork, all three other studies, interactive scene IDs and progress storage. Workflows and LinkedIn publisher metadata were not modified.

The private service is now deployed in the verified site account `430110755505`. CloudFormation stack `shams-site-admin` reached `CREATE_COMPLETE`; CloudFront `E14OT21V7ATYP1` reached `Deployed` with an uncached `/api/*` behavior. The existing S3 default behavior and rewrite function remain unchanged. The owner account was invited at `khalidshams@gmail.com`; password change and authenticator enrollment are the owner's remaining manual step. Authenticated dashboard, owner inbox edits, logout and live revocation acceptance remain pending that setup. Do not treat signed-out checks as proof of those owner flows.

The mobile improvements and public shells were published through [PR #10](https://github.com/DigiSavage/khalidshams.com/pull/10), merge `6eca9154df470a7e097bd6005f3a41f1ba017696`, successful [deployment 38302607517](https://github.com/DigiSavage/khalidshams.com/actions/runs/38302607517). Live release acceptance passed 518/518 art checks and 231/231 Enterprise Studio checks. Every mobile WebP matched the repository bytes by SHA256. The follow-up safeguards were published through PR #11 and deployment 38303351573.

Backend activation acceptance passed 32 live checks: config availability; JSON, private/no-store and uncached denial on six private routes; marked inquiry persistence and duplicate retry; marked event acceptance and deduplication. Direct DynamoDB inspection confirmed the marked inquiry and exactly one marked event, with zero production pageviews/visitors. A phone and desktop browser matrix confirmed ready contact/sign-in and locked signed-out admin, with no overflow or page errors. Evidence is under `evidence/admin-mobile/live-api.json` and `live-backend-ui/`.

A live negative test exposed the existing CDN's global 403-to-S3-404 mapping on cross-origin API requests. Request-origin validation now returns JSON 400 with private/no-store headers, leaving the public S3 error mapping intact. Unit coverage verifies this denial contract; post-update live verification is recorded separately.

The query response limit remains 1.5 MB and total inquiry notes remain bounded to 20,000 characters. Existing GitHub deployment credentials were not extracted or broadened. No resources were created in the earlier incorrect Safari account.

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

## Logging and pending owner acceptance

Verified in the actual account: CloudFront legacy/standard logging off; no matching CloudWatch delivery source; no real-time logging on the existing default behavior; S3 server-access logging off; no CloudTrail trails returned in the inspected account/region. Lambda diagnostic retention is 14 days. API execution logs and body tracing are disabled by the deployed template. These checks do not assert that all AWS operational/security metadata is absent.

Owner password/MFA setup, authenticated empty dashboard, marked inquiry editing through the inbox, logout/expiry and live disabled/de-grouped owner denial remain pending. Local fixture checks cover those contracts but do not replace live owner acceptance. The marked records remain labelled as test data and excluded from production aggregates.
