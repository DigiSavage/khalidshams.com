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

ROOT = Path(__file__).parent
SITE = "https://khalidshams.com"
TZ = timezone(timedelta(hours=-7))          # America/Phoenix: no DST
DIST, POSTS, TPL = ROOT / "dist", ROOT / "content" / "posts", ROOT / "templates"
HOME_LIMIT = 6
VISIBLE = {"approved", "published"}

MD = markdown.Markdown(extensions=["smarty", "sane_lists"], output_format="html5")


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


def tpl(name: str) -> str:
    return (TPL / name).read_text(encoding="utf-8")


def fill(s: str, **kw) -> str:
    for k, v in kw.items():
        s = s.replace("{{" + k + "}}", v)
    return s


def page(body: str, *, title: str, description: str, canonical: str, og_type="website") -> str:
    return fill(tpl("base.html"), BODY=body, TITLE=html.escape(title, quote=True),
                DESCRIPTION=html.escape(description, quote=True), CANONICAL=canonical, OG_TYPE=og_type)


def esc(s: str) -> str: return html.escape(s, quote=True)


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    static = ROOT / "static"
    if static.exists():
        shutil.copytree(static, DIST, dirs_exist_ok=True)

    posts = load_posts()
    live = visible(posts)
    masthead, footer = tpl("masthead.html"), tpl("footer.html")

    # ---- post pages
    for p in live:
        p.body_html = render_md(p)
        li = (f'<a href="{esc(p.linkedin_url)}" target="_blank" rel="noopener">Discuss on LinkedIn →</a>'
              if p.linkedin_url else "")
        body = fill(tpl("post.html"), MASTHEAD=masthead, FOOTER=footer, TITLE=esc(p.title),
                    DATE_LONG=p.date_long, TAG=esc(p.tag_label), CONTENT=p.body_html, LINKEDIN_LINK=li)
        out = DIST / "writing" / p.slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(body, title=f"{p.title} — Khalid Shams", description=p.summary or p.title,
                            canonical=p.abs_url, og_type="article"), encoding="utf-8")

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
    home = fill(tpl("home.html"), WRITING=writing)
    (DIST / "index.html").write_text(page(home, title="Khalid Shams — Principal Solutions Architect",
        description="Khalid Shams — Principal Solutions Architect in Phoenix, Arizona. Enterprise cloud, data & AI, and agentic systems for regulated, multi-tenant and mission-critical environments.",
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
        title="Writing — Khalid Shams", description="Short essays on architecture, agentic AI, and the decisions that actually cost money.",
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
  <title>Khalid Shams — Writing</title>
  <link>{SITE}/writing/</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Short essays on architecture, agentic AI, and the decisions that actually cost money.</description>
  <language>en-us</language>
{items_xml}
</channel>
</rss>
""", encoding="utf-8")

    # ---- sitemap + robots
    urls = [f"{SITE}/", f"{SITE}/writing/"] + [p.abs_url for p in live]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    # ---- 404 (CloudFront custom error response points here)
    nf = fill(tpl("404.html"), MASTHEAD=masthead, FOOTER=footer)
    (DIST / "404.html").write_text(page(nf, title="Not found — Khalid Shams",
                                        description="That page doesn't exist.", canonical=f"{SITE}/404.html"),
                                   encoding="utf-8")

    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

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
