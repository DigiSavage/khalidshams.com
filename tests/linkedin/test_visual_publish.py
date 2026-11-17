"""Infographic integrity and no-text-only-fallback publication checks."""
import contextlib
import hashlib
import io
import json
import os
import struct
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from scripts import publish_linkedin as publisher


class VisualPublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.posts = self.root / "content/posts"
        self.images = self.root / "content/images"
        self.posts.mkdir(parents=True)
        self.images.mkdir(parents=True)
        self.path = self.posts / "2026-11-23-proof.md"
        self.path.write_text("---\ntitle: Proof\ndate: 2026-11-23\nstatus: approved\nvisual_required: true\nlinkedin_url:\n---\nA useful check.\n")
        self.meta, _ = publisher.parse(self.path.read_text())
        self.asset = self.images / "proof.png"
        self.data = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1200, 1500) + b"fixture-padding"
        self.asset.write_bytes(self.data)
        self.manifest = self.root / "manifest.json"
        self.entry = {"post": "content/posts/2026-11-23-proof.md", "asset": "content/images/proof.png", "alt": "The write is refused when the approved amount changes.", "sha256": hashlib.sha256(self.data).hexdigest()}
        self.save_manifest()
        self.pending = self.root / "pending.json"
        self.hold = {"path": "content/posts/2026-11-23-proof.md", "date": "2026-11-23", "attempt": "visual-test"}
        for key, value in {"ROOT": self.root, "POSTS": self.posts, "IMAGES": self.images, "VISUAL_MANIFEST": self.manifest, "PENDING": self.pending}.items():
            mock = patch.object(publisher, key, value)
            mock.start()
            self.addCleanup(mock.stop)

    def save_manifest(self, entries=None):
        self.manifest.write_text(json.dumps({"schema_version": 1, "items": [self.entry] if entries is None else entries}))

    def run_main(self, **extra):
        env = {"SCHEDULED": "1", "LINKEDIN_ACCESS_TOKEN": "fixture-only", "PUBLICATION_ATTEMPT": "visual-test", "REQUIRE_RESERVATION": "1"} | extra
        with patch.dict(os.environ, env, clear=True), patch.object(publisher, "today", return_value=date(2026, 11, 23)), contextlib.redirect_stdout(io.StringIO()):
            return publisher.main()

    def test_reviewed_asset_and_descriptive_alt_are_selected(self):
        self.assertEqual(publisher.visual_for(self.path, self.meta), (self.asset.resolve(), self.entry["alt"], True))

    def test_missing_duplicate_and_tampered_assets_are_rejected(self):
        self.save_manifest([])
        with self.assertRaises(ValueError): publisher.visual_for(self.path, self.meta)
        self.save_manifest([self.entry, self.entry])
        with self.assertRaises(ValueError): publisher.visual_for(self.path, self.meta)
        self.save_manifest()
        self.asset.write_bytes(self.data + b"changed")
        with self.assertRaises(ValueError): publisher.visual_for(self.path, self.meta)

    def test_path_escape_and_wrong_dimensions_are_rejected(self):
        self.entry["asset"] = "../outside.png"
        self.save_manifest()
        with self.assertRaises(ValueError): publisher.visual_for(self.path, self.meta)
        self.entry["asset"] = "content/images/proof.png"
        self.asset.write_bytes(self.data[:16] + struct.pack(">II", 100, 100) + self.data[24:])
        self.save_manifest()
        with self.assertRaises(ValueError): publisher.visual_for(self.path, self.meta)

    def test_missing_visual_stops_before_reservation_and_network(self):
        self.asset.unlink()
        with patch.object(publisher, "api") as api:
            self.assertEqual(self.run_main(RESERVE_ONLY="1"), 1)
        self.assertFalse(self.pending.exists())
        api.assert_not_called()

    def test_invalid_visual_releases_only_matching_owned_hold_before_network(self):
        self.pending.write_text(json.dumps(self.hold))
        self.asset.unlink()
        with patch.object(publisher, "api") as api:
            self.assertEqual(self.run_main(), 1)
        self.assertFalse(self.pending.exists())
        api.assert_not_called()
        self.assertEqual(publisher.parse(self.path.read_text())[0]["status"], "approved")

    def test_invalid_visual_cannot_release_foreign_or_mismatched_hold(self):
        self.asset.unlink()
        for hold in (
            {**self.hold, "attempt": "another-attempt"},
            {**self.hold, "path": "content/posts/2026-11-23-another.md"},
        ):
            with self.subTest(hold=hold):
                saved = json.dumps(hold)
                self.pending.write_text(saved)
                with patch.object(publisher, "api") as api:
                    self.assertEqual(self.run_main(), 1)
                self.assertEqual(self.pending.read_text(), saved)
                api.assert_not_called()

    def test_failed_upload_releases_hold_without_posting_text(self):
        self.pending.write_text(json.dumps(self.hold))
        with patch.object(publisher, "api", return_value=(200, {}, '{"sub":"fixture"}')) as api, patch.object(publisher, "upload_image", return_value=None):
            self.assertEqual(self.run_main(), 1)
        self.assertEqual([c.args[1] for c in api.call_args_list], ["/v2/userinfo"])
        self.assertFalse(self.pending.exists())
        self.assertEqual(publisher.parse(self.path.read_text())[0]["status"], "approved")

    def test_success_publishes_the_graphic_with_its_alt_text(self):
        self.pending.write_text(json.dumps(self.hold))
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"fixture"}'), (201, {"x-restli-id": "urn:li:share:123456"}, "{}")]) as api, patch.object(publisher, "upload_image", return_value="urn:li:image:fixture"):
            self.assertEqual(self.run_main(), 0)
        media = api.call_args_list[1].args[3]["content"]["media"]
        self.assertEqual(media["altText"], self.entry["alt"])
        self.assertEqual(media["id"], "urn:li:image:fixture")


class RepositoryVisualTests(unittest.TestCase):
    def test_every_required_post_has_a_verified_graphic(self):
        required = []
        for path in publisher.POSTS.glob("*.md"):
            meta, _ = publisher.parse(path.read_text())
            if meta and meta.get("visual_required") == "true":
                required.append(path)
                with self.subTest(post=path.name):
                    asset, alt, is_required = publisher.visual_for(path, meta)
                    self.assertTrue(asset.is_file())
                    self.assertTrue(is_required)
        self.assertGreater(len(required), 0)
