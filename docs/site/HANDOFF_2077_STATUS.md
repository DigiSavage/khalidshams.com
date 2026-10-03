# SHAMS Atlas 2077 handoff: implementation status · 2026-10-03

Reconciled against the handoff brief, the repository and the live site. Rendered evidence is in `docs/site/evidence/` (screenshots of the build, not art studies).

## Source status, stated plainly
- The five approved illustration studies, the mobile "Approval required" composition, "Follow the thread / 2077" and the human-free workbench were **not available** to this build: not in the repository, not on any branch, not in the linked folders. Nothing here claims to have seen them. The scene registry marks every scene `study: awaiting-study`.
- The two phone screenshots of the Atlas and Method pages were available and were used as current-output references.

## Done in this pass (no art required)
| Brief item | Where | Evidence |
|---|---|---|
| Scene registry: five scenes locked to meaning and real routes, cast, object language, edge legend | `content/scenes.json`, validated in `learn_build.validate_scenes` at build | `tests/learn/test_structure.py` |
| Five reading chapters over the real 15 steps; every step carries a chapter; runs move back and forth between chapters | `content/atlas/scenarios/damaged-order.json` (`chapters`, `chapter` per step) | default run sequence: 01, 02, 02, 02, 03, 04, 02, 02, 03, 04, 04, 05, 03, 05, 05 |
| Chapter rail with the cobalt thread; jumps to this run's first step of a chapter; preserves design, condition, selection, pending state; keyboard operable; compact (under 100px) | `templates/atlas.html` `{{CHAPTERS}}`, `atlas.js`, `atlas.css` | `tests/atlas/ui_check.py` 2c; `evidence/atlas-wide-1920.jpg` |
| Trace as the inspector's first tab: public inputs, proposed arguments, results, evidence links, synthetic events; no hidden reasoning | `templates/atlas.html` | `evidence/atlas-mobile-step10-390.jpg` |
| Recorded approvals labelled as replay events | `atlas.js` event trail | check "recorded approval is labelled" |
| "Software metaphor" label beside every operator figure in the flagship and in the vignettes with a prominent operator | `atlas_scene.py`, `vignettes.py` | check "operators carry a software-metaphor label" |
| Agent loop: completion decided by application checks and explicit criteria; RAG, Memory and MCP reach more than one station; a CHECK sits between proposal and action | `templates/method.html` `#ag-svg`, captions | `evidence/method-loop-object-only-1440.jpg` |
| Enterprise clarity: the bookshelf story replaced by a dependency map with an unverified link kept unknown and a blast radius | `vignettes.estate`, Home situation 2 | `evidence/home-five-placements-1920.jpg` |
| Architectural judgment: the ladder replaced by a decision table with trade-offs and a signed recommendation (motif, no real name) | `vignettes.judgment`, Home situation 3 | same |
| Validation matrix: 360, 390, 430, 768, 1024, 1280, 1440, 1920, 2560; 200 percent zoom emulated as a 720 x 450 CSS viewport at 2x; light and dark; reduced motion | `tests/learn/ui_check.py`, `tests/atlas/ui_check.py` | 186 and 95 checks pass |

## Checked against the brief's facts
- The mobile composition's "Step 10 of 15" and "$84" agree with the scenario: step 10 of the default run is `authz_refund_approval`, "Allowed, but approval required", amount 84.00 from `content/atlas/scenarios/damaged-order.json`.
- Palette: the site's tokens were kept (paper #F7F7F5, cobalt #1F45C8); they pass contrast in both themes. The brief's warmer candidates (#F7F3E9, #2448D8) are a site-wide decision, not made here.

## Not done, and why
- Placing the five studies: the files were not supplied. When they are, each goes into its registered home as an illustration layer with its own alt text, with labels, values and controls kept in HTML, and desktop, compact, mobile and thumbnail crops recorded per the brief.
- The sticky-scene-with-scrolling-beats layout for the Atlas chapter: the chapter rail and step controls are in; the scrolling-beats variant is not, because it changes the lesson's reading model and should be judged against the "Follow the thread" study.
- The site-wide thread between the five homes on Home: not drawn; the five cards are not sequential operations and the brief leaves this optional.
- Retrieval, memory, tool/interface, collaboration, governance, enterprise, decision, SHAMS and operations diagram families: the flagship and model lessons cover most states (insufficient evidence, missing note, denied, failed, retried, escalated, budget, blocked). An inventory of which family each existing figure belongs to is in `docs/site/VISUAL_SYSTEM.md`; the estate map and Learn map still use their older node styles.
