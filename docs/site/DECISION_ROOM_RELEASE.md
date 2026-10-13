# SHAMS Decision Room

## Release state

Prepared on `codex/decision-room` from main `479fd0e`. Deployment is pending AWS owner sign-in and review of the prepared CloudFormation change set. This document does not claim the new service is live.

The workbench supports the $950 Architecture Decision Review: one decision, recorded evidence, findings, alternatives, a recommendation and a reviewed client brief. Production starts with no cases. There is no demo-data import, score, inferred client outcome or generated recommendation. The owner writes and reviews the work.

## Product and privacy boundary

The private admin links to `/admin/decision-room/`. The static shell is public but contains no client records or proprietary methodology. Every case, guidance and export request uses the existing owner session, live owner-group and MFA checks. The route is excluded from sitemap, search and telemetry. Its content security policy permits known build scripts and same-origin application requests.

The eight stages are Mandate, Evidence, Findings, Options, Decision, Handoff, Internal and Review. An assessment records one bounded decision; evidence distinguishes reported claims from documents, observations and tests. Findings reference evidence. Review requires substantive alternatives, a counterargument, a recommendation and accountable actions. An unresolved blocker or merely reported evidence prevents a `proceed` recommendation. These rules are completeness checks, not a compliance certification or an automated guarantee of sound architecture.

The proprietary guidance is a private, versioned S3 object outside this repository and outside `dist/`. The initial pack contains 49 questions across common assessment work, general architecture, cloud, SaaS, data, security, delivery and AI. No answers are prefilled. Each case pins the S3 version, method version and SHA-256. Preparing a later object version does not activate it; CloudFormation's `MethodVersion` parameter selects the version for new cases. Historical cases retain their own pin.

Client exports use explicit field allowlists, including nested records. They include the recorded evidence, alternatives and recommendation. They exclude private questions, answers and internal notes. A deliberate review creates an immutable snapshot. Each download freshly reauthorizes access, reads the chosen snapshot and records a metadata audit event. The downloaded HTML uses escaped text and no external resources; the owner can print it to PDF. Downloaded copies are outside server retention and must be handled by the owner.

The application does not send content to an AI provider, fetch evidence URLs, scan customer infrastructure, execute customer code or contact clients. Use redacted context and references; do not enter credentials, medical records or confidential source documents.

## Storage and access

- A dedicated `DecisionRoom` Lambda handles `/api/admin/assessments` and its child routes. The public contact and telemetry Lambda receives no assessment-table or methodology access.
- Its role can operate only on the new encrypted assessment table, read the existing session table, read the exact methodology object and its versions, read the existing origin secret, and check the existing owner directory. It cannot create sessions or query inquiries or analytics.
- Creation uses a request UUID for safe retries. Saves use revision conditions. Concurrent edits return a conflict and preserve the unsaved editor. Deletion changes the row kind and revision, preventing an in-flight write or review from resurrecting the deleted case.
- Review, mutation and export audits record action, owner, case identifier, revision and time, without case content. They are operational history, not a tamper-proof audit system.
- The owner selects 30, 90, 180 or 365 days at creation. Expiry is fixed; editing or reviewing does not renew it. Expired records are immediately inaccessible through the API. DynamoDB TTL and a bounded scheduled sweep remove storage asynchronously.
- Explicit deletion removes case content and all reviewed snapshots. A content-free identifier tombstone prevents retry resurrection until the original expiry. Metadata audit rows share that expiry. DynamoDB point-in-time recovery can retain earlier data within the configured recovery window; deletion does not instantly erase backups.
- In-memory browser drafts are cleared on sign-out, expiry or authorization failure. The application does not store them in browser storage or URLs. Writes are explicit; closing with unsaved changes prompts the owner.

Request bodies are limited to 24 KB, each evidence/finding/option/action collection to 16 records, and each case to 20 reviewed snapshots. Lists are paginated. The table uses on-demand throughput limits and the function reserved concurrency of two. These are load controls, not a hard AWS spending cap. Logs retain 14 days and application errors omit request bodies.

## Validation and evidence

Tests run against isolated AWS fixtures with real handlers, signed sessions and a real browser. Synthetic records exist only inside those tests and are never packaged into the site or Lambda. Empty-state screenshots are the only case screenshots intended for the public evidence folder.

Final local results: 20 Decision Room backend tests, 28 existing admin/infrastructure tests, 60 Decision Room browser checks and 68 existing admin browser checks passed, totaling 176. The static build passed with 495 public search entries. SAM/CloudFormation lint, JavaScript syntax and whitespace checks passed. Private routes are absent from the sitemap, search index and telemetry page catalog. Desktop 1380px, phone 390px and narrow 320px layouts passed, with light/dark empty states and populated stage checks. Selected empty-state screenshots and machine-readable results are under `evidence/decision-room/`.

```sh
.venv/bin/python build.py
.venv/bin/python -m unittest discover -s tests/decision_room -p 'test_*.py'
.venv/bin/python -m unittest discover -s tests/admin -p 'test_*.py'
.venv/bin/python tests/decision_room/ui_check.py /tmp/decision-room-ui
.venv/bin/python tests/admin/ui_check.py /tmp/decision-room-admin-regression
.venv/bin/cfn-lint infra/site-admin/template.json
node --check static/admin/decision-room.js
git diff --check
```

Backend checks cover empty state, JWT/owner/MFA/CSRF/origin failures, owner partition isolation, object version pins, validation, incomplete drafts, blocker rules, strict exports, conflicts, concurrent deletion, snapshot pagination, retention and sanitized failures. Browser checks cover saved fields, review acknowledgement, safe rendering, private-field exclusion, authorized export, conflicting tabs, revocation after preview, CSP, no analytics and phone layouts.

## Deployment and verification

Use the authorized AWS account `430110755505`, region `us-east-1`, existing stack `shams-site-admin`. The existing CloudFront API behavior already disables caching and does not need reconnecting. Do not extract GitHub deployment credentials or place the private methodology in the repository.

Prepare from the reviewed branch in the authorized environment, with the private pack outside the checkout:

```sh
python infra/site-admin/deploy.py \
  --prepare \
  --owner-email khalidshams@gmail.com \
  --domain-prefix khalidshams-owner-430110755505 \
  --method-file /private/path/decision-room.json \
  --evidence-dir /private/path/release-evidence
```

The preparation command uploads private versioned artifacts and creates a change set. It does not execute it. Review resource additions, IAM scope and any replacements before executing that exact change set. Record the code hash, pinned method hash/version and completed stack status in private release evidence. Never publish artifact credentials, the method contents or session material.

Deploy the API first. Check the new table has no assessment cases, the dedicated role has the intended scope, the deployed method is the approved version, and anonymous requests to case/method/export paths return uncached authorization errors. Merge the static PR only after the backend is ready, then wait for the existing deployment workflow and verify live HTML/assets by content hash.

Use the owner's real sign-in to verify the empty workbench and private guidance. Do not create production test cases. Local integration tests verify writes without adding fictional client data to the live service. Record the limitation explicitly if authenticated live acceptance is not yet available.

For rollback, remove the new navigation/static page through a revert and restore the previous function release or stack template through a reviewed change set. Preserve the assessment table and private method versions. Do not delete retained tables or backups as part of a routine rollback. Restoring a backup requires checking and reapplying expiry/deletion rules before serving records.
