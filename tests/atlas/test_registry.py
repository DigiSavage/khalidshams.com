"""Run: python -m unittest discover -s tests/atlas -p 'test_*.py'   (after python build.py)"""
import copy, json, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import atlas_build, atlas_scene  # noqa: E402

GRAPH = json.loads((ROOT / "content/learn/graph.json").read_text(encoding="utf-8"))
GIDS = {i["id"] for i in GRAPH["ideas"]}
DIST = ROOT / "dist"


class Registry(unittest.TestCase):
    def setUp(self):
        self.c, self.s, self.k, self.sc = atlas_build.load()
        self.svg = atlas_scene.scene()

    def errs(self, c=None, s=None, k=None, sc=None):
        return atlas_build.validate(c or self.c, s or self.s, k or self.k, sc or self.sc, GIDS, self.svg)

    def test_real_content_is_valid(self):
        self.assertEqual(self.errs(), [])

    def test_ids_unique_and_fields_present(self):
        ids = [x["id"] for x in self.c["concepts"]]
        self.assertEqual(len(ids), len(set(ids)))
        for x in self.c["concepts"]:
            for f in atlas_build.REQUIRED:
                self.assertIn(f, x, f"{x['id']} missing {f}")

    def test_every_scene_concept_has_a_picture_and_a_metaphor_limit(self):
        for cid in set(re.findall(r'data-c="([a-z_]+)"', self.svg)):
            c = next(x for x in self.c["concepts"] if x["id"] == cid)
            self.assertGreater(len(c["picture"]), 20); self.assertGreater(len(c["metaphorLimit"]), 20)

    def test_every_registry_concept_appears_in_the_scene(self):
        in_scene = set(re.findall(r'data-c="([a-z_]+)"', self.svg))
        for group in re.findall(r'data-sc="([a-z_ ]+)"', self.svg): in_scene |= set(group.split())
        for x in self.c["concepts"]:
            self.assertIn(x["id"], in_scene, f"{x['id']} has no illustration in the scene")

    def test_broken_references_are_caught(self):
        c = copy.deepcopy(self.c); c["concepts"].append(copy.deepcopy(c["concepts"][0]))
        self.assertTrue(any("duplicate" in e for e in self.errs(c=c)))
        c = copy.deepcopy(self.c); c["concepts"][0]["sources"] = ["nope"]
        self.assertTrue(any("unknown source" in e for e in self.errs(c=c)))
        c = copy.deepcopy(self.c); c["concepts"][3]["mapId"] = "not-an-idea"
        self.assertTrue(any("mapId" in e for e in self.errs(c=c)))
        c = copy.deepcopy(self.c); c["concepts"][3]["status"] = "source-checked"; c["concepts"][3]["sources"] = []
        self.assertTrue(any("without sources" in e for e in self.errs(c=c)))
        sc = copy.deepcopy(self.sc); sc["steps"]["request"]["edges"] = ["e_missing"]
        self.assertTrue(any("unknown edge" in e for e in self.errs(sc=sc)))
        k = copy.deepcopy(self.k); k["checks"][0]["options"][0]["ok"] = True
        self.assertTrue(any("exactly one" in e for e in self.errs(k=k)))

    def test_sources_have_dates_and_https(self):
        for s in self.s["sources"]:
            self.assertTrue(s["url"].startswith("https://")); self.assertRegex(s["checked"], r"^\d{4}-\d{2}-\d{2}$")

    def test_standalone_svg_has_explicit_fills(self):
        """Regression for the solid-black sheet: every shape must carry a fill attribute."""
        for theme in ("light", "dark"):
            s = atlas_build.standalone_svg(self.svg, theme)
            for tag in re.findall(r"<(?:rect|path|circle|ellipse|polygon)\b[^>]*>", s):
                self.assertIn("fill=", tag, f"{theme}: {tag[:90]}")


@unittest.skipUnless((DIST / "learn/atlas/index.html").exists(), "run python build.py first")
class Built(unittest.TestCase):
    def page(self, p): return (DIST / p).read_text(encoding="utf-8")

    def test_counts_match_the_data(self):
        n = len(GRAPH["ideas"])
        words = __import__("build").num_words(n)
        self.assertIn(f"{words} ideas", self.page("learn/index.html"))
        self.assertIn(f"{words.capitalize()} ideas", self.page("index.html"))
        self.assertIn(f"0 / {n} understood", self.page("learn/index.html"))

    def test_legacy_anchors_survive(self):
        learn = self.page("learn/index.html")
        for a in ["map", "stack", "kinds", "decide", "loop", "multi", "enforce", "faq", "atlas"]:
            self.assertIn(f'id="{a}"', learn, a)
        method = self.page("method/index.html")
        for a in ["shams", "agentic", "ag-parts", "ag-cost", "ag-team", "map", "ladder", "gates", "gate-check", "record"]:
            self.assertIn(f'id="{a}"', method, a)

    def test_progress_key_preserved(self):
        self.assertIn('"ks-learn"', self.page("learn/index.html"))
        js = (DIST / "atlas/atlas.js").read_text(encoding="utf-8")
        self.assertIn('"ks-learn"', js); self.assertIn('"ks-atlas-v1"', js)

    def test_internal_links_in_atlas_resolve(self):
        html = self.page("learn/atlas/index.html")
        for href in set(re.findall(r'href="(/[^"#?]*)', html)):
            p = DIST / href.lstrip("/")
            ok = p.exists() or (p / "index.html").exists()
            self.assertTrue(ok, href)

    def test_atlas_in_sitemap_and_search(self):
        self.assertIn("/learn/atlas/", self.page("sitemap.xml"))
        self.assertIn("/learn/atlas/", self.page("search.json"))

    def test_text_equivalent_present(self):
        html = self.page("learn/atlas/index.html")
        self.assertIn('id="text-version"', html)
        self.assertEqual(html.count('<li><b>'), len(json.loads((ROOT / "content/atlas/scenarios/damaged-order.json").read_text())["textEquivalent"]) + len(json.loads((ROOT / "content/atlas/scenarios/damaged-order.json").read_text())["outcomes"]))

    def test_no_dashes_in_public_output(self):
        for p in ["learn/atlas/index.html", "learn/index.html", "method/index.html"]:
            self.assertIsNone(re.search("—|–| -- ", self.page(p)), p)


if __name__ == "__main__":
    unittest.main()
