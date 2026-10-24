"""Tests for the unified poster schema (Sprint 1 contract layer)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services"))

from engine.schema import Poster, TrapScan, derive_id, validate  # noqa: E402


def sample_poster(**over) -> Poster:
    base = dict(
        id=derive_id("lightning_bounties", "lb-123"),
        source="lightning_bounties",
        source_label="Lightning Bounties",
        external_id="lb-123",
        title="Fix the thing",
        url="https://app.lightningbounties.com/x",
        sats=5000,
        escrow=True,
        repo="acme/widgets",
        first_seen="2026-10-24T00:00:00Z",
        last_checked="2026-10-24T00:00:00Z",
    )
    base.update(over)
    return Poster(**base)


class DeriveIdTests(unittest.TestCase):
    def test_ids_are_deterministic_and_source_scoped(self):
        a = derive_id("lightning_bounties", "lb-123")
        b = derive_id("lightning_bounties", "lb-123")
        c = derive_id("github_org", "lb-123")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(a.startswith("lightning_bounties-"))


class RoundtripTests(unittest.TestCase):
    def test_dict_roundtrip_preserves_fields(self):
        p = sample_poster(trap=TrapScan(verdict="TRAP", score=178,
                                         rules=[{"rule": "HIDDEN_DIRECTIVE",
                                                 "severity": 40, "title": "x",
                                                 "why": "y", "evidence": "z",
                                                 "source": "CONTRIBUTING.md"}],
                                         target="acme/widgets"))
        p2 = Poster.from_dict(p.to_dict())
        self.assertEqual(p2.id, p.id)
        self.assertEqual(p2.trap.verdict, "TRAP")
        self.assertEqual(p2.trap.rules[0]["rule"], "HIDDEN_DIRECTIVE")
        self.assertEqual(p2.sats, 5000)
        self.assertTrue(p2.to_dict()["schema_version"])

    def test_from_dict_tolerates_unknown_keys(self):
        d = sample_poster().to_dict()
        d["future_field"] = "ignored"
        p = Poster.from_dict(d)
        self.assertEqual(p.title, "Fix the thing")


class ValidateTests(unittest.TestCase):
    def test_valid_poster_has_no_problems(self):
        self.assertEqual(validate(sample_poster()), [])

    def test_id_external_id_mismatch_is_caught(self):
        p = sample_poster(external_id="lb-999")
        self.assertTrue(validate(p))

    def test_bad_verdict_is_caught(self):
        p = sample_poster(trap=TrapScan(verdict="MAYBE", score=1))
        self.assertTrue(validate(p))

    def test_bad_status_is_caught(self):
        self.assertTrue(validate(sample_poster(status="vibes")))


class TrapScanTests(unittest.TestCase):
    def test_decisive_rules_are_severity_40(self):
        t = TrapScan(verdict="TRAP", score=178, rules=[
            {"rule": "HIDDEN_DIRECTIVE", "severity": 40},
            {"rule": "URGENCY", "severity": 8},
        ])
        self.assertEqual(t.decisive_rules(), ["HIDDEN_DIRECTIVE"])


if __name__ == "__main__":
    unittest.main()
