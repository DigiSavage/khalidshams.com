"""Offline tests for campaign selection and publication receipt handling."""
import contextlib
import io
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import publish_linkedin as publisher


RECEIPT = "https://www.linkedin.com/feed/update/urn:li:share:123456789/"


def note(day, slug="ordinary", **fields):
    meta = {"date": day, "status": "approved", "title": slug, "linkedin_url": ""}
    meta.update(fields)
    return Path(f"{day}-{slug}.md"), meta, "A specific architecture observation."


def campaign(day, **fields):
    return note(day, "campaign", series="2036", linkedin_schedule="2036", **fields)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.config = publisher.load_schedule()

    def select(self, posts, day, scheduled=True):
        return publisher.select_post(posts, self.config, date.fromisoformat(day), scheduled)

    def test_campaign_selects_exact_date_ahead_of_ordinary_backlog(self):
        posts = [note("2026-10-20"), campaign("2026-10-28"), campaign("2026-10-30")]
        self.assertEqual(self.select(posts, "2026-10-28").post, posts[1])

    def test_manual_receipt_excludes_october_26_for_both_run_types(self):
        for scheduled in (True, False):
            with self.subTest(scheduled=scheduled):
                result = self.select([note("2026-10-20")], "2026-10-26", scheduled)
                self.assertEqual(result.status, "already_published")
                self.assertTrue(result.receipt_url.endswith("7520443246674878464/"))

    def test_campaign_is_bounded_and_weekends_do_not_drain_queue(self):
        posts = [note("2026-10-20"), campaign("2026-11-20")]
        for day in ("2026-10-23", "2026-10-31", "2026-11-23", "2026-11-25", "2026-11-27"):
            with self.subTest(day=day):
                self.assertEqual(self.select(posts, day).status, "outside_schedule")
        self.assertEqual(self.select(posts, "2026-11-20").post, posts[1])

    def test_tuesday_and_thursday_preserve_oldest_ordinary_overdue(self):
        posts = [campaign("2026-10-28"), note("2026-10-27"), note("2026-10-20")]
        for day in ("2026-10-27", "2026-10-29", "2026-11-24"):
            with self.subTest(day=day):
                self.assertEqual(self.select(posts, day).post, posts[2])

    def test_campaign_gaps_duplicates_and_unapproved_posts_fail(self):
        for posts in ([note("2026-10-20")], [campaign("2026-10-28"), campaign("2026-10-28")],
                      [campaign("2026-10-28", status="draft")]):
            with self.subTest(posts=posts):
                with self.assertRaises(ValueError):
                    self.select(posts, "2026-10-28")

    def test_manual_runs_allow_ordinary_backlog_but_never_late_campaign(self):
        posts = [campaign("2026-10-28"), note("2026-10-27")]
        self.assertEqual(self.select(posts, "2026-10-31", False).post, posts[1])
        self.assertEqual(self.select(posts[:1], "2026-10-31", False).status, "nothing_due")
        self.assertEqual(self.select(posts, "2026-11-23", False).post, posts[1])
        with self.assertRaises(ValueError):
            self.select(posts, "2026-10-30", False)

    def test_actual_publication_day_blocks_another_backlog_post(self):
        posts = [note("2026-10-15", status="published", linkedin_url=RECEIPT,
                      linkedin_published_at="2026-10-27T08:00:00-07:00"), note("2026-10-20")]
        result = self.select(posts, "2026-10-27")
        self.assertEqual(result.status, "already_published")
        self.assertEqual(result.receipt_url, RECEIPT)

    def test_legacy_publication_date_and_utc_timezone(self):
        posts = [note("2026-10-27", status="published", linkedin_url=RECEIPT)]
        self.assertEqual(self.select(posts, "2026-10-27").status, "already_published")
        posts[0][1]["linkedin_published_at"] = "2026-10-28T02:00:00Z"
        self.assertEqual(self.select(posts, "2026-10-27").status, "already_published")

    def test_missing_receipt_on_published_day_requires_reconciliation(self):
        with self.assertRaisesRegex(ValueError, "without a verifiable receipt"):
            self.select([note("2026-10-27", status="published")], "2026-10-27")

    def test_empty_base_queue_fails_but_future_queue_is_not_due(self):
        with self.assertRaisesRegex(ValueError, "queue is empty"):
            self.select([], "2026-10-27")
        self.assertEqual(self.select([note("2026-10-29")], "2026-10-27").status, "nothing_due")


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.posts = self.root / "posts"
        self.posts.mkdir()
        self.path = self.posts / "2026-10-20-note.md"
        self.path.write_text('---\ntitle: "Test title"\ndate: 2026-10-20\nstatus: approved\nlinkedin_url:\n---\n\nProof before slogans.\n', encoding="utf-8")
        self.original = self.path.read_bytes()
        self.output = self.root / "github-output"
        self.output.write_text("existing=value\n", encoding="utf-8")
        self.pending = self.root / "linkedin_pending.json"
        self.hold = {"path": str(self.path.relative_to(self.root)), "date": "2026-10-27", "attempt": "test-1"}
        self.pending.write_text(json.dumps(self.hold))
        self.env = {"SCHEDULED": "1", "GITHUB_OUTPUT": str(self.output),
                    "REQUIRE_RESERVATION": "1", "PUBLICATION_ATTEMPT": "test-1"}
        for attr, value in (("ROOT", self.root), ("POSTS", self.posts), ("IMAGES", self.root / "images"), ("PENDING", self.pending)):
            item = patch.object(publisher, attr, value)
            item.start()
            self.addCleanup(item.stop)

    def run_main(self, day="2026-10-27", **env):
        stream = io.StringIO()
        with patch.dict(os.environ, self.env | env, clear=True), contextlib.redirect_stdout(stream), \
             patch.object(publisher, "today", return_value=date.fromisoformat(day)):
            code = publisher.main()
        return code, stream.getvalue()

    def test_dry_run_without_token_never_networks_or_writes_any_file(self):
        self.pending.unlink()
        with patch.object(publisher.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")) as network, \
             patch.object(publisher.Path, "write_text", side_effect=AssertionError("write forbidden")), \
             patch("builtins.open", side_effect=AssertionError("output write forbidden")):
            code, output = self.run_main(DRY_RUN="1")
        self.assertEqual(code, 0)
        self.assertIn('"status": "dry_run"', output)
        self.assertIn("Proof before slogans.", output)
        network.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(self.output.read_text(), "existing=value\n")

    def test_missing_token_is_a_visible_failure_without_network(self):
        with patch.object(publisher, "api") as api:
            code, output = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('"status": "missing_token"', output)
        api.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(self.pending.exists())
        self.assertIn('"reservation_released": "true"', output)

    def test_prepublication_failure_releases_owned_hold(self):
        with patch.object(publisher, "api", return_value=(401, {}, "expired credential")) as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        self.assertEqual(api.call_count, 1)
        self.assertIn('"status": "preparation_error"', output)
        self.assertIn('"reservation_released": "true"', output)
        self.assertFalse(self.pending.exists())

    def test_success_records_receipt_actual_day_and_prevents_second_post(self):
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'),
                                                        (201, {"X-RESTLI-ID": "urn:li:share:123456789"}, "{}")]) as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 0)
        self.assertEqual(api.call_count, 2)
        self.assertIn('"published": "true"', output)
        self.assertIn(RECEIPT, output)
        self.assertFalse(self.pending.exists())
        meta, body = publisher.parse(self.path.read_text())
        self.assertEqual(meta["date"], "2026-10-20")
        self.assertEqual(meta["status"], "published")
        self.assertEqual(meta["linkedin_url"], RECEIPT)
        self.assertTrue(meta["linkedin_published_at"].startswith("2026-10-27T"))
        self.assertEqual(body, "Proof before slogans.")
        other = self.posts / "2026-10-22-other.md"
        other.write_text(self.original.decode().replace("2026-10-20", "2026-10-22"))
        with patch.object(publisher, "api") as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 0)
        self.assertIn('"status": "already_published"', output)
        api.assert_not_called()

    def test_absent_share_id_is_ambiguous_and_never_marks_published(self):
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'), (201, {}, "{}")]) as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        self.assertEqual(api.call_count, 2)
        self.assertIn('"status": "ambiguous"', output)
        self.assertIn("Do not blindly retry", output)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertNotIn("published=true", self.output.read_text())
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)

    def test_timeout_after_post_attempt_is_not_retried(self):
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'), TimeoutError("unknown outcome")]) as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        self.assertEqual(api.call_count, 2)
        self.assertIn('"status": "ambiguous"', output)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)

    def test_timeout_hold_blocks_later_day_and_even_same_attempt_reservation(self):
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'), TimeoutError("unknown")]):
            code, _ = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        for day, attempt in (("2026-10-27", "test-1"), ("2026-10-29", "test-2")):
            with self.subTest(day=day), patch.object(publisher, "api") as api:
                code, output = self.run_main(day=day, RESERVE_ONLY="1", PUBLICATION_ATTEMPT=attempt)
            self.assertEqual(code, 1)
            self.assertIn('"status": "reservation_held"', output)
            api.assert_not_called()
            self.assertEqual(json.loads(self.pending.read_text()), self.hold)

    def test_server_error_is_ambiguous_but_explicit_rejection_is_not(self):
        for status, expected in ((503, "ambiguous"), (400, "publish_failed")):
            self.pending.write_text(json.dumps(self.hold))
            with self.subTest(status=status), patch.object(publisher, "api", side_effect=[
                    (200, {}, '{"sub":"test-member"}'), (status, {}, "request failed")]) as api:
                code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
            self.assertEqual(code, 1)
            self.assertEqual(api.call_count, 2)
            self.assertIn(f'"status": "{expected}"', output)
            self.assertEqual(self.path.read_bytes(), self.original)
            self.assertEqual(self.pending.exists(), status == 503)

    def test_receipt_write_failure_reports_live_post_for_reconciliation(self):
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'),
                                                        (201, {"x-restli-id": "urn:li:share:123456789"}, "{}")]), \
             patch.object(publisher, "record_publication", side_effect=OSError("disk full")):
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        self.assertIn('"status": "receipt_write_failed"', output)
        self.assertIn(RECEIPT, output)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)

    def test_failed_remote_receipt_commit_leaves_persisted_hold_blocking_next_run(self):
        # Simulate a fresh checkout after LinkedIn succeeded but Git push failed:
        # the remote still contains the reservation and original approved post.
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'),
                                                        (201, {"x-restli-id": "urn:li:share:123456789"}, "{}")]):
            code, _ = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 0)
        self.path.write_bytes(self.original)
        self.pending.write_text(json.dumps(self.hold))
        with patch.object(publisher, "api") as api:
            code, output = self.run_main(day="2026-10-29", RESERVE_ONLY="1", PUBLICATION_ATTEMPT="next-run-1")
        self.assertEqual(code, 1)
        self.assertIn('"status": "reservation_held"', output)
        api.assert_not_called()

    def test_reservation_is_exclusive_and_performs_no_linkedin_network(self):
        self.pending.unlink()
        with patch.object(publisher, "api") as api, patch.object(publisher.urllib.request, "urlopen") as network:
            code, output = self.run_main(RESERVE_ONLY="1")
            repeat_code, repeat_output = self.run_main(RESERVE_ONLY="1")
        self.assertEqual(code, 0)
        self.assertIn('"reserved": "true"', output)
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)
        self.assertEqual(repeat_code, 1)
        self.assertIn('"status": "reservation_held"', repeat_output)
        api.assert_not_called()
        network.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_live_publish_requires_exact_reservation_and_cannot_bypass_hold(self):
        for changed in ({"attempt": "another-run"}, {"date": "2026-10-26"}, {"path": "posts/another.md"}):
            self.pending.write_text(json.dumps(self.hold | changed))
            with self.subTest(changed=changed), patch.object(publisher, "api") as api:
                code, _ = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
            self.assertEqual(code, 1)
            api.assert_not_called()
        self.pending.unlink()
        with patch.object(publisher, "api") as api:
            code, output = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 1)
        self.assertIn('"status": "reservation_required"', output)
        api.assert_not_called()

    def test_dry_run_reports_existing_hold_without_writes(self):
        original_output = self.output.read_text()
        with patch.object(publisher, "api") as api:
            code, output = self.run_main(DRY_RUN="1")
        self.assertEqual(code, 1)
        self.assertIn('"status": "reservation_held"', output)
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)
        self.assertEqual(self.output.read_text(), original_output)
        api.assert_not_called()

    def test_live_date_override_is_rejected_before_any_action(self):
        with patch.object(publisher, "api") as api:
            code, output = self.run_main(BUILD_DATE="2026-11-20", RESERVE_ONLY="1")
        self.assertEqual(code, 1)
        self.assertIn('"status": "invalid_date_override"', output)
        self.assertEqual(json.loads(self.pending.read_text()), self.hold)
        api.assert_not_called()

    def test_public_text_removes_only_http_autolink_markup(self):
        body = 'Read <https://example.com/proof?a=1&b=2> or <http://example.com>. Keep <tag> and [note].'
        expected = 'Read https://example.com/proof?a=1&b=2 or http://example.com. Keep <tag> and [note].'
        self.assertEqual(publisher.public_text(body), expected)
        self.assertIn(r'Keep \<tag\> and \[note\].', publisher.little_text(publisher.public_text(body)))

    def test_autolinks_are_plain_in_both_dry_preview_and_live_payload(self):
        self.path.write_text(self.original.decode().replace("Proof before slogans.", "Read <https://example.com/proof>."))
        self.pending.unlink()
        code, output = self.run_main(DRY_RUN="1")
        self.assertEqual(code, 0)
        self.assertIn("Read https://example.com/proof.", output)
        self.assertNotIn("<https://", output)
        self.pending.write_text(json.dumps(self.hold))
        with patch.object(publisher, "api", side_effect=[(200, {}, '{"sub":"test-member"}'),
                                                        (201, {"x-restli-id": "urn:li:share:123456789"}, "{}")]) as api:
            code, _ = self.run_main(LINKEDIN_ACCESS_TOKEN="test-only-token")
        self.assertEqual(code, 0)
        self.assertEqual(api.call_args_list[1].args[3]["commentary"], "Read https://example.com/proof.")

    def test_campaign_gap_is_nonzero_even_without_credentials(self):
        self.pending.unlink()
        code, output = self.run_main(day="2026-10-28")
        self.assertEqual(code, 1)
        self.assertIn('"status": "selection_error"', output)
        self.assertIn("Ordinary backlog will not be substituted", output)

    def test_bad_config_is_not_silently_ignored(self):
        config = self.root / "schedule.json"
        config.write_text('{"base_weekdays": [7]}')
        with patch.object(publisher, "SCHEDULE", config):
            code, output = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('"status": "selection_error"', output)


class RepositoryQueueTests(unittest.TestCase):
    """Keep the actual four-week queue complete as publication changes status."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.config = publisher.load_schedule(cls.root / "content" / "linkedin_schedule.json")
        cls.campaign = next(c for c in cls.config["campaigns"] if c["name"] == "2036")
        cls.posts = []
        for path in sorted((cls.root / "content" / "posts").glob("*.md")):
            meta, body = publisher.parse(path.read_text(encoding="utf-8"))
            if meta:
                cls.posts.append((path, meta, body))
        cls.start = date(2026, 10, 26)
        cls.end = date(2026, 11, 20)
        cls.window = [cls.start + timedelta(days=n) for n in range((cls.end - cls.start).days + 1)]

    def assert_publishable_record(self, post):
        path, meta, body = post
        self.assertEqual(path.name[:10], meta["date"], f"Filename and frontmatter date differ: {path.name}")
        self.assertTrue(meta.get("title", "").strip(), path.name)
        self.assertTrue(body.strip(), path.name)
        self.assertIn(meta.get("status"), ("approved", "published"), path.name)
        if meta["status"] == "published":
            self.assertTrue(publisher.valid_receipt(meta.get("linkedin_url", "")), f"Published post needs its receipt: {path.name}")
        else:
            self.assertFalse(meta.get("linkedin_url", "").strip(), f"Approved post already has a receipt: {path.name}")

    def test_actual_campaign_has_eleven_unique_correctly_marked_posts(self):
        self.assertEqual(self.campaign["start"], str(self.start))
        self.assertEqual(self.campaign["end"], str(self.end))
        self.assertEqual(self.campaign["weekdays"], [0, 2, 4])
        marked = [p for p in self.posts if p[1].get("series") == "2036" or p[1].get("linkedin_schedule") == "2036"]
        expected = [str(d) for d in self.window if d.weekday() in [0, 2, 4] and d != self.start]
        self.assertEqual(len(marked), 11)
        self.assertEqual(sorted(p[1]["date"] for p in marked), expected)
        for post in marked:
            with self.subTest(path=post[0].name):
                self.assertEqual(post[1].get("series"), "2036")
                self.assertEqual(post[1].get("linkedin_schedule"), "2036")
                self.assert_publishable_record(post)

    def test_actual_queue_and_manual_receipt_cover_twenty_dates_five_per_week(self):
        self.assertEqual(self.config["base_weekdays"], [1, 3])
        self.assertEqual(self.campaign["manual_dates"], [str(self.start)])
        self.assertEqual(self.campaign["manual_receipts"], {
            str(self.start): "https://www.linkedin.com/feed/update/urn:li:share:7520443246674878464/"
        })
        ordinary = [p for p in self.posts if self.start <= date.fromisoformat(p[1]["date"]) <= self.end
                    and not p[1].get("linkedin_schedule") and p[1].get("series") != "2036"]
        ordinary_dates = sorted(p[1]["date"] for p in ordinary)
        self.assertEqual(len(ordinary), 8)
        self.assertEqual(ordinary_dates, [str(d) for d in self.window if d.weekday() in [1, 3]])
        for post in ordinary:
            with self.subTest(path=post[0].name):
                self.assert_publishable_record(post)
        campaign_dates = [p[1]["date"] for p in self.posts if p[1].get("linkedin_schedule") == "2036"]
        all_dates = ordinary_dates + campaign_dates + self.campaign["manual_dates"]
        self.assertEqual(len(all_dates), 20)
        self.assertEqual(len(set(all_dates)), 20)
        self.assertEqual(sorted(all_dates), [str(d) for d in self.window if d.weekday() < 5])
        for week in range(4):
            monday = self.start + timedelta(days=7 * week)
            self.assertEqual(sum(monday <= date.fromisoformat(d) < monday + timedelta(days=7) for d in all_dates), 5)

    def test_actual_campaign_cannot_publish_before_or_after_its_window(self):
        # Existing receipts may legitimately make a later audit return
        # already_published. Neither state is permission to publish a campaign.
        for day in ("2026-10-23", "2026-11-23", "2026-11-25", "2026-11-27"):
            with self.subTest(day=day):
                selected = publisher.select_post(self.posts, self.config, date.fromisoformat(day), True)
                self.assertIn(selected.status, ("outside_schedule", "already_published"))

    def test_actual_campaign_autolinks_become_plain_linkedin_urls(self):
        checked_links = 0
        for path, meta, body in self.posts:
            if meta.get("linkedin_schedule") == "2036":
                with self.subTest(path=path.name):
                    rendered = publisher.public_text(body)
                    self.assertNotIn("<https://", rendered)
                    self.assertNotIn("<http://", rendered)
                    for link in re.findall(r"<(https?://[^<>\s]+)>", body):
                        checked_links += 1
                        self.assertIn(link, rendered)
        self.assertEqual(checked_links, 6, "Exercise all six links in the actual campaign queue.")


if __name__ == "__main__":
    unittest.main()
