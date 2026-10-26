# Video Studio · 26 October 2026

## Purpose and research decision

The owner needs a place to turn consequential business questions into useful five-minute videos: evidence, words, screen actions, preparation, rehearsal and reusable artifacts in one record. The first audience is anyone deciding how AI should fit real work, with enough implementation detail for builders. It is not limited to beginner lessons or healthcare.

Research priorities are editorial judgments about business consequence and teachability, not measured consulting prices or guaranteed returns:

1. Buy, build, or improve the current process.
2. Source authority and employee access.
3. Workflow integration and the exact human decision.
4. Cost per successful task, including rework and review.
5. Modernize, retain, or connect an existing capability.

`services/site-admin/video_research.json` retains original-source links, research dates, populations and limits from McKinsey, Flexera, Salesforce/MuleSoft, Microsoft and Ensono. Vendor-sponsored and self-reported findings are identified. No survey is presented as evidence of Khalid's results or a price customers will pay.

## What works

- `/admin/video-studio/`, reached from control room section 08. Research desk, saved episode library and a responsive editor use the existing site typography and themes.
- Three authored shooting plans, each with six beats totaling 300 planned seconds: build/buy/process, exact approval boundaries, and the first Foundry checkpoint. Timing includes demonstrations and pauses and still requires rehearsal.
- Each beat separates draft spoken words, screen clicks, visuals, Khalid's actions, Codex's preparation and what to preserve. Codex preparation is a plan; no background agent is implied.
- Explicitly create an episode from a plan or from a blank decision. Reading the catalog creates no production record. No fictional clients, completed recordings, measured results or analytics are seeded.
- Revision-checked private saves; meaningful conflict handling; add, remove and reorder beats; editable sources and preparation checks; readiness resets after changes.
- Rehearsal dialog with readable script, step cues, next/previous navigation and an elapsed timer. Nothing is recorded or published.
- Separately download a shooting pack, draft script and an actual recorded transcript when one has been supplied. A draft script is never labeled a recorded transcript. Downloads require fresh owner authorization and the current saved revision.
- The actual screen paths for the first two plans use the existing public Enterprise Agent Studio, explicitly identified as a deterministic teaching simulation. The Foundry plan remains a documented storyboard until an approved Azure sandbox and current portal clicks are rehearsed.

## Private runtime

The existing Decision Room Lambda dispatches `/api/admin/assessments/videos` only after the existing origin, live owner/MFA/session and mutation CSRF checks. No infrastructure, IAM, workflow, authentication scope, model integration or credential change is required.

Video records use an independent `video#<uuid>` sort-key prefix in the existing owner-partitioned assessment table. They are not assessment cases and do not enter analytics. Creates use a client UUID and payload fingerprint for retry safety; changes use conditional revisions; deletion writes a tombstone. Reads deny expired records immediately. Retention is 365 days from creation, with no extension on edits. The existing sweep and DynamoDB expiry remove expired material; physical removal and recovery backups can lag.

Request bodies remain limited to 24 KB. Collection, field, URL and duration limits are enforced server-side. Records use inert text in the browser. Owner content is not placed in persistent browser storage, URLs, public HTML, search or sitemap. The page has noindex, a restrictive CSP and no-referrer policy. Session expiry, sign-out, revocation and a changed login clear private state; a hidden tab is masked until authorization is checked again.

The authored catalog and source code are committed in this public repository; they are not proprietary secrets. The public build contains only the generic UI shell. Owner-created drafts and transcripts exist only in the private runtime and deliberate device downloads.

## Validation

- 18 new backend tests: real signed-session fixtures and isolated DynamoDB, including all three actual catalog templates through create, save, reload, ready and delete.
- 48 existing admin/infrastructure/Decision Room backend tests passed.
- 14 Enterprise engine and analytics timing tests passed.
- 68 existing admin browser checks passed, including sign-in, enrollment, inbox, consent and layout.
- A separate isolated-build test verifies no fixture record, research catalog, script or catalog file enters generated public artifacts; private routes remain absent from search, sitemap and the public page allowlist.
- Full static build passes with 558 search entries. JavaScript syntax and whitespace checks pass.
- 98 Video Studio browser checks passed across desktop/phone and both themes: saves, reload, conflicts, readiness, all exports, transcript/source markup, revocation and changed-session clearing.
- 16 shooting-sequence checks passed for the first two authored demonstrations at 390 and 1380 pixels, including the source denial, exact approval boundary and exported design record. No Foundry cloud run is claimed.
- Selected screenshots and machine-readable results: `docs/site/evidence/video-studio/`.

Browser fixtures are confined to tests and never packaged into the service or static build. Desktop and phone screenshots are verified in both themes; the existing site shell and real API handlers are exercised.

Commands:

```bash
python build.py
python -m unittest tests/video_studio/test_backend.py
python -m unittest tests/admin/test_service.py tests/admin/test_infrastructure.py tests/decision_room/test_backend.py
node --test tests/enterprise/*.test.mjs tests/analytics/*.test.cjs
node --check static/admin/video-studio.js
python tests/video_studio/ui_check.py /tmp/video-studio-ui
python tests/admin/ui_check.py /tmp/video-admin-regression
python -m http.server 8878 --bind 127.0.0.1 -d dist
# In another terminal:
python tests/video_studio/demo_check.py http://127.0.0.1:8878 /tmp/video-shooting-sequences
```

## Release state and order

Implementation is on `codex/video-studio`, based on main `81cab004ef6c9165230e7aa0723f7853b2ec1b9f`. The original checkout and its untracked `codex-brief.patch` were preserved. No changes are deployed by building or opening the PR.

At preparation time the site's AWS console session was signed out and no local AWS profile existed. Deployment is awaiting restored access to account `430110755505`. Publication is already authorized; this is an access dependency, not another approval requirement.

Deploy the backend package first using the existing site-admin deployment procedure. Preserve the current method object/version, owner parameters, API gateway configuration and roles. Inspect the prepared change set and confirm that only the intended function code updates are present. Verify denied anonymous catalog/read/write requests, private/no-store responses, package contents and runtime health before merging the static release. Then verify the successful static deployment and served HTML/JS/CSS against the build. Signed-in production acceptance requires the owner's real website session; isolated test success must not be represented as completed production acceptance.

No videos have been recorded, uploaded or scheduled by this implementation. Existing LinkedIn schedules and public educational content are unchanged.
