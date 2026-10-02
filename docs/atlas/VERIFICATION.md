# Verification · 2026-10-02

Everything below was run in the build session on branch `claude/shams-ai-atlas` against a local build served with `python -m http.server -d dist 8767` (Chromium via Playwright). Nothing was deployed.

## Commands and results
| Command | Result |
|---|---|
| `python build.py` | Pass. Prints `atlas: 19 concepts (14 linked to the Learn map), 33 step templates, 9 sources`. Content errors stop the build. |
| `node --test tests/atlas/*.test.mjs` | **12 passed, 0 failed.** All 128 interventions × design combinations end in exactly one known outcome; all six outcomes reachable; denied refund never executes; retries ≤ 2; budget never exceeded; no refund without approval; specialist never runs issue_refund and its work order withholds conversation and credentials; missing evidence or notes never produce a refund proposal; determinism; n(n−1)/2 vs n−1; URL state validation and round trip. |
| `python -m unittest discover -s tests/atlas -p 'test_*.py'` | **14 passed.** Registry valid; ids unique; required fields; every registry concept drawn in the scene; broken references caught; sources dated and https; standalone SVGs carry explicit fills (regression for the solid-black sheet); counts generated from data; legacy anchors on Learn and Method; `ks-learn` preserved; internal links resolve; sitemap and search include the atlas; text equivalent present; no em or en dashes in output. |
| `python tests/atlas/ui_check.py http://localhost:8767 <dir>` | **61 passed, 0 failed.** Default run to verified completion; back button; denied path (✕ mark, edge stops at gate, outcome, no refund slot); collaborator work order and structured result; click-to-inspect; Picture/Architecture keeps step and selection; corrupt localStorage; Harden lens; knowledge check recorded separately from "understood"; SVG export; expand, Escape, scroll and focus restore; keyboard-only stepping with reduced motion; SVG nodes not tab stops; no horizontal overflow and no console errors at 1920×1080, 2560×1080, 1440×900, 1280×800, 768×1024, 390×844, 360×740, 320×640 in light and dark; stage share of width ≥ 0.6 on desktop (0.64 to 0.71); regression on /, /learn/, /method/, /playbooks/, /playbooks/agentic-ai/, /tools/, /tools/availability/, /writing/ at 1380 and 390; site search finds the atlas. |

## Inspected by eye (screenshots in `docs/atlas/screenshots/`)
Default and completed run, collaborator, denied action, architecture view, Harden lens at 1440×900; 1920×1080; dark at 1440×900; 390×844; 768×1024. Also inspected during the build: 2560×1080 (scene letterboxed with margins; usable), 320×640 (stage framed on the active region; small but readable with zoom).

## Content corrections made on the live pages (in this branch)
- Learn, agentic loop rule: removed "safety net, never as the exit"; success is a verified goal; limits are legitimate, reported exits.
- Learn, hub and spoke: replaced the borrowed "AI in creative industries" example with Khalid's own incident-triage example.
- Learn, enforcement: "A hook is a rule" → "A check in code is a rule"; hooks can also only log or ask a model; code can be wrong too; removed "Zero exceptions, every time" and the borrowed closing line.
- Method #agentic: memory is not only progress and is not "retrieved every time"; skills cannot grant permissions; money and access need a check in code at the boundary, not "a hook".
- Learn map, agent idea: "until the stop reason says it is done" → goal verified or a bounded exit; stop reason explains one response.
- Home and Learn idea counts now generated from `content/learn/graph.json` (home said 32; the data has 44).

## Sources checked (fetched and read on 2026-10-02)
Anthropic: Building effective agents; Effective context engineering; Agent Skills. Claude Platform: Handling stop reasons (redirected from docs.claude.com). Claude Code: Hooks, Subagents (redirected to code.claude.com). MCP: Architecture overview (served as protocol 2026-07-28), Specification authorization (latest), Security best practices. Claims supported are listed per source in `content/atlas/sources.json`. One concept (`recovery`) is marked **needs review**; four are **editorial** (teaching judgment).

## Contrast (computed, WCAG relative luminance)
Light: body/card 9.87, atlas mute on paper 5.86, on context tray 4.86, blue on card 7.65, gold-ink on paper 4.98, warn on card 5.52. Dark: body/card 9.77, atlas mute on paper 7.42, blue/card 7.77, warn/card 7.35. Decorative thin rules (rule2 on paper 1.6) carry no meaning on their own; slot state also changes the icon fill and label colour.

## Performance (local, uncompressed server; CloudFront serves gzip)
| Asset | Bytes | gzip -9 |
|---|---|---|
| /learn/atlas/index.html (scene + registry inline) | 233,292 | 44,523 |
| /atlas/atlas.js | 35,484 | 10,882 |
| /atlas/engine.js | 5,297 | 2,089 |
| /atlas/atlas.css | 24,106 | 5,473 |
| /learn/atlas/scene.svg and scene-dark.svg (Learn preview, lazy) | 57,263 each | about 7,300 each |
Local timings: atlas DOMContentLoaded 541 ms, load 845 ms, 6 requests; /learn/ 147 ms and 372 ms. The Learn page grows by the call-out band; its preview image is lazy-loaded. No continuous animation: the courier runs once per step and is off with reduced motion.

## Print one-pager
Rendered headless with Chromium print media to A4 PDF for `?x=denyRefund&step=10&focus=authorization`. First attempt: page 2 had the inspector text overlapping the text-version headings, because the inline height set by `fitHeight()` beat the print rule. Fixed with `!important` heights and block flow in `@media print`. Re-rendered: three pages, scene and current step on page 1, concept and sources after, no overlap.

## Not run / not verified
- Real screen readers (VoiceOver, NVDA) and Windows High Contrast. Automated checks do not establish WCAG conformance.
- Browser zoom at 200 to 400 percent beyond the 320 px reflow check.
- Safari and Firefox (only Chromium was run).
- The browser print dialog itself (the print layout was rendered headless instead; see below).
- Learning outcomes with real learners. No comprehension claims are made.
- The reference folder under `~/Downloads/` (the copy under Documents/Projects was reviewed instead).
