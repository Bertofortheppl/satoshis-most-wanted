"""Tests for the Assay's historical layer (LB feed mining)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services"))

from engine.assay_history import build_lb_history  # noqa: E402


def feed_item(title, rewarder, sats=10000, awarded=False, winner=None,
              cofunder=None, created="2026-01-01", claimed=None):
    it = {
        "title": title,
        "is_closed": False,
        "repository_data": {"full_name": "acme/x"},
        "last_rewarder_data": {"github_username": rewarder},
        "unexpired_total_rewards": sats,
        "total_reward_sats": sats,
        "created_at": created,
        "claimed_at": claimed,
        "winner_data": ({"github_username": winner} if awarded else None),
        "html_url": f"https://lb/{title[:4]}",
    }
    if cofunder:
        it["second_last_rewarder_data"] = {"github_username": cofunder}
    return it


class BuildLbHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = build_lb_history([
            feed_item("won", "veteran", sats=20000, awarded=True,
                      winner="tadeubas", created="2026-01-01",
                      claimed="2026-01-10"),
            feed_item("crowd", "veteran", sats=5000, awarded=True,
                      winner="geyln", cofunder="flashorg",
                       created="2026-02-01", claimed="2026-02-21"),
            feed_item("open1", "veteran", sats=3000),
            feed_item("open2", "flashorg", sats=4000),
            feed_item("stale-open", "ghost", sats=2000, created="2025-01-01"),
        ])

    def test_platform_totals(self):
        p = self.h["platform"]
        self.assertEqual(p["lifetime"], 5)
        self.assertEqual(p["awarded"], 2)
        self.assertEqual(p["open"], 3)
        self.assertEqual(p["sats_awarded"], 25000)

    def test_rewarder_cards_from_history(self):
        by = {c["rewarder"]: c for c in self.h["rewarders"]}
        v = by["veteran"]
        self.assertEqual(v["touched"], 3)
        self.assertEqual(v["awarded"], 2)
        self.assertEqual(v["open"], 1)
        self.assertEqual(v["sats_awarded"], 25000)
        self.assertEqual(v["award_rate"], round(2 / 3, 2))
        # median of 9 and 20 days
        self.assertEqual(v["median_days_to_award"], 14)
        f = by["flashorg"]
        self.assertEqual(f["touched"], 2)      # crowd (co-funder) + open2
        self.assertEqual(f["awarded"], 1)
        self.assertEqual(f["sats_awarded"], 5000)

    def test_hunter_cards(self):
        by = {h["hunter"]: h for h in self.h["hunters"]}
        self.assertEqual(by["tadeubas"]["wins"], 1)
        self.assertEqual(by["tadeubas"]["sats"], 20000)
        self.assertEqual(by["geyln"]["sats"], 5000)

    def test_cards_sorted_by_sats(self):
        self.assertEqual(self.h["rewarders"][0]["rewarder"], "veteran")

    def test_no_awarded_days_is_none(self):
        by = {c["rewarder"]: c for c in self.h["rewarders"]}
        self.assertIsNone(by["ghost"]["median_days_to_award"])


if __name__ == "__main__":
    unittest.main()
