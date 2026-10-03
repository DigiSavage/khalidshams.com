# Brief for Codex: enhance the khalidshams.com drawings in the illustrated-studio theme

Repository: DigiSavage/khalidshams.com, branch off `main` (currently includes pull request #4). Work on a branch named `codex/illustrated-studio`. Do not push to `main`, do not deploy, do not touch `.github/workflows/`, do not commit `.venv/`, `dist/`, or anything from the reference drawings collection. Commits are authored as Khalid Shams <khalidshams@gmail.com>. No em dashes, en dashes or " -- " in anything public (templates, content, static, docs that render).

Read first, in this order:
1. `CLAUDE.md` (site rules), then `docs/site/VISUAL_SYSTEM.md` (the inventory of every visual and the grammar in section 3), then `docs/site/HANDOFF_2077_STATUS.md` (what is done and what is waiting on art), then `content/scenes.json` (the five scenes, cast, object language, edge legend).
2. Build and look: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python3 build.py && python3 -m http.server -d dist 8767`. Pages: `/`, `/learn/`, `/learn/atlas/`, `/learn/atlas/how-models-are-made/`, `/architect/`, `/method/`.

## The theme, in one paragraph
An illustrated working studio. Ivory paper, ink-black people, pencil and engraving texture, pale architectural objects, confident cobalt accents, restrained gold, editorial serif headings. Solid figures are people; outline figures are software and always carry a "software metaphor" label; a dashed box is a boundary; a gate carries a text mark (✓ ✕ ⏸); cobalt means focus and control, gold means cost or pending, coral means denial or error, and every colour meaning has a non-colour cue. One dominant action per composition, selective detail, usable negative space. Keep the KS identity (`static/logo.png`, navy #012480, gold #D4AF56) and the site tokens in `templates/base.html` `:root` (paper #F7F7F5, ink #0E1012, cobalt #1F45C8, gold #B8912F, coral #B4442E, with the dark set beside them). If you propose the warmer ivory #F7F3E9, do it as a separate commit touching only the tokens, with contrast numbers for both themes.

## Exact drawings to enhance

Every drawing below is code that generates SVG, with explicit fallback fills on every shape and site tokens applied through CSS (`.atlas-scene` in `static/atlas/atlas.css`, `.vig` in `templates/base.html`). Enhance means: keep every `id`, `data-o`, `data-c`, `data-sc`, `data-e`, `data-part` and class name exactly as is (the engine, tests and progress keys depend on them), keep the viewBox, and raise the drawing quality: texture, line-weight system, posture and expression on the people, selective detail, negative space, label-safe regions, lines routed away from text.

| # | Drawing | File and function | Route | What it must become |
|---|---|---|---|---|
| 1 | The flagship scene (atlas-workshop) | `atlas_scene.py` `scene()`, 1280×800, 24 objects | `/learn/atlas/` | The full studio from study 1: a concerned requester holding the damaged lamp, the owner at the goal board, the central workbench with the context tray, evidence shelves, the reviewer at the action boundary. People get posture and expression (`person()` and `operator()` are the only figure helpers; extend them, do not fork them). Keep the Architecture layer (`.arch`) untouched. |
| 2 | The model-making scene | `atlas_scene_model.py` `scene()`, 15 objects | `/learn/atlas/how-models-are-made/` | Same studio language for the training floor: tokenizer, embedding map, transformer stack, dials, the training loop, fine-tuning station, preference pairs with the rater, the evaluation bench, the release registry. The rater is a person; nothing else here is. |
| 3 | The 19 vignettes | `vignettes.py`, one function each, 320×180: `request`, `door_new`, `door_architect`, `door_explore`, `assistant`, `act`, `backoffice`, `knowledge`, `multi`, `decide`, `estate`, `judgment`, `cluster_foundations`, `cluster_learning`, `cluster_language`, `cluster_agents`, `cluster_operate`, `cluster_society` | Home doors and situations, `/architect/` cards, every `/learn/ideas/<id>/` and `/learn/paths/<id>/` hero | Optically simplified small forms of the same language. `act` is production-review (study 3): the $84 proposal, a reviewer pausing it, a closed gate. `estate` is enterprise-clarity (study 4): tangled systems organised into a dependency model, the unverified link kept unknown. `judgment` is architectural-judgment (study 5): alternatives on a table, explicit comparison, a signed recommendation with no real name. `decide` is shams-autonomy (study 2) and must not attach S H A M S to five rungs. |
| 4 | The agent loop | `templates/method.html` `#ag-svg` (460×440), pills `data-part` llm, skills, mcp, rag, memory; the CHECK badge; captions in the `CAP` object | `/method/#agentic` | Redraw with the studio grammar: the four stations, the goal at the centre, the check between proposal and action, the secondary dashed leads kept (retrieval and memory also reach Plan, MCP also returns to Observe). Keep the click behaviour and the `STN`/`STAGE` maps. |
| 5 | Mesh vs hub | `templates/method.html` `#ag-mesh`, `#ag-hubsvg` (240×240) | `/method/#ag-cost` | The slider and arithmetic are correct; make the two topologies read as drawings, gold for mesh links, cobalt for the hub. |
| 6 | The estate map | `templates/method.html` `#svg` (1000×760), classes `.m-*` | `/method/#map` | Group by domain and ownership with dashed boundaries, typed dependency edges, selected dependency and blast radius inspectable, risk outlines in gold and coral kept. Keep every node id and the industry re-weighting script. |
| 7 | The Learn living map | `templates/learn.html` `#ln-svg` (1800×800), nodes from `content/learn/graph.json`, classes `.ln-*` | `/learn/#map` | Node and edge styling in the grammar (cobalt lit, understood marks as a non-colour cue, cluster regions as dashed boundaries). Keep node ids, the circuit stepping and the `ks-learn` key. |
| 8 | The Learn inline diagrams | `templates/learn.html`, classes `.ln-box`, `.ln-dia`, `.ln-done`, `.ln-hub`, `.ln-arrow`, `.ln-lab` (decision tree, loop strip, hub and spoke, prompt vs hook) | `/learn/#decide` `#loop` `#multi` `#enforce` | Same line-weight system and typed edges as the atlas; these currently predate the grammar. |
| 9 | The chapter rail | `static/atlas/atlas.css` `.chapters`, markup from `atlas_build.py` `render_scene` | `/learn/atlas/` | The cobalt thread from the "Follow the thread / 2077" study: one continuous line, five stops, current stop lit. It is navigation, never a data edge. Must stay under 100px tall on desktop and compact on phones. |

## The eight studies: how to hand them in so they land in the build

Put the files at `static/art/<scene-id>/<variant>.webp` (and `.png` masters under `art-src/` which is gitignored; add that line to `.gitignore`). Scene ids: `atlas-workshop`, `shams-autonomy`, `production-review`, `enterprise-clarity`, `architectural-judgment`, plus `thread-2077` and `workbench-objects` for the two new studies and `approval-mobile` for the mobile composition. Variants: `desktop` (1600 wide), `compact` (960), `mobile` (720), `thumb` (320). Light and dark are separate files, never an inverted copy: `desktop-light.webp`, `desktop-dark.webp`.

Add `content/art.json`:
```json
{"assets": [{"scene": "production-review", "variant": "desktop", "theme": "light", "file": "/art/production-review/desktop-light.webp",
  "purpose": "illustration layer behind the Home situation card", "crop": "full", "background": "paper",
  "alt": "A reviewer pauses a proposed $84 refund at a closed gate; the proposal card waits beside it.",
  "concepts": ["authorization", "approver", "guardrails"], "text_in_image": false}]}
```
Rules: `text_in_image` must be false for anything placed on a page (headings, amounts, states and buttons stay in HTML); a study with baked-in text is a reference, not a placed asset. `concepts` must be ids from `content/atlas/concepts.json`. Each asset lists its alt text. The build will validate this file.

## Non-negotiables
- No new framework, no React, no runtime model calls, no new deployment platform, no raster for diagrams (raster is allowed only as the illustration layer declared in `content/art.json`).
- Technical truth over the poster: the step index, the $84, the outcomes and the edge types come from `content/atlas/scenarios/damaged-order.json`; "Step 10 of 15" and "$84" are correct; the 2077 poster's copy is not product copy.
- Labels never clipped, lines never through text, no `overflow:hidden` as a repair. Check at 360, 390, 430, 768, 1440, 1920 and at 200 percent zoom (a 720×450 viewport at 2x).
- Reduced motion gets complete static states; no scroll hijacking; no continuous decorative animation.

## Before you hand back
```
python3 build.py
node --test tests/atlas/*.test.mjs
python3 -m unittest tests/atlas/test_registry.py tests/learn/test_structure.py
python3 -m http.server -d dist 8767 &
python3 tests/atlas/ui_check.py http://localhost:8767 shots/atlas
python3 tests/learn/ui_check.py http://localhost:8767 shots/learn
```
All must pass (currently 18, 16, 13, 95 and 186). Add screenshots of every drawing you touched at 1920 and 390, light and dark, under `docs/site/evidence/codex/`. Write `docs/site/CODEX_REPORT.md`: what changed per drawing, what you verified, what you did not, and anything in the brief you could not reconcile with the source. Do not claim user testing or learning gains. Open a pull request against `main` and stop; publication is Khalid's step.
