"""Hermetic tests for engine/github.py using a fake transport.

The `gh` object is injected (same design as the scout we lifted from), so
all logic below runs without network. Live behavior was already proven by
the scout's two months of unattended cron runs.
"""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services"))

from engine import github as ghmod  # noqa: E402


class FakeGh:
    """Records reads, returns canned payloads."""

    def __init__(self, payloads=None):
        self.payloads = payloads or {}
        self.reads = []

    def get(self, key, ttl=None):
        return None

    def put(self, key, value):
        pass

    def gh(self, url, ttl=None):
        self.reads.append(url)
        for prefix, payload in self.payloads.items():
            if url.startswith(prefix):
                if isinstance(payload, Exception):
                    raise payload
                return payload
        raise AssertionError(f"unexpected url: {url}")


REPO = {
    "archived": False,
    "pushed_at": "2026-10-20T12:00:00Z",
    "stargazers_count": 1234,
    "language": "TypeScript",
}


class RepoHealthTests(unittest.TestCase):
    def test_repo_health_from_repo_info(self):
        gh = FakeGh({"https://api.github.com/repos/acme/widgets": REPO})
        h = ghmod.repo_health(gh, "acme/widgets")
        self.assertEqual(h, {"archived": False, "last_push": "2026-10-20", "stars": 1234})

    def test_repo_health_survives_api_error(self):
        gh = FakeGh({"https://api.github.com/repos/acme/gone": RuntimeError("boom")})
        h = ghmod.repo_health(gh, "acme/gone")
        self.assertFalse(h["archived"])
        self.assertIsNone(h["last_push"])


class AttemptHistoryTests(unittest.TestCase):
    """Timeline-authoritative attempt data (one call, no search flakiness)."""

    def test_timeline_classifies_open_dead_merged(self):
        payloads = {"https://api.github.com/repos/acme/widgets/issues/7/timeline": [
            {"event": "cross-referenced", "source": {"issue": {
                "number": 90, "title": "open one", "state": "open",
                "user": {"login": "u1"}, "created_at": "2026-09-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/acme/widgets",
                "pull_request": {"merged_at": None}}}},
            {"event": "cross-referenced", "source": {"issue": {
                "number": 91, "title": "dead one", "state": "closed",
                "user": {"login": "u2"}, "created_at": "2026-05-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/acme/widgets",
                "pull_request": {"merged_at": None}}}},
            {"event": "cross-referenced", "source": {"issue": {
                "number": 92, "title": "merged one", "state": "closed",
                "user": {"login": "u3"}, "created_at": "2026-06-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/acme/widgets",
                "pull_request": {"merged_at": "2026-07-01T00:00:00Z"}}}},
            # cross-repo mention: cannot merge here -> ignored
            {"event": "cross-referenced", "source": {"issue": {
                "number": 93, "title": "cross repo", "state": "open",
                "user": {"login": "u4"}, "created_at": "2026-10-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/other/repo",
                "pull_request": {"merged_at": None}}}},
        ]}
        gh = FakeGh(payloads)
        h = ghmod.attempt_history(gh, "acme/widgets", 7)
        self.assertEqual(len(h["open"]), 1)
        self.assertEqual(len(h["dead"]), 1)
        self.assertEqual(len(h["merged"]), 1)
        self.assertEqual(h["open"][0]["number"], 90)
        self.assertIsInstance(h["open"][0]["age_days"], int)
        self.assertEqual(h["merged"][0]["number"], 92)

    def test_timeline_error_returns_all_empty(self):
        gh = FakeGh({"https://api.github.com/repos/acme/widgets/issues/8/timeline":
                     RuntimeError("x")})
        h = ghmod.attempt_history(gh, "acme/widgets", 8)
        self.assertEqual(h, {"open": [], "dead": [], "merged": []})


class IssueThreadTests(unittest.TestCase):
    def test_non_reporter_replies_counted(self):
        payloads = {
            "https://api.github.com/repos/acme/widgets/issues/7/comments": [
                {"user": {"login": "reporter"}, "created_at": "2026-10-01T00:00:00Z"},
                {"user": {"login": "maintainer"}, "created_at": "2026-10-15T00:00:00Z"},
            ],
            "https://api.github.com/repos/acme/widgets/issues/7": {
                "user": {"login": "reporter"},
            },
        }
        gh = FakeGh(payloads)
        t = ghmod.issue_thread(gh, "acme/widgets", 7)
        self.assertEqual(t["replies"], 1)
        self.assertIsInstance(t["last_reply_age_days"], int)

    def test_reporter_only_thread_is_zero_replies(self):
        payloads = {
            "https://api.github.com/repos/acme/widgets/issues/8/comments": [
                {"user": {"login": "reporter"}, "created_at": "2026-10-01T00:00:00Z"},
            ],
            "https://api.github.com/repos/acme/widgets/issues/8": {
                "user": {"login": "reporter"},
            },
        }
        gh = FakeGh(payloads)
        t = ghmod.issue_thread(gh, "acme/widgets", 8)
        self.assertEqual(t["replies"], 0)
        self.assertIsNone(t["last_reply_age_days"])


class RewarderTests(unittest.TestCase):
    def test_low_trust_flag_for_fresh_empty_account(self):
        gh = FakeGh({"https://api.github.com/users/newbie": {
            "created_at": "2026-09-01T00:00:00Z", "followers": 0,
            "public_repos": 1, "public_gists": 0,
        }})
        self.assertEqual(ghmod.rate_rewarder(gh, "newbie"), "low-trust")

    def test_ok_flag_for_established_account(self):
        gh = FakeGh({"https://api.github.com/users/veteran": {
            "created_at": "2019-01-01T00:00:00Z", "followers": 300,
            "public_repos": 40, "public_gists": 2,
        }})
        self.assertEqual(ghmod.rate_rewarder(gh, "veteran"), "ok")

    def test_unknown_username(self):
        self.assertEqual(ghmod.rate_rewarder(None, ""), "unknown")


if __name__ == "__main__":
    unittest.main()
