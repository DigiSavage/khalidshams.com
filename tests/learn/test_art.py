"""Art intake failures must stop a build before an unsafe or mislabeled asset ships."""
import tempfile
import unittest
from pathlib import Path

from art_assets import validate_art


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


if __name__ == "__main__":
    unittest.main()
