# Concept-by-concept visual pass · 2026-10-05

## Scope and current status

The requested direction is to raise the visual quality throughout the existing learning flow, including lower-page concept cards, rather than only adding large art near the top. This pass completes independent repository changes. The original eight finished studies remain integrated. The extended concept-art set below is not complete because the built-in image service began failing to connect. The user explicitly chose to stay with that service and complete independent work; no CLI/API fallback was used.

## Completed in the repository

- Redrew all three entry-door diagrams in their existing card positions: six illustrated book stations in the same path order, three explicit decision gates beside a reviewer, and an open concept atlas. Decorative first/second-path completion cues were removed; actual browser progress remains authoritative.
- Added visible instrument side faces and paper depth through shared SVG primitives. This reaches both full interactive scenes and all 19 vignette keys (18 distinct drawings). Stateful rectangles, empty dashed boundaries and slot documents are excluded. Existing labels and front faces remain intact. Removed the blanket Picture-layer shadow that also blurred small labels.
- Added mounting geometry to Learn and Method map nodes without changing any dependency, node identity, radius weighting, position, selection handler or progress key.
- Matched finished rich art to 11 concept keys (10 distinct drawings) and placed it within their existing cards, with a keyboard-accessible disclosure for the original live diagram. This reaches 20 of 44 idea pages, three of six guided-path headers, four of six architect situations, the architect entry door on Home/Learn, and matching library cards. Unmatched families retain their improved native drawing instead of receiving unrelated art.
- Replaced the first technical studio thumbnail in the exact library section shown by the user with its finished workshop illustration. Its destination remains the same interactive lesson. The model-making preview retains its refined SVG while its dedicated rich study is pending.
- Both Architecture layers and all existing Atlas IDs, data-o, data-c, data-sc, data-e, data-part, data-slot, data-tk and data-crit hooks were compared against the previous commit and preserved. Reading order, destinations, lesson state and browser progress remain intact.

## New image generation and remaining files

Four light masters were generated with the built-in tool and saved under ignored `art-src/concepts/`: learning-path, learning-map, grounded-assistant and specialist-workflow. They are drafts for review and are not advertised as complete themed assets. The source artwork, exact prompts, selected mode and source hashes are recorded in `CONCEPT_ART_PROMPTS.json`. They have not been silently substituted for missing dark art.

The first batch for evidence-library, coordinated-team and model-foundations failed to connect. A subsequent single evidence-library retry also failed. No paid API was called.

| New concept study | Status | Exact master paths |
| --- | --- | --- |
| `learning-path` | Saved light master; dark missing | `art-src/concepts/learning-path-light.png`, `art-src/concepts/learning-path-dark.png` |
| `learning-map` | Saved light master; dark missing | `art-src/concepts/learning-map-light.png`, `art-src/concepts/learning-map-dark.png` |
| `grounded-assistant` | Saved light master; dark missing | `art-src/concepts/grounded-assistant-light.png`, `art-src/concepts/grounded-assistant-dark.png` |
| `specialist-workflow` | Saved light master; dark missing | `art-src/concepts/specialist-workflow-light.png`, `art-src/concepts/specialist-workflow-dark.png` |
| `evidence-library` | Light and dark missing | `art-src/concepts/evidence-library-light.png`, `art-src/concepts/evidence-library-dark.png` |
| `coordinated-team` | Light and dark missing | `art-src/concepts/coordinated-team-light.png`, `art-src/concepts/coordinated-team-dark.png` |
| `model-foundations` | Light and dark missing | `art-src/concepts/model-foundations-light.png`, `art-src/concepts/model-foundations-dark.png` |
| `model-training` | Light and dark missing | `art-src/concepts/model-training-light.png`, `art-src/concepts/model-training-dark.png` |
| `language-tokens` | Light and dark missing | `art-src/concepts/language-tokens-light.png`, `art-src/concepts/language-tokens-dark.png` |
| `operations-controls` | Light and dark missing | `art-src/concepts/operations-controls-light.png`, `art-src/concepts/operations-controls-dark.png` |
| `responsible-data` | Light and dark missing | `art-src/concepts/responsible-data-light.png`, `art-src/concepts/responsible-data-dark.png` |

After each complete pair is reviewed, export to `static/art/<study-id>/{desktop,compact,mobile,thumb}-{light,dark}.webp` and register it in `content/art.json` before placing it. The planned set has 22 masters: four generated, 18 outstanding. In particular, the six-path card and model-making studio are not claimed to have their final rich light/dark artwork yet.

## Verification

- Build: passed, 375 search entries.
- Engine: 18; Python registry/structure/art: 39; Atlas browser: 95; Learn/site browser: 186; focused SVG checks: 180; integrated page checks: 213; original art checks: 197; concept-flow checks: 148. Total: **1,076 passed, zero failed**.
- Existing interactive checks include light/dark, reduced motion, the viewport matrix and 200 percent equivalent, search, learning progress, step changes, conditions, keyboard navigation and the native diagram disclosures.
- All 44 idea pages retain their original diagram and progress control. Door destinations are checked unchanged. New evidence covers Home/Learn doors, architect situations, an idea and a guided path, and the studio previews at 390 and 1920 in both themes.
- Evidence: `evidence/codex/concepts/`, refreshed `evidence/codex/integration/`, and updated native drawing captures in `evidence/codex/`. No claim of manual Safari, Firefox, screen-reader or user testing.

No backend authorization work, workflows, main push, merge or deployment. The original `codex-brief.patch` remains untouched.
