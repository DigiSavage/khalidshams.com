"""SHAMS AI Atlas: load, validate and render the atlas from the content registry.

Content lives in content/atlas/ (concepts, sources, checks, scenarios). This module is imported by build.py.
Validation errors stop the build: a broken reference should never reach the site.
"""
from __future__ import annotations
import html, json, re
from pathlib import Path

import atlas_scene
import atlas_scene_model

# Each lesson: its scenario file, its drawing and its route. The flagship comes first.
SCENES = [
    {"id": "damaged-order", "file": "damaged-order.json", "draw": atlas_scene.scene, "out": "learn/atlas"},
    {"id": "model-making", "file": "model-making.json", "draw": atlas_scene_model.scene, "out": "learn/atlas/how-models-are-made"},
]

ROOT = Path(__file__).parent
ADIR = ROOT / "content" / "atlas"
REQUIRED = ["id", "title", "aliases", "kind", "primaryLayer", "relatedLayers", "recognize", "understand", "architect",
            "picture", "metaphorLimit", "prerequisites", "example", "failureMode", "boundaryNotes", "shams", "sources", "status"]
STATUSES = {"source-checked", "editorial", "needs-review"}
OUTCOME_KINDS = {"success", "pause", "stop", "error"}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load():
    concepts = json.loads((ADIR / "concepts.json").read_text(encoding="utf-8"))
    sources = json.loads((ADIR / "sources.json").read_text(encoding="utf-8"))
    checks = json.loads((ADIR / "checks.json").read_text(encoding="utf-8"))
    scenario = json.loads((ADIR / "scenarios" / "damaged-order.json").read_text(encoding="utf-8"))
    return concepts, sources, checks, scenario


def load_scenario(sid: str) -> dict:
    meta = next(m for m in SCENES if m["id"] == sid)
    return json.loads((ADIR / "scenarios" / meta["file"]).read_text(encoding="utf-8"))


def walk_plan(nodes, flags: dict) -> list:
    out = []
    for n in nodes:
        if isinstance(n, str): out.append(n)
        else: out += walk_plan(n.get("then", []) if flags.get(n["if"]) else n.get("else", []), flags)
    return out


def validate(concepts, sources, checks, scenario, graph_ids: set[str], svg: str) -> list[str]:
    errs: list[str] = []
    layer_ids = {l["id"] for l in concepts["layers"]}
    shams_ids = {s["id"] for s in concepts["shams"]}
    src_ids = [s["id"] for s in sources["sources"]]
    if len(src_ids) != len(set(src_ids)): errs.append("duplicate source ids")
    for s in sources["sources"]:
        if not s.get("url", "").startswith("https://"): errs.append(f"source {s['id']}: url must be https")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s.get("checked", "")): errs.append(f"source {s['id']}: checked date missing")
    ids = [c["id"] for c in concepts["concepts"]]
    if len(ids) != len(set(ids)): errs.append("duplicate concept ids")
    idset = set(ids)
    for c in concepts["concepts"]:
        for f in REQUIRED:
            if f not in c: errs.append(f"concept {c.get('id')}: missing {f}")
        if c.get("primaryLayer") not in layer_ids: errs.append(f"concept {c['id']}: bad primaryLayer")
        for l in c.get("relatedLayers", []):
            if l not in layer_ids: errs.append(f"concept {c['id']}: bad related layer {l}")
        for m in c.get("shams", []):
            if m not in shams_ids: errs.append(f"concept {c['id']}: bad SHAMS move {m}")
        for s in c.get("sources", []):
            if s not in src_ids: errs.append(f"concept {c['id']}: unknown source {s}")
        for p in c.get("prerequisites", []):
            if p not in idset: errs.append(f"concept {c['id']}: unknown prerequisite {p}")
        if c.get("status") not in STATUSES: errs.append(f"concept {c['id']}: bad status")
        if c.get("status") == "source-checked" and not c.get("sources"): errs.append(f"concept {c['id']}: source-checked without sources")
        if c.get("mapId") and c["mapId"] not in graph_ids: errs.append(f"concept {c['id']}: mapId {c['mapId']} not on the Learn map")
        for f in ("recognize", "understand", "architect", "metaphorLimit"):
            if len(c.get(f, "")) < 20: errs.append(f"concept {c['id']}: {f} too short")
    # scene objects and edges
    objs = set(re.findall(r'data-o="([a-z_]+)"', svg))
    obj_concepts = set(re.findall(r'data-c="([a-z_]+)"', svg))
    edges = set(re.findall(r'data-e="([a-z_]+)"', svg))
    for group in re.findall(r'data-sc="([a-z_ ]+)"', svg):
        for sc_ in group.split():
            if sc_ not in idset: errs.append(f"scene sub-part concept {sc_} not in registry")
    for oc in obj_concepts:
        if oc not in idset: errs.append(f"scene object concept {oc} not in registry")
    slot_ids = {s["id"] for s in scenario["slots"]}
    for sid, st in scenario["steps"].items():
        for o in st.get("focus", []) + [st.get("actor")]:
            if o not in objs: errs.append(f"step {sid}: unknown scene object {o}")
        for e in st.get("edges", []):
            if e not in edges: errs.append(f"step {sid}: unknown edge {e}")
        for k in st.get("load", []):
            if k not in slot_ids: errs.append(f"step {sid}: unknown slot {k}")
        for c in st.get("concepts", []):
            if c not in idset: errs.append(f"step {sid}: unknown concept {c}")
        if st.get("outcome") and st["outcome"] not in scenario["outcomes"]: errs.append(f"step {sid}: unknown outcome")
        for f in ("phase", "title", "narration", "events"):
            if not st.get(f): errs.append(f"step {sid}: missing {f}")
    for k, o in scenario["outcomes"].items():
        if o.get("kind") not in OUTCOME_KINDS: errs.append(f"outcome {k}: bad kind")
    if "plan" in scenario:
        iv = {i["id"] for i in scenario["interventions"]}
        def check_nodes(nodes):
            for n in nodes:
                if isinstance(n, str):
                    if n not in scenario["steps"]: errs.append(f"plan: unknown step {n}")
                else:
                    if n.get("if") not in iv: errs.append(f"plan: unknown condition {n.get('if')}")
                    check_nodes(n.get("then", [])); check_nodes(n.get("else", []))
        check_nodes(scenario["plan"])
        from itertools import product
        for combo in product([False, True], repeat=len(iv)):
            ids = walk_plan(scenario["plan"], dict(zip(sorted(iv), combo)))
            ends = [i for i in ids if scenario["steps"].get(i, {}).get("outcome")]
            if not ends: errs.append(f"plan: a condition set ends without an outcome ({dict(zip(sorted(iv), combo))})")
    for t in scenario["textEquivalent"]:
        if t not in scenario["steps"]: errs.append(f"textEquivalent: unknown step {t}")
    for ch in checks["checks"]:
        if sum(1 for o in ch["options"] if o["ok"]) != 1: errs.append(f"check {ch['id']}: needs exactly one correct option")
        for c in ch["concepts"]:
            if c not in idset: errs.append(f"check {ch['id']}: unknown concept {c}")
        if ch.get("scene", "damaged-order") not in {m["id"] for m in SCENES}: errs.append(f"check {ch['id']}: unknown scene")
    return errs


DARK = {"#0E1012": "#F1F2F1", "#FFFFFF": "#14171A", "#EFEFEC": "#101315", "#E9E6DE": "#1C2026", "#C6C6BF": "#343B45",
        "#1F45C8": "#8FA6FF", "#E7EBFB": "#161C33", "#B8912F": "#D4AF56", "#F6EED9": "#2A2312", "#3E4449": "#B9C0C5", "#6B737A": "#8E969D", "#59616A": "#9AA2A9"}


def standalone_svg(svg: str, theme: str = "light") -> str:
    """The scene as a file: Picture layer only, no interactive edges. Presentation attributes make it render alone,
    so it never falls back to black fills. The dark file maps each light token to its chosen dark token."""
    s = svg.replace('<svg class="atlas-scene" id="atlas-scene"', '<svg class="atlas-scene"', 1)
    style = ('<style>.arch,.edges,.courier,.inj-note,.bars-skew,.ho-bad{display:none}.ticks{display:none}</style>')
    bg = "#0D0F11" if theme == "dark" else "#F7F7F5"
    s = s.replace('<defs>', style + f'<rect x="0" y="0" width="1280" height="800" fill="{bg}"/><defs>', 1)
    if theme == "dark":
        for k, v in DARK.items():
            s = s.replace(f'"{k}"', f'"{v}"')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + s


LEGENDS = {
    "runtime": [
        ('<svg width="44" height="10" aria-hidden="true"><path d="M2 5H40" stroke="currentColor" stroke-width="2.2"/><circle cx="40" cy="5" r="3.5" fill="currentColor"/></svg>', "<b>Information moves</b> (data, evidence, results)"),
        ('<svg width="44" height="10" aria-hidden="true" class="lg-ctrl"><path d="M2 5H36" stroke="currentColor" stroke-width="2.2" stroke-dasharray="8 5"/><path d="M34 1L42 5L34 9z" fill="currentColor"/></svg>', "<b>Control</b> (a proposal, call or work order)"),
        ('<svg width="44" height="10" aria-hidden="true" class="lg-ctrl"><path d="M2 5H40" stroke="currentColor" stroke-width="2.2" stroke-dasharray="2 4"/></svg>', "<b>Approval route</b> to a person"),
        ('<svg width="44" height="10" aria-hidden="true" class="lg-own"><path d="M2 5H40" stroke="currentColor" stroke-width="2" stroke-dasharray="2 5"/></svg>', "<b>Ownership</b>, not a runtime call"),
        ('<span class="lg-sym">&#10003; &#10005; &#9208;</span>', "<b>Decisions</b> at the check plate and the gates: allowed, refused, waiting for approval"),
        ("PEOPLE", "<b>Solid figures are people.</b> Outline figures are software behaviour drawn as operators; they do not understand or intend anything."),
        ('<span class="lg-sym">&#9671;</span>', "<b>Learn first</b> links appear in the inspector, never as runtime arrows."),
    ],
    "training": [
        ('<svg width="44" height="10" aria-hidden="true"><path d="M2 5H40" stroke="currentColor" stroke-width="2.2"/><circle cx="40" cy="5" r="3.5" fill="currentColor"/></svg>', "<b>Data moves</b> (text, tokens, vectors, checkpoints)"),
        ('<svg width="44" height="10" aria-hidden="true" class="lg-ctrl"><path d="M2 5H36" stroke="currentColor" stroke-width="2.2" stroke-dasharray="8 5"/><path d="M34 1L42 5L34 9z" fill="currentColor"/></svg>', "<b>Control</b> (adjusting parameters, sending work back)"),
        ('<span class="lg-sym">&#10003; &#10005;</span>', "<b>Evaluation results</b>: criterion met, criterion failed"),
        ("PEOPLE", "<b>Solid figures are people</b>: raters and the release owner. Nothing else in this drawing understands or intends anything."),
        ('<span class="lg-sym">&#9671;</span>', "<b>Learn first</b> links appear in the inspector, never as arrows in the drawing."),
    ],
}
PEOPLE_SYM = ('<span class="lg-sym"><svg width="14" height="20" aria-hidden="true"><circle cx="7" cy="5" r="4.5" fill="currentColor"/><path d="M1 20V13Q1 9 7 9Q13 9 13 13V20Z" fill="currentColor"/></svg> '
              '<svg width="14" height="20" aria-hidden="true"><circle cx="7" cy="5" r="4.5" fill="none" stroke="currentColor"/><path d="M1 20Q1 11 7 11Q13 11 13 20" fill="none" stroke="currentColor"/></svg></span>')
DESIGN_SEG = ('<div class="tb-g"><span class="tb-l" id="lbl-design">Design</span><div class="seg" role="group" aria-labelledby="lbl-design">'
              '<button type="button" class="seg-b" data-design="single" aria-pressed="true">One agent</button>'
              '<button type="button" class="seg-b" data-design="team" aria-pressed="false">Coordinator + specialist</button></div></div>')


def scene_concepts(svg: str, scenario: dict) -> list[str]:
    ids = re.findall(r'data-c="([a-z_]+)"', svg)
    for g in re.findall(r'data-sc="([a-z_ ]+)"', svg): ids += g.split()
    for st in scenario["steps"].values(): ids += st.get("concepts", [])
    seen = []
    for i in ids:
        if i not in seen: seen.append(i)
    return seen


def render_scene(sid: str, tpl: str, *, masthead: str, footer: str, graph_ids: set[str], extra: dict | None = None):
    concepts, sources, checks, _ = load()
    scenario = load_scenario(sid)
    meta = next(m for m in SCENES if m["id"] == sid)
    svg = meta["draw"]()
    errs = validate(concepts, sources, checks, scenario, graph_ids, svg)
    if errs:
        raise SystemExit(f"Atlas content errors ({sid}):\n  " + "\n  ".join(errs))
    pg = scenario["page"]
    here = scene_concepts(svg, scenario)
    by_id = {c["id"]: c for c in concepts["concepts"]}
    layers = concepts["layers"]
    # the other lessons, for cross-links ("also drawn in")
    scenes = []
    for m in SCENES:
        sc_m = load_scenario(m["id"])
        scenes.append({"id": m["id"], "title": sc_m["title"], "route": sc_m["page"]["route"], "concepts": scene_concepts(m["draw"](), sc_m)})
    rail = []
    for l in layers:
        items = [by_id[i] for i in here if by_id[i]["primaryLayer"] == l["id"]]
        if not items: continue
        rail.append(f'<li class="rl-layer"><span class="rl-n">{l["n"]}</span><span class="rl-t">{esc(l["title"])}</span><ul>' +
                    "".join(f'<li><button type="button" class="rl-c" data-c="{c["id"]}"><span>{esc(c["title"])}</span>'
                            f'<i class="rl-k">{esc(c["kind"])}</i></button></li>' for c in items) + '</ul></li>')
    steps = scenario["steps"]
    text_steps = "".join(f'<li><b>{esc(steps[s]["phase"])}.</b> <span class="tx-t">{esc(steps[s]["title"])}.</span> {esc(steps[s]["narration"])}</li>'
                         for s in scenario["textEquivalent"])
    outcomes = "".join(f'<li><b>{esc(o["label"])}.</b> {esc(o["text"])}</li>' for o in scenario["outcomes"].values())
    def ivs(adv):
        return "".join(f'<li><label class="iv"><input type="checkbox" id="iv-{i["id"]}" data-iv="{i["id"]}"><span><b>{esc(i["label"])}</b>'
                       f'<small>{esc(i["help"])}</small></span></label></li>' for i in scenario["interventions"] if bool(i.get("advanced")) == adv)
    adv = ivs(True)
    glossary = "".join(
        f'<div class="gl-i" id="c-{c["id"]}"><dt>{esc(c["title"])} <span class="gl-l">{esc(next(l["title"] for l in layers if l["id"] == c["primaryLayer"]))}</span></dt>'
        f'<dd>{esc(c["recognize"])} {esc(c["understand"])} <em>Where the analogy stops:</em> {esc(c["metaphorLimit"])}</dd></div>'
        for c in (by_id[i] for i in here))
    used_src = []
    for i in here:
        for sref in by_id[i]["sources"]:
            if sref not in used_src: used_src.append(sref)
    srcs = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a>, {esc(s["publisher"])}. Checked {esc(s["checked"])}. {esc(s["supports"])}</li>'
                   for s in sources["sources"] if s["id"] in used_src)
    my_checks = {"version": checks["version"], "checks": [k for k in checks["checks"] if k.get("scene", "damaged-order") == sid]}
    data = {"concepts": concepts, "sources": sources, "checks": my_checks, "scenario": scenario, "scenes": scenes, "here": sid}
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    shams_btns = "".join(f'<button type="button" class="ls-b" data-lens="{m["id"]}" aria-pressed="false" title="{esc(m["reveals"])}"><b>{m["letter"]}</b><span>{esc(m["title"])}</span></button>'
                         for m in concepts["shams"])
    legend = "".join(f'<li>{PEOPLE_SYM if sym == "PEOPLE" else sym}<span>{txt}</span></li>' for sym, txt in LEGENDS[pg["legend"]])
    others = " ".join(f'<a href="{esc(m["route"])}">{esc(m["title"])}</a>' for m in scenes if m["id"] != sid)
    rep = {"MASTHEAD": masthead, "FOOTER": footer, "SCENE": svg, "RAIL": "".join(rail), "TEXTSTEPS": text_steps, "OUTCOMES": outcomes,
           "INTERVENTIONS": ivs(False), "INTERVENTIONS_ADV": (f'<details class="iv-more"><summary>More conditions</summary><ul class="iv-list">{adv}</ul></details>' if adv else ""),
           "GLOSSARY": glossary, "SOURCES": srcs, "SHAMS": shams_btns, "DATA": data_json, "VERSION": esc(concepts["version"]),
           "NCONCEPTS": str(len(here)), "DISCLAIMER": esc(scenario["disclaimer"]), "CASE": esc(scenario["case"]),
           "CRUMB": esc(pg["crumb"]), "H1": esc(pg["h1"]), "H1EM": esc(pg["h1em"]), "LABEL": esc(pg["label"]), "FOLLOW": esc(pg["follow"]),
           "READY": esc(pg["ready"]), "INTRO": esc(pg["intro"]), "DESIGNSEG": DESIGN_SEG if pg["designs"] else "", "LEGEND": legend,
           "OUTCOMESINTRO": esc(pg["outcomesIntro"]), "OTHERS": others, "SCENETITLE": esc(scenario["title"])}
    rep.update(extra or {})
    out = tpl
    for k, v in rep.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left: raise SystemExit(f"atlas template placeholders left unfilled: {left}")
    stats = {"concepts": len(here), "steps": len(steps), "sources": len(used_src),
             "mapped": sum(1 for i in here if by_id[i].get("mapId")), "registry": len(concepts["concepts"])}
    return out, {"light": standalone_svg(svg), "dark": standalone_svg(svg, "dark")}, stats


def render(tpl: str, *, masthead: str, footer: str, graph_ids: set[str]):
    """The flagship lesson (kept for callers that predate the second scene)."""
    return render_scene("damaged-order", tpl, masthead=masthead, footer=footer, graph_ids=graph_ids)
