#!/usr/bin/env python3
"""
Static site generator for khalidshams.com.

  content/posts/YYYY-MM-DD-slug.md  ->  dist/writing/<slug>/index.html
  templates/home.html               ->  dist/index.html   (with Writing section)
                                        dist/writing/index.html
                                        dist/feed.xml, dist/sitemap.xml, dist/robots.txt

A post is visible when its date has arrived (America/Phoenix) and its
status is `approved` or `published`. Drafts never render, even if dated.
"""
from __future__ import annotations
import html, json, re, shutil, sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import markdown  # pip install markdown
import atlas_build
import learn_build
import vignettes

ROOT = Path(__file__).parent
SITE = "https://khalidshams.com"
TZ = timezone(timedelta(hours=-7))          # America/Phoenix: no DST
DIST, POSTS, TPL = ROOT / "dist", ROOT / "content" / "posts", ROOT / "templates"
HOME_LIMIT = 6
VISIBLE = {"approved", "published"}

MD = markdown.Markdown(extensions=["smarty", "sane_lists"], output_format="html5")
MD_PB = markdown.Markdown(extensions=["smarty", "sane_lists", "toc"],
                          extension_configs={"toc": {"toc_depth": "2", "permalink": False}}, output_format="html5")
PLAYBOOKS = ROOT / "content" / "playbooks"

# Tools: one template per tool in templates/tools/<slug>.html, rendered to /tools/<slug>/.
# Order here is the order on /tools/ and the number shown on each page.
TOOLS = [
    {"slug": "availability", "title": "Availability and recovery budget",
     "kicker": "Multiply the chain, then time the restore",
     "summary": "Composite availability from your hard and soft dependencies, the downtime it allows, and a recovery time built from restore steps someone actually timed.",
     "chips": ["Composite SLA", "Downtime budget", "RTO", "RPO"],
     "description": "A calculator for the availability you can actually promise: multiply every hard dependency, see where the downtime comes from and which change buys the most back, then build the recovery time from restore steps and check it against the RTO and RPO."},
]


@dataclass
class Post:
    slug: str
    title: str
    date: date
    status: str
    tag: str
    summary: str
    linkedin_url: str
    body_md: str
    path: Path
    body_html: str = field(default="", init=False)

    @property
    def image(self) -> "Path | None":
        img = ROOT / "content" / "images" / f"{self.slug}.png"
        return img if img.exists() else None
    @property
    def image_url(self) -> str:
        return f"{SITE}/images/{self.slug}.png" if self.image else f"{SITE}/og.png"

    @property
    def url(self) -> str: return f"/writing/{self.slug}/"
    @property
    def abs_url(self) -> str: return SITE + self.url
    @property
    def date_long(self) -> str: return self.date.strftime("%B %-d, %Y")
    @property
    def date_iso(self) -> str: return self.date.isoformat()
    @property
    def tag_label(self) -> str: return self.tag.replace("-", " ")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("missing frontmatter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] == '"':
            v = v[1:-1].replace('\\"', '"')
        meta[k.strip()] = v
    return meta, m.group(2).strip()


def load_posts() -> list[Post]:
    posts = []
    for p in sorted(POSTS.glob("*.md")):
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", p.name)
        if not m:
            print(f"skip (bad filename): {p.name}", file=sys.stderr); continue
        posts.append(Post(
            slug=m.group(2),
            title=meta.get("title", m.group(2)),
            date=date.fromisoformat(meta.get("date", m.group(1))),
            status=meta.get("status", "draft").lower(),
            tag=meta.get("tag", "notes"),
            summary=meta.get("summary", ""),
            linkedin_url=meta.get("linkedin_url", "").strip(),
            body_md=body, path=p))
    return posts


@dataclass
class Playbook:
    slug: str
    num: int
    title: str
    kicker: str
    summary: str
    stack: list[str]
    body_md: str
    body_html: str = ""
    toc: list[tuple[str, str]] = field(default_factory=list)

    @property
    def url(self) -> str: return f"/playbooks/{self.slug}/"
    @property
    def abs_url(self) -> str: return SITE + self.url
    @property
    def nn(self) -> str: return f"{self.num:02d}"


def load_playbooks() -> list[Playbook]:
    out = []
    if not PLAYBOOKS.exists():
        return out
    for p in sorted(PLAYBOOKS.glob("*.md")):
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        m = re.match(r"(\d+)-(.+)\.md$", p.name)
        if not m:
            print(f"skip (bad playbook filename): {p.name}", file=sys.stderr); continue
        out.append(Playbook(
            slug=m.group(2), num=int(meta.get("order", m.group(1))),
            title=meta.get("title", m.group(2)), kicker=meta.get("kicker", ""),
            summary=meta.get("summary", ""),
            stack=[t.strip() for t in meta.get("stack", "").split("·") if t.strip()],
            body_md=body))
    return sorted(out, key=lambda x: x.num)


def render_playbook_md(pb: Playbook) -> None:
    MD_PB.reset()
    pb.body_html = MD_PB.convert(pb.body_md)
    pb.toc = [(t["id"], t["name"]) for t in MD_PB.toc_tokens]


def today_phx() -> date:
    """Today in Phoenix. Override with BUILD_DATE=YYYY-MM-DD to preview a future build."""
    import os
    if os.environ.get("BUILD_DATE"):
        return date.fromisoformat(os.environ["BUILD_DATE"])
    return datetime.now(TZ).date()


def visible(posts: list[Post]) -> list[Post]:
    t = today_phx()
    out = [p for p in posts if p.status in VISIBLE and p.date <= t]
    return sorted(out, key=lambda p: p.date, reverse=True)


def render_md(p: Post) -> str:
    MD.reset()
    return MD.convert(p.body_md)


def num_words(n: int) -> str:
    """Small cardinal in words (0-99), so counts in prose come from the data."""
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
    if n < 20: return ones[n]
    t, o = divmod(n, 10)
    return tens[t] + ("" if o == 0 else "-" + ones[o])


def tpl(name: str) -> str:
    return (TPL / name).read_text(encoding="utf-8")


def fill(s: str, **kw) -> str:
    for k, v in kw.items():
        s = s.replace("{{" + k + "}}", v)
    return re.sub(r"\{\{VIG:([A-Za-z-]+)\}\}", lambda m: vignettes.vignette(m.group(1), "three-vig"), s)


def page(body: str, *, title: str, description: str, canonical: str, og_type="website", og_image=None) -> str:
    return fill(tpl("base.html"), BODY=body, TITLE=html.escape(title, quote=True),
                DESCRIPTION=html.escape(description, quote=True), CANONICAL=canonical, OG_TYPE=og_type,
                OG_IMAGE=og_image or f"{SITE}/og.png")


def esc(s: str) -> str: return html.escape(s, quote=True)



def build_search_index(pages, graph, posts):
    """Walk rendered pages and emit one entry per heading-delimited section (plus map ideas and posts)."""
    from html.parser import HTMLParser

    class Walker(HTMLParser):
        SKIP = {"script", "style", "header", "footer", "nav", "svg", "select", "button", "option", "title"}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.skip = 0; self.stack = []; self.sections = []; self.cur = None; self.h1 = ""; self.in_h1 = False
            self.in_head = None; self.head_buf = ""
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            cls = a.get("class", "") or ""
            VOID = {"img", "br", "hr", "meta", "link", "input", "source", "wbr"}
            sk = tag in self.SKIP or a.get("id") == "drawer"
            if sk: self.skip += 1
            if tag not in VOID: self.stack.append((tag, a.get("id"), sk))
            if self.skip: return
            if tag == "h1": self.in_h1 = True
            if tag in ("h2", "h3", "summary"):
                anchor = a.get("id") or self._nearest_id()
                self.cur = {"t": "", "a": anchor or "", "s": "", "lvl": tag}; self.sections.append(self.cur); self.in_head = tag; self.head_buf = ""
        def _nearest_id(self):
            for tag, i, _ in reversed(self.stack):
                if i: return i
            return None
        def handle_endtag(self, tag):
            for k in range(len(self.stack) - 1, -1, -1):
                if self.stack[k][0] == tag:
                    for item in self.stack[k:]:
                        if item[2]: self.skip = max(0, self.skip - 1)
                    del self.stack[k:]; break
            if tag == "h1": self.in_h1 = False
            if tag == self.in_head:
                self.cur["t"] = " ".join(self.head_buf.split()); self.in_head = None
        def handle_data(self, data):
            if self.skip: return
            if self.in_h1: self.h1 += data
            if self.in_head: self.head_buf += data
            elif self.cur is not None: self.cur["s"] += data + " "
            elif not self.sections and data.strip():
                self.cur = {"t": "", "a": "", "s": data + " "}; self.sections.append(self.cur)
    out = []
    for url, path in pages:
        w = Walker(); w.feed(path.read_text(encoding="utf-8"))
        page = " ".join(w.h1.split()) or url
        last_h2 = ""
        for sec in w.sections:
            text = " ".join(sec["s"].split())
            if sec.get("lvl") == "h2": last_h2 = sec["t"]
            if not text and not sec["t"]: continue
            entry = {"u": url + ("#" + sec["a"] if sec["a"] else ""), "p": page, "t": sec["t"] or page, "s": text[:420], "k": "section"}
            if sec.get("lvl") in ("h3", "summary") and last_h2 and last_h2 != sec["t"]: entry["x"] = last_h2[:90]
            out.append(entry)
    if graph:
        for i in graph["ideas"]:
            out.append({"u": f"/learn/ideas/{i['id']}/", "p": "Learn AI", "t": i["label"], "s": i["plain"] + " " + i["picture"] + " " + i["deep"], "k": "idea", "c": i["cluster"]})
    for p in posts:
        body = re.sub(r"<[^>]+>", " ", p.body_html or "")
        out.append({"u": p.url, "p": "Writing", "t": p.title, "s": " ".join((p.summary + " " + body).split())[:600], "k": "post", "d": p.date_long})
    return out


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    static = ROOT / "static"
    if static.exists():
        shutil.copytree(static, DIST, dirs_exist_ok=True)
    images = ROOT / "content" / "images"
    if images.exists():
        shutil.copytree(images, DIST / "images", dirs_exist_ok=True)

    posts = load_posts()
    live = visible(posts)
    masthead, footer = tpl("masthead.html"), tpl("footer.html")
    n_ideas_all = len(json.loads((ROOT / "content" / "learn" / "graph.json").read_text(encoding="utf-8"))["ideas"])
    # ---- learn structure: guided paths, idea pages, the architect route (validated; errors stop the build)
    lgraph, lpaths, lroutes = learn_build.load()
    lerrs = learn_build.validate(lgraph, lpaths, lroutes, set(), None)
    lerrs += learn_build.validate_scenes(json.loads((ROOT / "content" / "scenes.json").read_text(encoding="utf-8")))
    if lerrs: raise SystemExit("Learn structure errors:\n  " + "\n  ".join(lerrs))
    by_idea = {i["id"]: i for i in lgraph["ideas"]}
    doors_full = learn_build.render_doors(lpaths, by_idea)
    doors_compact = learn_build.render_doors(lpaths, by_idea, compact=True)
    paths_json_s = learn_build.paths_json(lpaths, by_idea)

    # ---- post pages
    for p in live:
        p.body_html = render_md(p)
        li = (f'<a href="{esc(p.linkedin_url)}" target="_blank" rel="noopener">Discuss on LinkedIn →</a>'
              if p.linkedin_url else "")
        fig = (f'<figure class="card"><img src="/images/{p.slug}.png" alt="{esc(p.title)}" width="1200" height="1200" loading="lazy"></figure>'
               if p.image else "")
        body = fill(tpl("post.html"), MASTHEAD=masthead, FOOTER=footer, TITLE=esc(p.title),
                    DATE_LONG=p.date_long, TAG=esc(p.tag_label), CONTENT=p.body_html, LINKEDIN_LINK=li, FIGURE=fig)
        out = DIST / "writing" / p.slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(body, title=f"{p.title} · Khalid Shams", description=p.summary or p.title,
                            canonical=p.abs_url, og_type="article", og_image=p.image_url), encoding="utf-8")

    # ---- home
    if live:
        cards = "\n".join(
            f'''    <div class="post-card">
      <p class="meta"><span>{p.date_long}</span><span class="tg">{esc(p.tag_label)}</span></p>
      <h3><a href="{p.url}">{esc(p.title)}</a></h3>
      <p>{esc(p.summary)}</p>
      <a class="read" href="{p.url}">Read →</a>
    </div>''' for p in live[:HOME_LIMIT])
        writing = f'<div class="posts">\n{cards}\n  </div>\n  <p class="more"><a href="/writing/">All writing ({len(live)}) →</a></p>'
    else:
        writing = '<p class="empty">First notes land here on September 15, 2026.</p>'
    # ---- playbooks
    pbs = load_playbooks()
    for pb in pbs:
        render_playbook_md(pb)
    def pb_card(pb: Playbook, current: Playbook | None = None) -> str:
        on = ' aria-current="page"' if current and pb.slug == current.slug else ""
        chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in pb.stack[:5])
        return (f'    <a class="pb-card" href="{pb.url}"{on}><b>{pb.nn}</b><span class="pb-k">{esc(pb.kicker)}</span>'
                f'<span class="pb-t">{esc(pb.title)}</span><span class="pb-s">{esc(pb.summary)}</span>'
                f'<span class="chips">{chips}</span><span class="pb-go">Read the playbook →</span></a>')
    if pbs:
        (DIST / "playbooks").mkdir(exist_ok=True)
        for i, pb in enumerate(pbs):
            nxt = pbs[(i + 1) % len(pbs)]
            toc = "\n".join(f'      <a href="#{hid}">{esc(name)}</a>' for hid, name in pb.toc)
            jump = "".join(f'<a class="btn{" solid" if j == 0 else ""}" href="#{hid}">{esc(name)}</a>'
                           for j, (hid, name) in enumerate(pb.toc[:3]))
            body = fill(tpl("playbook.html"), MASTHEAD=masthead, FOOTER=footer, NUM=pb.nn, TOTAL=f"{len(pbs):02d}",
                        KICKER=esc(pb.kicker), TITLE=esc(pb.title), SUMMARY=esc(pb.summary),
                        STACK="".join(f'<span class="chip">{esc(t)}</span>' for t in pb.stack), JUMP=jump, TOC=toc,
                        CONTENT=pb.body_html, NEXT_TITLE=esc(nxt.title), NEXT_SUMMARY=esc(nxt.summary),
                        NEXT_URL=nxt.url, NEXT_NUM=nxt.nn,
                        SIBLINGS="\n".join(pb_card(o, pb) for o in pbs if o.slug != pb.slug))
            (DIST / "playbooks" / pb.slug).mkdir(exist_ok=True)
            (DIST / "playbooks" / pb.slug / "index.html").write_text(page(body,
                title=f"{pb.title} playbook · Khalid Shams", description=pb.summary, canonical=pb.abs_url,
                og_type="article"), encoding="utf-8")
        idx = fill(tpl("playbooks_index.html"), MASTHEAD=masthead, FOOTER=footer,
                   CARDS="\n".join(pb_card(o) for o in pbs))
        (DIST / "playbooks" / "index.html").write_text(page(idx, title="Playbooks · Khalid Shams",
            description="Six principal-level playbooks: agentic AI, application modernization, data and AI platform, security and governance, cloud foundations and multi-tenant SaaS, and full-stack product engineering. The questions, the Azure build in order, and the real use cases.",
            canonical=f"{SITE}/playbooks/"), encoding="utf-8")

    # ---- tools
    def tool_card(i: int, t: dict) -> str:
        chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in t["chips"])
        return (f'    <a class="pb-card" href="/tools/{t["slug"]}/"><b>{i:02d}</b><span class="pb-k">{esc(t["kicker"])}</span>'
                f'<span class="pb-t">{esc(t["title"])}</span><span class="pb-s">{esc(t["summary"])}</span>'
                f'<span class="chips">{chips}</span><span class="pb-go">Open the tool →</span></a>')
    (DIST / "tools").mkdir(exist_ok=True)
    for i, t in enumerate(TOOLS, 1):
        body = fill(tpl(f"tools/{t['slug']}.html"), MASTHEAD=masthead, FOOTER=footer, NUM=f"{i:02d}", TOTAL=f"{len(TOOLS):02d}")
        (DIST / "tools" / t["slug"]).mkdir(exist_ok=True)
        (DIST / "tools" / t["slug"] / "index.html").write_text(page(body, title=f"{t['title']} · Tools · Khalid Shams",
            description=t["description"], canonical=f"{SITE}/tools/{t['slug']}/"), encoding="utf-8")
    ti = fill(tpl("tools_index.html"), MASTHEAD=masthead, FOOTER=footer,
              CARDS="\n".join(tool_card(i, t) for i, t in enumerate(TOOLS, 1)))
    (DIST / "tools" / "index.html").write_text(page(ti, title="Tools · Khalid Shams",
        description="Reference calculators for cloud and AI architecture: composite availability and recovery time today, with agent cost per run, tenant tier rules, a detection-first log budget, and an honest estimate on the bench. Runs in your browser.",
        canonical=f"{SITE}/tools/"), encoding="utf-8")

    home = fill(tpl("home.html"), NIDEASCAP=num_words(n_ideas_all).capitalize(), WRITING=writing, MASTHEAD=masthead,
                PLAYBOOKS="\n".join(pb_card(o) for o in pbs), DOORS=doors_compact, PATHSJSON=paths_json_s)
    (DIST / "index.html").write_text(page(home, title="Khalid Shams · Principal Solutions Architect",
        description="Khalid Shams, Principal Solutions Architect in Phoenix, Arizona. Enterprise cloud, data & AI, and agentic systems for regulated, multi-tenant and mission-critical environments.",
        canonical=SITE + "/", og_type="profile"), encoding="utf-8")

    # ---- writing index
    items = "\n".join(
        f'''      <div class="item">
        <p class="d">{p.date_long}</p>
        <div><h3><a href="{p.url}">{esc(p.title)}</a></h3><p>{esc(p.summary)}</p></div>
      </div>''' for p in live) or '      <p class="empty">Nothing published yet.</p>'
    (DIST / "writing").mkdir(exist_ok=True)
    (DIST / "writing" / "index.html").write_text(page(
        fill(tpl("writing_index.html"), MASTHEAD=masthead, FOOTER=footer, ITEMS=items),
        title="Writing · Khalid Shams", description="Short essays on architecture, agentic AI, and the decisions that actually cost money.",
        canonical=SITE + "/writing/"), encoding="utf-8")

    # ---- feed.xml
    def rfc822(d: date) -> str:
        return datetime(d.year, d.month, d.day, 15, 0, tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items_xml = "\n".join(f"""  <item>
    <title>{esc(p.title)}</title>
    <link>{p.abs_url}</link>
    <guid isPermaLink="true">{p.abs_url}</guid>
    <pubDate>{rfc822(p.date)}</pubDate>
    <description>{esc(p.summary)}</description>
    <content:encoded><![CDATA[{p.body_html}]]></content:encoded>
  </item>""" for p in live)
    (DIST / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Khalid Shams · Writing</title>
  <link>{SITE}/writing/</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Short essays on architecture, agentic AI, and the decisions that actually cost money.</description>
  <language>en-us</language>
{items_xml}
</channel>
</rss>
""", encoding="utf-8")

    # ---- sitemap + robots
    urls = ([f"{SITE}/", f"{SITE}/learn/", f"{SITE}/learn/atlas/", f"{SITE}/learn/atlas/how-models-are-made/", f"{SITE}/architect/", f"{SITE}/method/", f"{SITE}/playbooks/"]
            + [f"{SITE}/learn/paths/{x['id']}/" for x in learn_build.load()[1]["paths"]] + [f"{SITE}/learn/ideas/{x['id']}/" for x in learn_build.load()[0]["ideas"]] + [pb.abs_url for pb in load_playbooks()]
            + [f"{SITE}/tools/"] + [f"{SITE}/tools/{t['slug']}/" for t in TOOLS]
            + [f"{SITE}/writing/"] + [p.abs_url for p in live])
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    # ---- method page
    mp = fill(tpl("method.html"), MASTHEAD=masthead, FOOTER=footer)
    mp = mp.replace("{{PAGENAV}}", learn_build.page_nav(mp))
    (DIST / "method").mkdir(exist_ok=True)
    (DIST / "method" / "index.html").write_text(page(mp, title="The SHAMS Method · Khalid Shams",
        description="Where AI belongs in your enterprise and how to keep it safe: an interactive map of your estate, the autonomy ladder, and the eight gates between a demo and a system.",
        canonical=f"{SITE}/method/"), encoding="utf-8")

    # ---- SHAMS AI Atlas (content registry in content/atlas, validated at build time)
    graph = json.loads((ROOT / "content" / "learn" / "graph.json").read_text(encoding="utf-8"))
    graph_ids = {i["id"] for i in graph["ideas"]}
    ATLAS_META = {
        "damaged-order": ("The SHAMS AI Atlas · Learn AI · Khalid Shams",
                          "See what each part does, and how the whole system works: follow one customer request through an illustrated, governed AI system. Picture and architecture views, SHAMS overlays, and what changes when evidence is missing, a permission is denied, a tool fails or a record carries a planted instruction."),
        "model-making": ("How a model is made · The SHAMS AI Atlas · Khalid Shams",
                         "Follow one language model from raw text to a pinned release: data and bias, tokens and embeddings, the transformer and attention, the training loop and backpropagation, fine-tuning, alignment and evaluation. Illustrated, with picture and architecture views."),
    }
    atlas_stats = None
    for m in atlas_build.SCENES:
        a_html, a_svg, a_stats = atlas_build.render_scene(m["id"], tpl("atlas.html"), masthead=masthead, footer=footer, graph_ids=graph_ids, extra={"PATHSJSON": paths_json_s})
        out_dir = DIST / m["out"]; out_dir.mkdir(parents=True, exist_ok=True)
        t_, d_ = ATLAS_META[m["id"]]
        (out_dir / "index.html").write_text(page(a_html, title=t_, description=d_, canonical=f"{SITE}/{m['out']}/"), encoding="utf-8")
        (out_dir / "scene.svg").write_text(a_svg["light"], encoding="utf-8")
        (out_dir / "scene-dark.svg").write_text(a_svg["dark"], encoding="utf-8")
        atlas_stats = atlas_stats or a_stats
        print(f"atlas {m['id']}: {a_stats['concepts']} concepts ({a_stats['mapped']} linked to the Learn map), {a_stats['steps']} step templates, {a_stats['sources']} sources")
    atlas_registry = a_stats["registry"]

    # ---- learn page
    n_ideas = len(graph["ideas"])
    lp = fill(tpl("learn.html"), MASTHEAD=masthead, FOOTER=footer, NIDEAS=num_words(n_ideas), NIDEASCAP=num_words(n_ideas).capitalize(), NIDEASN=str(n_ideas), ATLASN=str(atlas_registry),
              GRAPH=json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), DOORS=doors_full, PATHSJSON=paths_json_s)
    lp = lp.replace("{{PAGENAV}}", learn_build.page_nav(lp))
    (DIST / "learn").mkdir(exist_ok=True)
    (DIST / "learn" / "index.html").write_text(page(lp, title="Learn AI · Khalid Shams",
        description=f"Learn AI the way it learns: an interactive map of {n_ideas} ideas with three depths each, the seven-layer AI stack (where MCP, agents and guardrails actually sit), model vs chatbot vs workflow vs agent, the agentic loop, multi-agent patterns, prompts vs hooks, and the questions beginners ask.",
        canonical=f"{SITE}/learn/"), encoding="utf-8")

    # ---- guided paths, one page per idea, the architect route
    atlas_where = {}
    for m in atlas_build.SCENES:
        sc_ = atlas_build.load_scenario(m["id"]); cons = atlas_build.scene_concepts(m["draw"](), sc_)
        for c in atlas_build.load()[0]["concepts"]:
            if c["id"] in cons and c.get("mapId") and c["mapId"] not in atlas_where:
                atlas_where[c["mapId"]] = {"href": f"{sc_['page']['route']}?focus={c['id']}", "title": sc_["title"]}
    for pth in lpaths["paths"]:
        out = DIST / "learn" / "paths" / pth["id"]; out.mkdir(parents=True, exist_ok=True)
        body = learn_build.render_path(tpl("path.html"), pth, lpaths, by_idea, masthead=masthead, footer=footer)
        (out / "index.html").write_text(page(body, title=f"Path {pth['n']}: {pth['title']} · Learn AI · Khalid Shams",
            description=f"Guided path {pth['n']} of 6. {pth['promise']} About {pth['minutes']} minutes, {len(pth['stops'])} stops.",
            canonical=f"{SITE}/learn/paths/{pth['id']}/").replace("<body>", f'<body data-path="{pth["id"]}">', 1), encoding="utf-8")
    for i in lgraph["ideas"]:
        out = DIST / "learn" / "ideas" / i["id"]; out.mkdir(parents=True, exist_ok=True)
        body = learn_build.render_idea(tpl("idea.html"), i, lgraph, lpaths, by_idea, atlas_where, masthead=masthead, footer=footer)
        (out / "index.html").write_text(page(body, title=f"{i['label']} · Learn AI · Khalid Shams",
            description=f"{i['plain']} {i['picture']}", canonical=f"{SITE}/learn/ideas/{i['id']}/").replace("<body>", f'<body data-stop="idea:{i["id"]}">', 1), encoding="utf-8")
    ap = learn_build.render_architect(tpl("architect.html"), lroutes, lpaths, by_idea, masthead=masthead, footer=footer)
    ap = ap.replace("{{PAGENAV}}", learn_build.page_nav(ap))
    (DIST / "architect").mkdir(exist_ok=True)
    (DIST / "architect" / "index.html").write_text(page(ap, title="Architect · what are you building? · Khalid Shams",
        description="Say what you are building and get the route: what to learn first, what to watch run, the gate to decide it, the playbook, the number to check and a worked example. Plus a brief builder for the design review.",
        canonical=f"{SITE}/architect/"), encoding="utf-8")
    print(f"learn structure: {len(lpaths['paths'])} paths, {len(lgraph['ideas'])} idea pages, {len(lroutes['situations'])} architect situations")

    # ---- 404 (CloudFront custom error response points here)
    nf = fill(tpl("404.html"), MASTHEAD=masthead, FOOTER=footer)
    (DIST / "404.html").write_text(page(nf, title="Not found · Khalid Shams",
                                        description="That page doesn't exist.", canonical=f"{SITE}/404.html"),
                                   encoding="utf-8")

    # ---- privacy policy (needed by the LinkedIn app registration)
    pv = fill(tpl("privacy.html"), MASTHEAD=masthead, FOOTER=footer)
    (DIST / "privacy").mkdir(exist_ok=True)
    (DIST / "privacy" / "index.html").write_text(page(pv, title="Privacy policy · Khalid Shams",
        description="This site sets no cookies and collects no personal data.", canonical=f"{SITE}/privacy/"),
        encoding="utf-8")

    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    # ---- search index
    pages = [("/", DIST / "index.html"), ("/learn/", DIST / "learn" / "index.html"), ("/learn/atlas/", DIST / "learn" / "atlas" / "index.html"), ("/learn/atlas/how-models-are-made/", DIST / "learn" / "atlas" / "how-models-are-made" / "index.html"), ("/architect/", DIST / "architect" / "index.html"), ("/method/", DIST / "method" / "index.html")] + \
            [(f"/learn/paths/{x['id']}/", DIST / "learn" / "paths" / x["id"] / "index.html") for x in lpaths["paths"]] + [
             ("/playbooks/", DIST / "playbooks" / "index.html")] + [(pb.url, DIST / "playbooks" / pb.slug / "index.html") for pb in pbs] + \
            [("/tools/", DIST / "tools" / "index.html")] + [(f"/tools/{t['slug']}/", DIST / "tools" / t["slug"] / "index.html") for t in TOOLS] + \
            [("/writing/", DIST / "writing" / "index.html"), ("/privacy/", DIST / "privacy" / "index.html")]
    idx = build_search_index([pg for pg in pages if pg[1].exists()], graph, live)
    (DIST / "search.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"search index: {len(idx)} entries")

    # ---- manifest (used by the publisher and handy for debugging)
    (DIST / "posts.json").write_text(json.dumps([{
        "slug": p.slug, "title": p.title, "date": p.date_iso, "status": p.status,
        "url": p.abs_url, "linkedin_url": p.linkedin_url} for p in sorted(posts, key=lambda x: x.date)],
        indent=2), encoding="utf-8")

    n_draft = sum(1 for p in posts if p.status == "draft")
    n_queued = sum(1 for p in posts if p.status == "approved" and p.date > today_phx())
    print(f"built: {len(live)} live post(s), {n_queued} approved & scheduled, {n_draft} draft(s) → {DIST}")


if __name__ == "__main__":
    build()
