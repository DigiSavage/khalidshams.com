"""Learn structure: guided paths, one page per map idea, the architect route and the page navigation.

Content lives in content/learn/{graph,paths,routes}.json. Validation errors stop the build. Imported by build.py.
"""
from __future__ import annotations
import html, json, re
from pathlib import Path

from vignettes import vignette, SCENES

ROOT = Path(__file__).parent
LDIR = ROOT / "content" / "learn"
DEPTHS = [("plain", "In one line"), ("picture", "Picture it"), ("deep", "Under the hood")]
PATH_ART = {"what-is-ai": "Foundations", "how-machines-learn": "Learning", "what-a-model-does": "Language", "what-makes-an-agent": "Agents", "running-it-safely": "Operate", "should-we-build-one": "Decide"}


def esc(s) -> str: return html.escape(str(s), quote=True)


def load():
    g = json.loads((LDIR / "graph.json").read_text(encoding="utf-8"))
    p = json.loads((LDIR / "paths.json").read_text(encoding="utf-8"))
    r = json.loads((LDIR / "routes.json").read_text(encoding="utf-8"))
    return g, p, r


def stop_key(st: dict) -> str:
    if "idea" in st: return "idea:" + st["idea"]
    if "atlas" in st: return "atlas:" + st["done"]
    return st["key"]


def validate_scenes(scenes: dict) -> list[str]:
    """The five primary homes: every scene names a real vignette and an internal route."""
    import re as _re
    errs = []
    ids = [x["id"] for x in scenes["scenes"]]
    if len(ids) != len(set(ids)): errs.append("scenes: duplicate id")
    for x in scenes["scenes"]:
        for f in ("line", "purpose", "primary", "cast", "art", "study"):
            if f not in x: errs.append(f"scene {x['id']}: missing {f}")
        if not x["primary"]["route"].startswith("/"): errs.append(f"scene {x['id']}: primary route must be internal")
        for c in x["cast"]:
            if c not in scenes["cast"]: errs.append(f"scene {x['id']}: unknown cast {c}")
        for o in x.get("objects", []):
            if o not in scenes["objects"]: errs.append(f"scene {x['id']}: unknown object {o}")
        for v in _re.findall(r"\{\{VIG:([A-Za-z-]+)\}\}", x["primary"]["component"]):
            if v not in SCENES: errs.append(f"scene {x['id']}: vignette {v} does not exist")
    return errs


def validate(g, p, r, atlas_concepts: set[str], dist_exists) -> list[str]:
    errs = []
    ids = {i["id"] for i in g["ideas"]}
    seen_ids = set()
    for path in p["paths"]:
        if path["id"] in seen_ids: errs.append(f"path {path['id']}: duplicate id")
        seen_ids.add(path["id"])
        for f in ("title", "promise", "minutes", "stops", "n"):
            if f not in path: errs.append(f"path {path['id']}: missing {f}")
        keys = set()
        for st in path["stops"]:
            if "idea" in st and st["idea"] not in ids: errs.append(f"path {path['id']}: unknown idea {st['idea']}")
            if "atlas" in st and not (st.get("done") and st.get("label")): errs.append(f"path {path['id']}: atlas stop needs done and label")
            if "section" in st and not (st.get("key") and st.get("label")): errs.append(f"path {path['id']}: section stop needs key and label")
            if not any(k in st for k in ("idea", "atlas", "section")): errs.append(f"path {path['id']}: stop without a target")
            k = stop_key(st)
            if k in keys: errs.append(f"path {path['id']}: repeated stop {k}")
            keys.add(k)
    for d in p["doors"]:
        if d["id"] != "new" and not d.get("href"): errs.append(f"door {d['id']}: missing href")
    sids = set()
    for s in r["situations"]:
        if s["id"] in sids: errs.append(f"situation {s['id']}: duplicate")
        sids.add(s["id"])
        if not re.fullmatch(r"[0-4]", str(s.get("rung", ""))): errs.append(f"situation {s['id']}: rung must be 0 to 4")
        for gid in s.get("gates", []):
            if not re.fullmatch(r"g[1-8]", gid): errs.append(f"situation {s['id']}: bad gate {gid}")
        kinds = [x["kind"] for x in s["steps"]]
        for x in s["steps"]:
            if x["kind"] not in r["kinds"]: errs.append(f"situation {s['id']}: bad kind {x['kind']}")
            if not x["href"].startswith("/"): errs.append(f"situation {s['id']}: href must be internal: {x['href']}")
        if "example" not in kinds: errs.append(f"situation {s['id']}: needs a worked example")
    for q in r["brief"]["questions"]:
        for gid in q["yes_adds"].get("gates", []):
            if not re.fullmatch(r"g[1-8]", gid): errs.append(f"brief {q['id']}: bad gate {gid}")
    return errs


# ------------------------------------------------------------------ helpers shared by templates
def idea_href(i: dict) -> str: return f"/learn/ideas/{i['id']}/"


def path_of_idea(p, idea_id: str):
    for path in p["paths"]:
        for n, st in enumerate(path["stops"]):
            if st.get("idea") == idea_id: return path, n
    return None, None


def stop_view(st: dict, by_id: dict) -> dict:
    """What a stop looks like in a list: href, label, sub, kind, key."""
    if "idea" in st:
        i = by_id[st["idea"]]
        return {"href": idea_href(i), "label": i["label"], "sub": i["plain"], "kind": "idea", "key": stop_key(st)}
    if "atlas" in st:
        return {"href": st["atlas"], "label": st["label"], "sub": st.get("sub", ""), "kind": "atlas", "key": stop_key(st)}
    return {"href": st["section"], "label": st["label"], "sub": st.get("sub", ""), "kind": "section", "key": stop_key(st)}


def stops_html(path: dict, by_id: dict, current: str | None = None) -> str:
    out = []
    for n, st in enumerate(path["stops"]):
        v = stop_view(st, by_id)
        href = v["href"] + ("&" if "?" in v["href"] else "?") + "path=" + path["id"] if v["kind"] != "section" else v["href"]
        cur = ' aria-current="step"' if current == v["key"] else ""
        out.append(f'<li class="ps" data-key="{esc(v["key"])}" data-kind="{v["kind"]}"{cur}><span class="ps-n">{n + 1}</span>'
                   f'<a class="ps-a" href="{esc(href)}"><b>{esc(v["label"])}</b><small>{esc(v["sub"])}</small></a>'
                   f'<span class="ps-k">{ {"idea": "idea", "atlas": "atlas lesson", "section": "section"}[v["kind"]] }</span><span class="ps-st" aria-hidden="true"></span></li>')
    return '<ol class="path-stops">' + "".join(out) + "</ol>"


def paths_json(p, by_id) -> str:
    """The compact form the browser needs for progress: stop keys per path."""
    data = {"paths": [{"id": x["id"], "n": x["n"], "title": x["title"], "href": f"/learn/paths/{x['id']}/",
                       "stops": [dict(stop_view(st, by_id), key=stop_key(st)) for st in x["stops"]]} for x in p["paths"]]}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def page_nav(body: str) -> str:
    """A sticky section list built from the page's own bands: id + the section label."""
    items = []
    for m in re.finditer(r'<div class="band[^"]*" id="([a-z0-9-]+)">.*?<p class="sec-label">([^<]+)</p>', body, flags=re.S):
        sid, label = m.group(1), " ".join(m.group(2).split())
        if sid not in [i[0] for i in items]: items.append((sid, label))
    if len(items) < 3: return ""
    return ('<nav class="pagenav" aria-label="On this page"><div class="wrap pagenav-row"><span class="pagenav-l">On this page</span>' +
            "".join(f'<a href="#{sid}">{esc(label)}</a>' for sid, label in items) + "</div></nav>")


# ------------------------------------------------------------------ renderers
def render_doors(p, by_id, compact=False) -> str:
    paths = p["paths"]
    first = paths[0]
    cards = []
    for d in p["doors"]:
        if d["id"] == "new":
            lst = "".join(f'<li data-path="{x["id"]}"><a href="/learn/paths/{x["id"]}/"><span class="dp-n">{x["n"]}</span><span class="dp-t">{esc(x["title"])}</span>'
                          f'<span class="dp-m">{x["minutes"]} min</span><span class="dp-bar"><i></i></span></a></li>' for x in paths)
            body = (f'<ol class="door-paths">{lst}</ol>' if not compact else "") + \
                   f'<p class="door-cta"><a class="btn solid" id="door-continue" href="/learn/paths/{first["id"]}/">{esc(d["cta"])}</a> <span class="door-prog" id="door-prog"></span></p>'
        else:
            body = f'<p class="door-cta"><a class="btn" href="{esc(d["href"])}">{esc(d["cta"])}</a></p>'
        cards.append(f'<div class="door door-{d["id"]}">{vignette("door-" + d["id"], "door-art")}<p class="sec-label">{ {"new": "Door 1", "architect": "Door 2", "explore": "Door 3"}[d["id"]] }</p>'
                     f'<h3>{esc(d["title"])}</h3><p class="door-sub">{esc(d["sub"])}</p>{body}</div>')
    return '<div class="doors">' + "".join(cards) + "</div>"


def render_path(tpl: str, path: dict, p, by_id, *, masthead, footer) -> str:
    total = len(path["stops"]); ideas = sum(1 for s in path["stops"] if "idea" in s)
    nxt = next((x for x in p["paths"] if x["n"] == path["n"] + 1), None)
    prv = next((x for x in p["paths"] if x["n"] == path["n"] - 1), None)
    nav = ((f'<a class="btn" href="/learn/paths/{prv["id"]}/">&#8592; Path {prv["n"]}</a> ' if prv else "") +
           (f'<a class="btn" href="/learn/paths/{nxt["id"]}/">Path {nxt["n"]}: {esc(nxt["title"])} &#8594;</a>' if nxt else '<a class="btn" href="/architect/">Next: choose a situation &#8594;</a>'))
    first = stop_view(path["stops"][0], by_id)
    first_href = first["href"] + ("&" if "?" in first["href"] else "?") + "path=" + path["id"] if first["kind"] != "section" else first["href"]
    return fill(tpl, MASTHEAD=masthead, FOOTER=footer, N=str(path["n"]), TITLE=esc(path["title"]), PROMISE=esc(path["promise"]),
                MINUTES=str(path["minutes"]), TOTAL=str(total), ART=vignette(PATH_ART.get(path["id"], "door-new"), "hero-art"), IDEAS=str(ideas), STOPS=stops_html(path, by_id), PATHID=path["id"],
                FIRST=esc(first_href), NAV=nav, PATHSJSON=paths_json(p, by_id))


def render_idea(tpl: str, i: dict, g, p, by_id, atlas_where: dict, *, masthead, footer) -> str:
    edges = g["edges"]
    frm = [by_id[a] for a, b in edges if b == i["id"] and a in by_id]
    to = [by_id[b] for a, b in edges if a == i["id"] and b in by_id]
    chips = lambda xs: "".join(f'<a class="chip" href="{idea_href(x)}">{esc(x["label"])}</a>' for x in xs) or '<span class="chip chip-none">none</span>'
    depths = "".join(f'<div class="idea-depth"><p class="sec-label">{lab}</p><p>{esc(i[k])}</p></div>' for k, lab in DEPTHS)
    path, n = path_of_idea(p, i["id"])
    on_path = ""
    if path:
        on_path = (f'<p class="sec-label">On a guided path</p><p class="idea-path"><a href="/learn/paths/{path["id"]}/">Path {path["n"]}: {esc(path["title"])}</a>, stop {n + 1} of {len(path["stops"])}.</p>')
    drawn = atlas_where.get(i["id"])
    see = (f'<a class="btn" href="{esc(drawn["href"])}">See it drawn: {esc(drawn["title"])}</a>' if drawn else "")
    deeper = f'<a class="btn" href="{esc(i["link"]["href"])}">{esc(i["link"]["label"])}</a>' if i.get("link") and not i["link"]["href"].startswith("/learn/atlas/") else ""
    idx = [x["id"] for x in g["ideas"]].index(i["id"]) + 1
    return fill(tpl, MASTHEAD=masthead, FOOTER=footer, ID=i["id"], LABEL=esc(i["label"]), CLUSTER=esc(i["cluster"]), IDX=str(idx), NIDEAS=str(len(g["ideas"])),
                PLAIN=esc(i["plain"]), DEPTHS=depths, ART=vignette(i["cluster"], "hero-art"), FROM=chips(frm), TO=chips(to), ONPATH=on_path, SEE=see, DEEPER=deeper, PATHSJSON=paths_json(p, by_id))


def render_architect(tpl: str, r, p, by_id, *, masthead, footer) -> str:
    cards = []
    for s in r["situations"]:
        steps = "".join(f'<li class="rt-step rt-{x["kind"]}"><span class="rt-k">{esc(r["kinds"][x["kind"]])}</span><a href="{esc(x["href"])}">{esc(x["label"])}</a><small>{esc(x["why"])}</small></li>' for x in s["steps"])
        gates = " ".join(f'<a class="chip" href="/method/#{gid}">Gate {gid[1:].zfill(2)}</a>' for gid in s["gates"])
        art = vignette(s["id"], "route-art") if s["id"] in SCENES else ""
        cards.append(f'<article class="route" id="{s["id"]}">{art}<div class="route-head"><h3>{esc(s["title"])}</h3><p class="route-when">{esc(s["when"])}</p>'
                     f'<p class="route-meta"><span class="chip chip-b">Rung {s["rung"]} on the ladder</span> {gates}</p></div><ol class="rt-steps">{steps}</ol></article>')
    qs = "".join(f'<fieldset class="bq" data-q="{q["id"]}"><legend>{esc(q["q"])}</legend>'
                 f'<label><input type="radio" name="{q["id"]}" value="yes"> {esc(q["yes"])}</label><label><input type="radio" name="{q["id"]}" value="no" checked> {esc(q["no"])}</label></fieldset>'
                 for q in r["brief"]["questions"])
    sit_opts = "".join(f'<option value="{s["id"]}">{esc(s["title"])}</option>' for s in r["situations"])
    data = json.dumps({"situations": r["situations"], "brief": r["brief"], "kinds": r["kinds"]}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return fill(tpl, MASTHEAD=masthead, FOOTER=footer, INTRO=esc(r["intro"]), ROUTES="".join(cards), QUESTIONS=qs, SITOPTS=sit_opts,
                BRIEFINTRO=esc(r["brief"]["intro"]), ROUTESJSON=data, NSIT=str(len(r["situations"])))


def fill(s: str, **kw) -> str:
    for k, v in kw.items(): s = s.replace("{{" + k + "}}", v)
    left = [x for x in re.findall(r"\{\{[A-Z_]+\}\}", s) if x != "{{PAGENAV}}"]   # PAGENAV is filled from the finished body
    if left: raise SystemExit(f"learn template placeholders left unfilled: {left}")
    return s
