# Illustrated studio implementation

Base: `e69d950` on `main`. Branch: `codex/illustrated-studio`.

This pass develops the reusable drawing language for a broad principal architecture resource: systems, dependencies, ownership, trade-offs, operations and AI. The Atlas remains one learning area within that wider purpose. No learning gains or user testing are claimed.

## Repository and scope

Verified `/Users/khalidlens/Development/khalidshams-atlas`, origin `https://github.com/DigiSavage/khalidshams.com.git`, initial branch `main`, and fetched `origin/main` at `e69d950`. The initial untracked `codex-brief.patch` was preserved untouched. No backend governance, server recovery, workflows, deployment configuration, main-branch push, merge or deployment belongs to this change.

## Changes by drawing

| Drawing | Implementation and meaning |
| --- | --- |
| Flagship, `atlas_scene.py` | Extended the shared person helper with a solid coat, profile, expression and review, hold and pause poses. The requester carries a cracked lamp; the reviewer raises a hand at the approval boundary. Outline software figures have instrument-like detail. Binder, cabinet, book spines and workbench have sparse engraving in reserved margins. Moved the software caption clear of the head and fitted long labels. |
| Model making, `atlas_scene_model.py` | Shared human figures, graduated parameter dials, book spines, stack engraving and checkpoint contacts. Moved the training return below its label. The rater and existing release owner remain human. |
| All 19 vignette keys, `vignettes.py` | Shared figures, etched station and document surfaces, less tracking on small labels, an outlined learning-map board, data dots and dependency arrowheads. Production review stops at a closed gate with a visible pause and no outgoing execution line. Enterprise clarity keeps the unknown link unknown. Judgment keeps the B heading visible above its selected column and retains the unsigned-name signature motif. Autonomy remains five numbered rungs with a selected lower rung and no SHAMS-to-rung mapping. |
| Agent loop, Method | Four instrument plates, a pinned goal card, control dashes, small station symbols and square component tabs. The CHECK, secondary retrieval/memory/MCP leads, component interactions, captions and STN/STAGE mappings remain. |
| Mesh and hub, Method | Numbered software cards and dashed perimeter construction lines; gold mesh links and cobalt hub links. Slider and link-count arithmetic remain. |
| Estate map, Method | Infrastructure and AI-use domains have dashed boundaries and explicitly unresolved owners. Dependencies follow curved routes behind label halos. Node selection persists after pointer exit. Keyboard-operable dependency buttons expose the required maturity and potential blast radius derived from the existing `needs` registry. Industry payoff and risk re-weighting remain. These are declared planning dependencies, not evidence of a real customer's estate. |
| Learn living map | Seven separate cluster boards, including Society, with labels wrapped within each board. IDs, graph relationships, circuits, cluster zoom and `ks-learn` remain. Understood nodes have a visible check as well as colour and an accessible state label. Removed the recurring decorative signal animation; reader-triggered signals remain. |
| Learn inline diagrams | Structural line weights and paper-backed labels; runtime data uses solid ink and dot heads, calls use cobalt dashes and arrowheads. Decision-tree branches keep their distinct decision meaning. Added fallback presentation attributes to literal shapes. |
| Chapter rail | One continuous cobalt navigation line between five centered stops. Current and visited states retain their numbered non-colour cues. Desktop and mobile remain below 100px tall. |

The KS identity, light/dark tokens and all SVG viewBoxes are retained. No warmer-paper token change was made. Both Atlas Architecture layers were compared against fetched main and are byte-identical. Original Atlas IDs, data-o, data-c, data-sc, data-e and classes were compared and preserved.

## Visible integration across the site

The revised drawings were present inside existing lessons, but Method still opened with a long text introduction and the full collection had no public entry point. This follow-up places existing illustrations where readers arrive and where they make a decision:

- Home, Learn and Method now have a large drawing directly after the headline, before the introductory prose on phones, with a link to the illustrated library.
- Method places the estate, autonomy, production-review and judgment illustrations beside their map, ladder, gates and record sections. Existing interactive diagrams, controls and anchors remain in place.
- `/illustrated/` displays all 18 distinct vignette drawings (19 keys, with `Decide` aliasing `decide`), both full studio scenes in light and dark, and links to every interactive drawing family. Each picture leads to its working lesson or reference. The collection begins with estate architecture, ownership, decisions and operations.
- Desktop submenus, the phone drawer, the sitemap and search index include the library. All its local links and section targets are checked against the build.
- No new raster art is claimed. The previously unavailable studies listed below remain unavailable; this integrates the completed SVG work.

Additional evidence: `docs/site/evidence/codex/integration/` contains 48 screenshots of real page placements at 390 and 1920 in both themes, plus `checks.json`. The new check exercises widths 360, 390, 430, 768, 1440, 1920 and a 720 by 450 viewport at scale 2. It verifies visible drawings, theme-specific studio image loading, keyboard navigation, layout and script errors. Sticky navigation is hidden only within element screenshot capture, not during interaction checks or in the product.

## Missing art, exact intake paths

None of the eight approved studies was found in the repository. Current-output screenshots are evidence of the build, not substitutes for those studies. `content/scenes.json` continues to say `awaiting-study`.

Each row below is missing **all eight files** named after the table, for 64 missing WebP exports in total:

| Study | Required directory |
| --- | --- |
| Full workshop | `static/art/atlas-workshop/` |
| Autonomy | `static/art/shams-autonomy/` |
| Production review | `static/art/production-review/` |
| Enterprise clarity | `static/art/enterprise-clarity/` |
| Architectural judgment | `static/art/architectural-judgment/` |
| Follow the thread / 2077 | `static/art/thread-2077/` |
| Human-free workbench objects | `static/art/workbench-objects/` |
| Approval on mobile | `static/art/approval-mobile/` |

Required names in **each** directory: `desktop-light.webp`, `desktop-dark.webp`, `compact-light.webp`, `compact-dark.webp`, `mobile-light.webp`, `mobile-dark.webp`, `thumb-light.webp`, `thumb-dark.webp`. Target widths are 1600, 960, 720 and 320 respectively. PNG masters are also unavailable and belong under the now-ignored `art-src/`, never in the committed reference collection.

Added `content/art.json` with an honest empty asset list. Build validation checks required metadata, recognized scene/variant/theme, canonical path, file existence and WebP header, atlas concept IDs, duplicate variants, alt text, and `text_in_image: false`. Text-bearing references cannot pass intake. This is an intake gate, not automatic placement. Crops, pixel dimensions, illustration-only content and separately authored dark art still need visual review when real assets arrive. No placeholder art or invented alt text for unseen art was placed.

## Reconciliation and limits

- The brief says 19 vignettes but lists 18 functions; the registry has 19 keys because `decide` and `Decide` share the same drawing. Evidence includes every key.
- The model-making brief says the rater is the only person. Existing source and the visual system also explicitly identify a release owner. Both established human roles were preserved; no training machinery was personified.
- The estate map contains layer and AI-use dependencies, not discovered customer systems or actual owner names. The new grouping states that owners must be established in review. Its potential impact list is calculated from those declared dependencies, without claiming a verified operational blast radius.
- `prompt vs hook` is an HTML comparison rather than a separate SVG in the source; its diagram-adjacent section is included in the visual evidence and its technical copy is unchanged.
- Actual study placement, approved crop matching, the reference mobile composition and a study-matched scrolling chapter layout cannot be completed without the studies. The existing focus/pan model remains.
- Complex maps deliberately retain pan/zoom or a corresponding HTML inspector on phones. A whole-scene thumbnail cannot make every small label readable; focus views and live HTML provide the reading detail.

## Verification

The final build and validation results are recorded below. Tests use Chromium through Playwright, including light and dark, reduced motion, widths 360, 390, 430, 768, 1440 and 1920, and a 720 by 450 CSS viewport at device scale 2 for the requested 200 percent equivalent. This is not a claim of manual Safari, Firefox, screen-reader or user testing.

Screenshots are under `docs/site/evidence/codex/`. Each drawing family has 1920 and 390 light/dark evidence; `vignettes-*` are contact sheets of every library key using the real generators and site CSS. `learn-map-overview-*` fit the whole SVG for review, separate from the actual scrolling page screenshots. Sticky navigation is suppressed only during element screenshot capture so it does not obscure long drawings. It is not hidden in the product.

Commands:

```sh
.venv/bin/python build.py
node --test tests/atlas/*.test.mjs
.venv/bin/python -m unittest tests/atlas/test_registry.py tests/learn/test_structure.py tests/learn/test_art.py
.venv/bin/python tests/atlas/ui_check.py http://localhost:8767 work/shots/atlas
.venv/bin/python tests/learn/ui_check.py http://localhost:8767 work/shots/learn
.venv/bin/python tests/site/illustrated_check.py http://localhost:8767 docs/site/evidence/codex
```

A direct Atlas run passed 95 checks. Subsequent runs hit intermittent external font timeouts: a diagnostic page loaded local files in about 20 milliseconds but waited about 18 seconds for Google Fonts. `tests/site/run_cached.py` caches the original font CSS and font bytes in `work/font-cache` across browser contexts. It does not replace or cache site HTML, JavaScript or styles, relax assertions, or substitute fonts. Final browser runs use:

```sh
.venv/bin/python tests/site/run_cached.py tests/atlas/ui_check.py http://localhost:8767 work/final-shots/atlas
.venv/bin/python tests/site/run_cached.py tests/learn/ui_check.py http://localhost:8767 work/final-shots/learn
.venv/bin/python tests/site/run_cached.py tests/site/illustrated_check.py http://localhost:8767 docs/site/evidence/codex
.venv/bin/python tests/site/run_cached.py tests/site/integration_check.py http://localhost:8767 docs/site/evidence/codex/integration
```

### Final results

| Check | Result |
| --- | --- |
| Static build | Passed: both Atlas lessons, six paths, 44 idea pages, 342 search entries |
| Atlas engine | 18 passed |
| Atlas registry and Learn structure | 29 passed |
| Art intake validation | 5 passed |
| Atlas browser suite | 95 passed |
| Learn and site browser suite | 186 passed |
| Focused studio browser suite | 180 passed |
| Integrated drawing browser suite | 213 passed |
| Total automated assertions/tests | 726 passed, zero failed |
| Public punctuation scan | Clean |
| Git diff whitespace check | Clean |
| Evidence | 112 JPEGs: 64 drawing checks and 48 real page placements, plus machine-readable check results |

The focused suite verifies keyboard dependency inspection, one selected dependency, industry risk re-weighting, mesh/hub arithmetic at twelve agents, component selection, the understood check mark and saved key, circuit stepping, Society zoom, and search arrival highlights. The additional layout matrix covers both lessons, Method and Learn in both themes at every requested width and the 200 percent equivalent. All 19 vignette keys pass SVG text-bound checks.
