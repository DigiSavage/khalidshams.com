# Implementation status · 2026-10-02 · branch `claude/shams-ai-atlas`

## Working
- `/learn/atlas/` workspace shell independent of the 1140px prose `.wrap`: toolbar, collapsible layer rail, central scene, inspector (This step / Concept / Check yourself), sized to the first screen on desktop.
- One connected scene (`atlas_scene.py`) with Picture and Architecture layers on the same objects; selection, step and design persist across the switch.
- Deterministic engine (`static/atlas/engine.js`): one-agent and coordinator + specialist designs; interventions: remove evidence, omit saved notes, deny refund permission, refund service failure (bounded retry, max 2 attempts), customer cancels, tight step budget. Outcomes: verified completion, waiting for input, denied before execution, cancelled, budget exhausted, operational failure.
- Step controls (follow / previous / next / play-pause / reset), keyboard arrows, reduced-motion support (no courier animation; play slower).
- SHAMS overlays (S H A M S) as design lenses with highlighted objects, letter badges and an explanation panel.
- Typed edges: information (solid + dot), control (cobalt dashed + arrow), approval route (dotted), ownership (grey dotted). Learn-first links only in the inspector (◇).
- Inspector: desk contents, proposed vs executed tool call with arguments and results, structured specialist result, evidence with provenance, work order (given / not given), budget, synthetic event trail (no model reasoning), concepts at three depths, "Where the analogy stops", sources with check dates and status.
- Coordination arithmetic n(n−1)/2 vs n−1 with the topology-only caveat (team design and Measure lens context).
- Knowledge checks (3); progress kept locally in `ks-atlas-v1` with visited / understood / passed kept separate; the Learn map's `ks-learn` key is read, never rewritten.
- Shareable URL state (`design`, `view`, `lens`, `depth`, `focus`, `x`, `step`), validated; back/forward restores.
- Expand (viewport-filling, no Fullscreen API), Exit, Escape, Fit view, zoom; focus and scroll restored.
- Mobile: controls behind "Options", camera frames the active step region, "Whole scene" toggle, inspector below.
- Exports: "Download this view (SVG)" with resolved theme colours and caption; "Print one-pager" via print CSS.
- Text version below the workspace (default path, outcomes, glossary, sources) for no-JS and assistive tech.
- Integration: Learn hero button + atlas band with light/dark preview SVGs; masthead and drawer entries; Method #agentic links; sitemap; search index.
- Corrections on live pages (see VERIFICATION.md).

## Not done in this milestone
- Illustrated coverage for the other Learn-map concepts (see CONTENT_COVERAGE.md). Paused for review by design.
- Field lens and a separate training/evaluation track view.
- Human learning evaluation; screen-reader walkthrough with a real AT user.
- Production deploy (needs Khalid's approval).

## Next steps once the flagship is approved
1. Extract the remaining 30 Learn-map ideas into `content/atlas/concepts.json` (keep their ids; `ks-learn` progress keeps working).
2. Draw each with the same vocabulary: map mark, concept scene, system-scene object.
3. Field lens over the registry; replace the map's text panels with the concept scene.
4. Broaden checks; review sources for every new concept.

## 2026-10-02 · Runtime concepts added to the flagship
Six Learn-map ideas that belong in the running system are now in the scene: system prompt (Instructions slot), prompting (Request slot), tokens (the model's token strip), guardrails and hooks (a pre-call check plate on the tool dock), prompt injection (a planted note in the Orders record, new condition "Plant an instruction in the order record", new outcome "Blocked by a check") and hallucination (the Reply slot, the escalation path and verification). Two new knowledge checks. Four new primary sources, checked 2026-10-02. Coverage: 20 of 44 map ideas.
Next: a second scene, "How a model is made", for the Foundations, Learning and Language ideas; then the Decide ideas.

## 2026-10-02 · Second lesson: How a model is made
New page /learn/atlas/how-models-are-made/ with its own drawing (atlas_scene_model.py) and a declarative scenario. 18 new concepts: AI, machine learning, deep learning, data, bias, algorithm, training, supervised learning, parameters, artificial neuron, neural network, backpropagation, embeddings, attention, transformer, the trained model file, fine-tuning, alignment. Reuses tokens, evaluation, the runtime model and the event trail. Three conditions (skewed data, overfitting, skipped preference stage) and two outcomes (released, held back). Three knowledge checks, including one that ties both lessons together (the released model does not learn in use). Seven new primary sources. Learn-map ideas now link to their drawing. Coverage: 38 of 44 map ideas.
Next: the six Decide ideas (when to use an agent, autonomy ladder, eight gates, SHAMS, data platform, cloud foundations).
