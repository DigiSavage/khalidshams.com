# SHAMS AI Atlas · build brief (milestone 1: flagship lesson)

**Product.** The SHAMS AI Atlas lives inside khalidshams.com at `/learn/atlas/`. Headline: "See what each part does, and how the whole system works."
Thesis: the picture explains the capability, the connections explain the system, the boundaries explain the architecture, SHAMS explains whether it is ready.

**This milestone (per the visual course correction).** One integrated, interactive flagship lesson, "Follow one request through a governed AI system", reviewed before the visual language is multiplied across the library. Library-wide illustration is deliberately paused for review.

**Teaching unit.** Role + action + input + output + limit or consequence. Not one icon per noun.

**Scenario.** Fictional damaged-order case (order A-1042, $84 table lamp, Returns policy v7 §4.2). All records, names, policies and events are synthetic. Deterministic teaching simulation: no model calls, no backend, no telemetry.

**Visual language (Architect's Workshop).** Editorial cutaway of one connected workspace: people (solid figures) outside an application runtime; software behaviour drawn as outline operators with a cobalt badge; bench, bounded context tray, replaceable model engine, tool dock, MCP ports; procedure binder (skills), notes cabinet (memory), policy library (retrieval); authorization gates on the runtime wall; service stations; approver desk; specialist station; budget gauge; hand-off tray; event trail.
Colour states: cobalt = focus / active flow, gold = cost and limits, coral = denial or error. Every state also has a non-colour cue (✓ ✕ ⏸ marks, line style, labels, selection brackets).

**Stack.** Unchanged: Python static build (`build.py`) + vanilla JS + inline SVG, deployed by the existing S3/CloudFront workflow on push to `main`. No framework, no database, no runtime AI, no new dependencies.

**Out of scope for this milestone.** Illustrated coverage of the remaining Learn-map concepts, Field lens, a full-library knowledge-check set, production deploy.
