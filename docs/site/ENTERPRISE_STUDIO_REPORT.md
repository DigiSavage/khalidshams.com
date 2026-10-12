# Enterprise agent studio · 12 October 2026

## Published release

Published through [PR #9](https://github.com/DigiSavage/khalidshams.com/pull/9), merge `7b48126f989fc7f6bd19f968f2c729a9b19731c9`, with successful [deployment 38298640673](https://github.com/DigiSavage/khalidshams.com/actions/runs/38298640673). Live URL: https://khalidshams.com/architect/agent-studio/. The live browser suite passed 231/231 after initial publication and again after the mobile follow-up in deployment 38302607517.

## Purpose and placement

The existing field guide explains components, and the Atlas follows a request. The new `/architect/agent-studio/` joins those ideas into a complete enterprise design journey: business outcome, architecture choice, authority, evidence, evaluation, release and operation.

This is an additive teaching page. It is linked from Home's workshop, the Architect hero and desktop/mobile submenu, and the Method delivery field guide. It is registered in the sitemap and site search. Existing Atlas lessons, concept IDs, scene IDs, data attributes, artwork and learning progress keys are preserved.

## What the reader can do

- Switch between document intelligence and an internal knowledge assistant. Both complete written designs remain readable without JavaScript.
- Compare conventional automation, grounded assistants, fixed AI workflows, bounded tool agents and specialist coordination.
- Choose a pattern independently of business authority. This reference design narrows consequential autonomous writes to reviewed writes; it never treats model capability as authorization.
- Follow Scope, Harden, Anchor, Measure and Sustain along a continuous reading rail. Each lens maps to the existing eight gates and leaves a concrete design deliverable.
- Step through synthetic runtime events. Fixed, adaptive and specialist patterns have distinct handoffs and tool-call counts. Approval, rejection, permission revocation, payload changes, insufficient evidence, unallowlisted actions, budget exhaustion and uncertain write results are explicit states.
- Inspect a public event trail and a code-native architecture drawing. Mobile defaults to an enlarged active region; the complete map remains one button away. Light and dark modes follow the existing tokens and artwork.
- Compare Azure model deployment with Azure-hosted and Anthropic-hosted Claude in Foundry. The processing boundary, provider terms and integration capabilities must be checked for the exact deployment.
- Diagnose source, extraction, model-behavior and enforcement failures. Guidance distinguishes RAG, conversation memory, prompt/tool changes, custom document training and supported language-model fine-tuning.
- Download a text design record with choices, boundaries, tests, operating guidance and unresolved production decisions. The simulation keeps design inputs in page memory and makes no model or operational cloud calls. Optional site measurement can record allowlisted interaction counts after consent, never those inputs.

## Files

| File | Responsibility |
|---|---|
| `content/enterprise/studio.json` | Two worked examples, acceptance cases and seven checked primary sources |
| `enterprise_build.py` | Build validation, static examples, illustration placement and live SVG |
| `templates/enterprise.html` | Enterprise journey, platform mapping, improvement and review record |
| `static/enterprise/engine.js` | Pure deterministic simulation, bounded authority and design-record generation |
| `static/enterprise/studio.js` | Accessible controls, active diagram regions, local record download |
| `static/enterprise/studio.css` | Scoped responsive styles using the existing visual tokens |
| `tools/export_enterprise_preview.py` | Standalone offline review export, separate from the production build |
| `tests/enterprise/` | Engine, registry/build and browser interaction checks |

The studio reuses the existing finished `atlas-workshop` light/dark illustration through `art_assets.illustration()`. No raster image is used for technical relationships or mutable labels. The new diagram uses instruments for software, a solid human reviewer, dashed boundaries, typed edges, cobalt focus, gold budget/review and coral denial with explicit text.

## Verification

Built against `main` at `1dde9b4d81b30d324ba1f201985117cb9e79eb75`. Build output: 482 search entries, 9 live posts, 53 approved/scheduled posts. No publishing metadata changed.

| Check | Result |
|---|---:|
| Node Atlas and enterprise engine tests | 28 passed |
| Python Atlas, Learn, art and enterprise structure tests | 43 passed |
| Enterprise browser checks | 231 passed |
| Atlas browser checks | 95 passed |
| Learn browser checks | 186 passed |
| Menu browser checks | 103 passed |
| Delivery field-guide browser checks | 96 passed |
| Total named automated checks | 782 passed |

The engine matrix exercises 2,160 combinations of example, condition, authority, pattern, call limit and reviewer decision. It checks termination, determinism and budgets. Targeted assertions check that read-only and rejected runs never write, revoked permission or changed payload blocks an approved operation, and a timed-out write remains unknown.

New-page browser coverage: 360, 390, 768, 1024, 1440 and 1920 CSS pixels; light/dark; reduced motion; an emulated 200 percent zoom viewport; no-JavaScript reading; keyboard reset; both diagram modes; example and authority changes; approval/revocation; provider boundaries; download content and no script errors or horizontal page overflow. Evidence includes desktop and phone captures in both themes.

The standalone preview was opened with external HTTPS requests blocked. Embedded artwork and controls worked without a network connection. Site-wide navigation in that export links to the current public site; it does not simulate the site's search or drawer.

Environment notes:

- Browser checks ran in Chromium 134 with Playwright 1.51.0. External Google Fonts requests failed from the browser in this environment. The existing `tests/site/run_cached.py` helper served unmodified font responses fetched separately; application HTML, scripts and assertions were not mocked.
- Two existing Atlas assertions misclassified hidden SVG groups: Chromium returned nonzero group boxes despite computed `display:none`. A small `svg_visible` test helper now checks ancestor display in addition to Playwright visibility. Production Atlas code did not change.
- The test server was launched in the same execution process as each browser check because execution sessions have separate loopback contexts here.

Reproduction, after installing `requirements.txt` and Playwright:

```bash
python build.py
node --test tests/atlas/*.test.mjs tests/enterprise/*.test.mjs
python -m unittest tests/atlas/test_registry.py tests/learn/test_structure.py tests/learn/test_art.py tests/enterprise/test_structure.py
python -m http.server -d dist 8767
```

With that server running:

```bash
python tests/enterprise/ui_check.py http://localhost:8767 /tmp/enterprise-ui
python tests/atlas/ui_check.py http://localhost:8767 /tmp/atlas-ui
python tests/learn/ui_check.py http://localhost:8767 /tmp/learn-ui
python tests/site/menu_check.py http://localhost:8767 /tmp/menu-ui
python tests/site/delivery_check.py http://localhost:8767 /tmp/delivery-ui
python tools/export_enterprise_preview.py
```

## Limits and release boundary

The page is a deterministic teaching experience and proposed reference architecture, not a production agent builder. It does not provision Azure, invoke Anthropic, process customer documents, train a model or provide measured enterprise outcomes. Acceptance criteria and service mappings need validation for the client's actual estate. The simulation demonstrates selected known failure cases, not exhaustive prompt-injection detection or a security guarantee.

No user testing, learning gains, Safari/Firefox compatibility or screen-reader audit is claimed. The diagrams and copy are reviewable additions using the current visual language. The owner has authorized merge and publication after fresh integrated verification.

## Integrated release verification · 12 October 2026

Imported the supplied patch after verifying SHA-256 `a271b4a4bd000cafb34c593dfc1dbe19f599dff95229ad9d238b88712276763c`. The original author is preserved. The patch applied cleanly to current main `1dde9b4`. The feature branch is pushed successfully with the current GitHub CLI identity; the prior environment's authentication limitation does not apply here.

Fresh integrated results: 28 Node tests, 43 Python tests, 231 Enterprise browser checks, 95 Atlas, 186 Learn, 103 menu and 96 delivery checks, totaling 782 named checks. Playwright 1.63.0 with its bundled Chromium was used, with unmodified cached Google Font responses. Reviewed phone and desktop screenshots in both themes. The narrow SVG ancestor-visibility correction preserves the existing assertions. Public punctuation and diff whitespace checks are clean. No workflows, publisher metadata or original patch files changed. The optional offline export is absent from the production payload.

This records the pre-merge gate. Deployment and live verification are recorded separately after the workflow completes; local passing tests alone do not establish publication.
