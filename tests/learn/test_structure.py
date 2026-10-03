"""Guided paths, idea pages and the architect route. Run: python -m unittest tests/learn/test_structure.py   (after python build.py)"""
import copy, json, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import learn_build  # noqa: E402

DIST = ROOT / "dist"
G, P, R = learn_build.load()


def resolves(href: str) -> bool:
    """An internal link resolves when its page is built and, if it has a fragment, the anchor exists on that page."""
    path, _, frag = href.partition("#")
    path = path.split("?")[0]
    f = DIST / path.lstrip("/")
    page = f / "index.html" if f.is_dir() else f
    if not page.exists(): return False
    return (f'id="{frag}"' in page.read_text(encoding="utf-8")) if frag else True


class Content(unittest.TestCase):
    def test_real_content_is_valid(self):
        self.assertEqual(learn_build.validate(G, P, R, set(), None), [])

    def test_six_paths_cover_every_map_idea_once(self):
        ideas = [st["idea"] for p in P["paths"] for st in p["stops"] if "idea" in st]
        self.assertEqual(len(ideas), len(set(ideas)), "an idea sits on two paths")
        self.assertEqual(set(ideas), {i["id"] for i in G["ideas"]}, "every idea belongs to exactly one path")
        self.assertEqual([p["n"] for p in P["paths"]], [1, 2, 3, 4, 5, 6])

    def test_broken_content_is_caught(self):
        p = copy.deepcopy(P); p["paths"][0]["stops"].append({"idea": "nope"})
        self.assertTrue(any("unknown idea" in e for e in learn_build.validate(G, p, R, set(), None)))
        r = copy.deepcopy(R); r["situations"][0]["steps"] = [s for s in r["situations"][0]["steps"] if s["kind"] != "example"]
        self.assertTrue(any("worked example" in e for e in learn_build.validate(G, P, r, set(), None)))
        r = copy.deepcopy(R); r["situations"][0]["gates"].append("g9")
        self.assertTrue(any("bad gate" in e for e in learn_build.validate(G, P, r, set(), None)))

    def test_every_situation_routes_through_all_six_kinds_or_close(self):
        for s in R["situations"]:
            kinds = {x["kind"] for x in s["steps"]}
            self.assertTrue({"learn", "decide", "build", "example"} <= kinds, s["id"])


@unittest.skipUnless((DIST / "architect/index.html").exists(), "run python build.py first")
class Built(unittest.TestCase):
    def page(self, p): return (DIST / p).read_text(encoding="utf-8")

    def test_every_idea_has_a_page_with_three_depths(self):
        for i in G["ideas"]:
            html = self.page(f"learn/ideas/{i['id']}/index.html")
            for lab in ("In one line", "Picture it", "Under the hood"): self.assertIn(lab, html, i["id"])
            self.assertIn(f'data-stop="idea:{i["id"]}"', html)

    def test_every_link_in_paths_and_routes_resolves(self):
        hrefs = set()
        for p in P["paths"]:
            for st in p["stops"]:
                if "atlas" in st: hrefs.add(st["atlas"].split("?")[0])
                if "section" in st: hrefs.add(st["section"])
        for s in R["situations"]:
            for x in s["steps"]: hrefs.add(x["href"])
        for q in R["brief"]["questions"]:
            for k in ("lessons", "watch", "check"): hrefs.update(q["yes_adds"].get(k, []))
        for k in ("lessons", "check"): hrefs.update(R["brief"]["always"][k])
        for h in sorted(hrefs): self.assertTrue(resolves(h), h)

    def test_start_doors_on_learn_and_home_and_nav_links(self):
        for pg in ("learn/index.html", "index.html"):
            html = self.page(pg); self.assertIn('class="doors"', html, pg); self.assertIn('id="door-continue"', html, pg)
        self.assertIn('href="/architect/"', self.page("learn/index.html"))
        for pg in ("learn/index.html", "method/index.html", "architect/index.html"):
            self.assertIn('class="pagenav"', self.page(pg), pg)
        self.assertNotIn("{{", self.page("architect/index.html"))

    def test_map_panel_opens_the_idea_page(self):
        self.assertIn("/learn/ideas/", self.page("learn/index.html"))

    def test_search_and_sitemap_know_the_new_pages(self):
        sm = self.page("sitemap.xml"); sj = self.page("search.json")
        for r in ("/architect/", "/learn/paths/what-is-ai/", "/learn/ideas/agent/"):
            self.assertIn(r, sm, r)
        self.assertIn("/learn/ideas/agent/", sj); self.assertIn("/architect/", sj)

    def test_no_dashes_and_no_fixed_narrow_wrap(self):
        for p in ("architect/index.html", "learn/paths/what-is-ai/index.html", "learn/ideas/agent/index.html", "index.html"):
            self.assertIsNone(re.search("—|–| -- ", self.page(p)), p)
        self.assertIn("--wrap:1680px", self.page("index.html"))


if __name__ == "__main__":
    unittest.main()
