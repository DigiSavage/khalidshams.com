# From discovery to delivery · 2026-10-21

Public route: `/method/engagement/`. Branch: `codex/discovery-to-delivery`, based on `246caa9` from main. The homepage, Method page, Architect page and both Method menus link to the experience. Search and the sitemap include it.

## Purpose and approach

The page makes the complete architecture engagement inspectable. A field-service quote preparation example follows one decision, D-01, from account preparation to operation. It shows what the architect does, the artifact left behind, the accountable role, the evidence needed to proceed and the reason to hold each stage.

This is explicitly a new worked design with illustrative planning inputs. It is not a historical customer engagement, a deployed business system or a measured outcome. No private source documents, recordings, recruiter or customer identities, compensation, interview status or internal links are published. It does not create records in the private Decision Room.

## Coverage

| Responsibility | Inspectable implementation |
| --- | --- |
| Prepare before the meeting | Account hypotheses, participant roles, evidence request, decision-focused pre-read and a 60-minute example agenda |
| Know the audience | Four views for executives, engineering, risk and operations, with different questions and evidence but the same underlying decision |
| Discover the actual work | Current-state handoffs, exceptions, source ownership and a baseline measurement plan |
| Select an architecture | Process improvement and deterministic automation compared with a bounded AI draft; Azure foundations, read-only ERP integration and a separate Fabric measurement path |
| Make a commercial commitment | SOW deliverables, exclusions, role effort, assumptions, dependencies, acceptance and change control; technical, commercial and delivery authority stay distinct |
| Rehearse the uncertainty | Approved or synthetic samples, missing and stale data, malicious embedded instructions, rejection and a continuation decision |
| Lead delivery | Design authority, workstream interfaces, decision history, reviews, escalation and customer communication |
| Release with evidence | Access, source isolation, approval replay, operational readiness and a rehearsed fallback |
| Operate and measure | Preparation plus review effort, correction rate, adoption, reliability, cost and a continue/change/retire decision |
| Enable a capable team | Shadowing, teach-back, debriefs, runbooks and demonstrated exception handling |
| Develop the practice | Joint account planning, conditional program eligibility, reusable evidence and customer permission |

## Interactive mechanism

Changing a requirement updates four connected records: decision, scope, acceptance and operation. It also updates ownership and the planning envelope. Changing the audience never changes the price or permissions.

- Baseline: draft-only pilot, 160 to 252 person-hours.
- Requested automatic sending: retain the draft-only boundary and identify a separate assurance package, 208 to 332 person-hours. No action authority is granted.
- Unowned source: hold delivery; totals remain unknown. The 24 to 36 hour investigation allowance is not a delivery estimate.
- Two-week request: narrow to a read-only prototype, 96 to 144 person-hours. Effort is not a promised elapsed duration.

The sample labor rate is USD 150/hour with 15 percent contingency. Software, cloud usage, licenses, tax, customer effort and ongoing support are excluded. These are teaching assumptions, separate from the $950 Architecture Decision Review. The pilot ends at an explicitly approved draft and has no sending or dispatch capability.

The exercise runs locally in the browser without a model call, client-data input, stored case or business mutation. URL state contains allowlisted audience and condition choices. Copy/download includes the current change assessment, assumptions and an explicitly labeled baseline workflow reference. Static artifacts and audience briefs remain available without JavaScript. Printing expands artifacts, retains sources and restores disclosure state afterward.

## Implementation and evidence

`content/engagement.json` owns the 11 stages and audience narratives. `engagement_build.py` validates and escapes them into `templates/engagement.html`. Page-scoped CSS and JavaScript live in `static/engagement/`. The pure engine has no DOM, storage or network dependency.

Two homepage employment summaries were corrected to distinguish nearly five years supporting Microsoft Azure customers and programs across partner roles and direct Microsoft employment. Existing outcome metrics remain in their original context.

Primary Microsoft references were checked on October 21, 2026 and are linked on the page. Product choice does not imply production readiness; licensing, region, capability status, customer permissions and program eligibility remain engagement-specific checks.

Verification and selected screenshots are in `evidence/engagement/`. The release pull request records the final test counts, deployment run and live verification. Tests exercise real rendered controls and downloads; API responses are intercepted in regression tests so no inquiry or analytics record is created. Browser automation covers Chromium and WebKit, not a physical phone or a screen-reader certification.

Reproduce after building and serving `dist/`:

```sh
.venv/bin/python build.py
node --test tests/engagement/engine.test.mjs
.venv/bin/python -m unittest tests/engagement/test_structure.py
.venv/bin/python tests/site/run_cached.py tests/engagement/ui_check.py http://127.0.0.1:8767 /tmp/engagement-check chromium
.venv/bin/python tests/site/run_cached.py tests/engagement/ui_check.py http://127.0.0.1:8767 /tmp/engagement-check webkit
.venv/bin/python tests/site/run_cached.py tests/site/text_layout_check.py http://127.0.0.1:8767 /tmp/engagement-layout
.venv/bin/python tests/site/run_cached.py tests/site/menu_check.py http://127.0.0.1:8767 /tmp/engagement-menu chromium
.venv/bin/python tests/site/run_cached.py tests/site/menu_check.py http://127.0.0.1:8767 /tmp/engagement-menu-webkit webkit
.venv/bin/python tests/site/run_cached.py tests/commercial/ui_check.py http://127.0.0.1:8767 /tmp/engagement-commercial
```

The original untracked `codex-brief.patch` is preserved. No workflow, credential, access policy or backend implementation is changed. The generated public-page registry includes this route and the two newly published posts; that registry file alone does not redeploy the analytics service. Publication uses the existing static site workflow.

## Inquiry integration follow-up

Live integration review identified a dependency on the separately deployed inquiry service's page registry. A newly published page can produce an explicit `400 Unknown public page` validation response even when every user field is valid. The contact form now retries that one pre-storage rejection once with `/contact/` as the source. Inquiry ID, challenge and user fields remain identical. Other errors, ambiguous responses and network failures do not trigger this fallback; storage must still be explicitly confirmed. No production test inquiries are seeded.

This preserves inquiries while static routes and the service registry are deployed independently. Detailed analytics for newly added routes still require the normal backend registry refresh; this static release does not claim those observations are available.

All 100 commercial/inquiry browser checks pass, including the legacy-registry recovery, unchanged identifiers and challenge, refusal to retry other errors, failed fallback storage, network failures and ambiguous receipts. See `evidence/engagement/contact-resilience.json`. The initial public deployment completed in [run 39628987077](https://github.com/DigiSavage/khalidshams.com/actions/runs/39628987077); live page and asset bytes matched the tested build, and Home, Method and Architect exposed the new link.
