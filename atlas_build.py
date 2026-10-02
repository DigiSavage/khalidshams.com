"""SHAMS AI Atlas: load, validate and render the atlas from the content registry.

Content lives in content/atlas/ (concepts, sources, checks, scenarios). This module is imported by build.py.
Validation errors stop the build: a broken reference should never reach the site.
"""
from __future__ import annotations
import html, json, re
from pathlib import Path

import atlas_scene

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
    for t in scenario["textEquivalent"]:
        if t not in scenario["steps"]: errs.append(f"textEquivalent: unknown step {t}")
    for ch in checks["checks"]:
        if sum(1 for o in ch["options"] if o["ok"]) != 1: errs.append(f"check {ch['id']}: needs exactly one correct option")
        for c in ch["concepts"]:
            if c not in idset: errs.append(f"check {ch['id']}: unknown concept {c}")
    return errs


DARK = {"#0E1012": "#F1F2F1", "#FFFFFF": "#14171A", "#EFEFEC": "#101315", "#E9E6DE": "#1C2026", "#C6C6BF": "#343B45",
        "#1F45C8": "#8FA6FF", "#E7EBFB": "#161C33", "#B8912F": "#D4AF56", "#F6EED9": "#2A2312", "#3E4449": "#B9C0C5", "#6B737A": "#8E969D", "#59616A": "#9AA2A9"}


def standalone_svg(svg: str, theme: str = "light") -> str:
    """The scene as a file: Picture layer only, no interactive edges. Presentation attributes make it render alone,
    so it never falls back to black fills. The dark file maps each light token to its chosen dark token."""
    s = svg.replace('<svg class="atlas-scene" id="atlas-scene"', '<svg class="atlas-scene"', 1)
    style = ('<style>.arch,.edges,.courier{display:none}.ticks{display:none}</style>')
    bg = "#0D0F11" if theme == "dark" else "#F7F7F5"
    s = s.replace('<defs>', style + f'<rect x="0" y="0" width="1280" height="800" fill="{bg}"/><defs>', 1)
    if theme == "dark":
        for k, v in DARK.items():
            s = s.replace(f'"{k}"', f'"{v}"')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + s


def render(tpl: str, *, masthead: str, footer: str, graph_ids: set[str]) -> tuple[str, str, dict]:
    concepts, sources, checks, scenario = load()
    svg = atlas_scene.scene()
    errs = validate(concepts, sources, checks, scenario, graph_ids, svg)
    if errs:
        raise SystemExit("Atlas content errors:\n  " + "\n  ".join(errs))
    by_id = {c["id"]: c for c in concepts["concepts"]}
    layers = concepts["layers"]
    # rail: concepts grouped under the seven orientation layers (primary teaching location)
    rail = []
    for l in layers:
        items = [c for c in concepts["concepts"] if c["primaryLayer"] == l["id"]]
        if not items: continue
        rail.append(f'<li class="rl-layer"><span class="rl-n">{l["n"]}</span><span class="rl-t">{esc(l["title"])}</span><ul>' +
                    "".join(f'<li><button type="button" class="rl-c" data-c="{c["id"]}"><span>{esc(c["title"])}</span>'
                            f'<i class="rl-k">{esc(c["kind"])}</i></button></li>' for c in items) + '</ul></li>')
    # text equivalent of the default path
    steps = scenario["steps"]
    text_steps = "".join(f'<li><b>{esc(steps[s]["phase"])}.</b> <span class="tx-t">{esc(steps[s]["title"])}.</span> {esc(steps[s]["narration"])}</li>'
                         for s in scenario["textEquivalent"])
    outcomes = "".join(f'<li><b>{esc(o["label"])}.</b> {esc(o["text"])}</li>' for o in scenario["outcomes"].values())
    interventions = "".join(
        f'<li><label class="iv"><input type="checkbox" id="iv-{i["id"]}" data-iv="{i["id"]}"><span><b>{esc(i["label"])}</b>'
        f'<small>{esc(i["help"])}</small></span></label></li>' for i in scenario["interventions"] if not i.get("advanced"))
    interventions_adv = "".join(
        f'<li><label class="iv"><input type="checkbox" id="iv-{i["id"]}" data-iv="{i["id"]}"><span><b>{esc(i["label"])}</b>'
        f'<small>{esc(i["help"])}</small></span></label></li>' for i in scenario["interventions"] if i.get("advanced"))
    glossary = "".join(
        f'<div class="gl-i" id="c-{c["id"]}"><dt>{esc(c["title"])} <span class="gl-l">{esc(next(l["title"] for l in layers if l["id"] == c["primaryLayer"]))}</span></dt>'
        f'<dd>{esc(c["recognize"])} {esc(c["understand"])} <em>Where the analogy stops:</em> {esc(c["metaphorLimit"])}</dd></div>'
        for c in concepts["concepts"])
    srcs = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a>, {esc(s["publisher"])}. Checked {esc(s["checked"])}. {esc(s["supports"])}</li>'
                   for s in sources["sources"])
    data = {"concepts": concepts, "sources": sources, "checks": checks, "scenario": scenario}
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    shams_btns = "".join(f'<button type="button" class="ls-b" data-lens="{m["id"]}" aria-pressed="false" title="{esc(m["reveals"])}"><b>{m["letter"]}</b><span>{esc(m["title"])}</span></button>'
                         for m in concepts["shams"])
    out = (tpl.replace("{{MASTHEAD}}", masthead).replace("{{FOOTER}}", footer)
           .replace("{{SCENE}}", svg).replace("{{RAIL}}", "".join(rail)).replace("{{TEXTSTEPS}}", text_steps)
           .replace("{{OUTCOMES}}", outcomes).replace("{{INTERVENTIONS}}", interventions).replace("{{INTERVENTIONS_ADV}}", interventions_adv)
           .replace("{{GLOSSARY}}", glossary).replace("{{SOURCES}}", srcs).replace("{{SHAMS}}", shams_btns)
           .replace("{{DATA}}", data_json).replace("{{VERSION}}", esc(concepts["version"]))
           .replace("{{NCONCEPTS}}", str(len(concepts["concepts"]))).replace("{{DISCLAIMER}}", esc(scenario["disclaimer"]))
           .replace("{{CASE}}", esc(scenario["case"])))
    stats = {"concepts": len(concepts["concepts"]), "steps": len(steps), "sources": len(sources["sources"]),
             "mapped": sum(1 for c in concepts["concepts"] if c.get("mapId"))}
    return out, {"light": standalone_svg(svg), "dark": standalone_svg(svg, "dark")}, stats
