"""Art intake failures must stop a build before an unsafe or mislabeled asset ships."""
import tempfile
import unittest
from pathlib import Path

from art_assets import validate_art, illustration, VARIANTS, THEMES


class ArtTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.asset = dict(scene="production-review", variant="desktop", theme="light",
                          file="/art/production-review/desktop-light.webp", purpose="Home illustration",
                          crop="full", background="paper", alt="A reviewer pauses a proposed refund.",
                          concepts=["authorization"], text_in_image=False)
        self.file = self.root / self.asset["file"].lstrip("/")
        self.file.parent.mkdir(parents=True)
        # Minimal valid 1x1 WebP, used to exercise the file-type gate.
        import base64
        self.file.write_bytes(base64.b64decode("UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA"))

    def errors(self, assets=None):
        return validate_art({"assets": assets if assets is not None else [self.asset]}, {"authorization"}, self.root)

    def test_empty_manifest_and_valid_asset(self):
        self.assertEqual(self.errors([]), [])
        self.assertEqual(self.errors(), [])

    def test_missing_asset_and_wrong_file_type(self):
        self.file.unlink()
        self.assertIn("missing static/art", " ".join(self.errors()))
        self.file.write_text("not an image")
        self.assertIn("expected a WebP", " ".join(self.errors()))

    def test_reference_text_unknown_concept_and_duplicate(self):
        self.asset.update(text_in_image=True, concepts=["imagined"])
        errors = " ".join(self.errors([self.asset, self.asset]))
        for expected in ("text_in_image", "concept ids", "duplicate"):
            self.assertIn(expected, errors)

    def test_path_traversal_and_wrong_variant(self):
        self.asset["file"] = "/art/../../outside.webp"
        self.assertIn("file must be", " ".join(self.errors()))
        self.asset["variant"] = "huge"
        self.assertIn("unknown variant", " ".join(self.errors()))

    def test_malformed_records_and_missing_alt(self):
        self.assertTrue(validate_art([], set(), self.root))
        self.assertTrue(self.errors([None]))
        self.asset["scene"] = []
        self.asset.pop("alt")
        errors = " ".join(self.errors())
        self.assertIn("unknown scene", errors)
        self.assertIn("alt must be", errors)

    def test_incomplete_placed_study_fails(self):
        with self.assertRaisesRegex(ValueError, "missing variants"):
            illustration({"assets": [self.asset]}, "production-review")

    def test_dimensions_must_be_positive_integers(self):
        for value in (0, -1, True, '720'):
            self.asset['width'] = value
            self.assertIn('width must be', ' '.join(self.errors()))

    def test_renderer_escapes_alt_and_includes_authored_theme_pairs(self):
        assets = [dict(self.asset, variant=v, theme=t, width=720, height=480,
                       file=f'/art/production-review/{v}-{t}.webp', alt='A "proposal" <pending>')
                  for v in VARIANTS for t in THEMES]
        rendered = illustration({'assets': assets}, 'production-review', eager=True)
        self.assertIn('&quot;proposal&quot; &lt;pending&gt;', rendered)
        self.assertIn('software metaphor', rendered)
        self.assertEqual(rendered.count('<img '), 2)
        for theme in THEMES:
            self.assertIn(f'desktop-{theme}.webp 720w', rendered)
        self.assertIn('loading="eager"', rendered)
        assets[0].pop('height')
        with self.assertRaisesRegex(ValueError, 'positive width and height'):
            illustration({'assets': assets}, 'production-review')


if __name__ == "__main__":
    unittest.main()
