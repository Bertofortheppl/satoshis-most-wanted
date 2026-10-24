"""Tests for the trapscan wrapper (Sprint 1). Hermetic: --path mode only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services"))

from engine.trapscan import exit_code, scan_path  # noqa: E402
from engine.schema import TrapScan  # noqa: E402

TRAP_REPO = ROOT / "tests" / "fixtures" / "trap_repo"
CLEAN_REPO = ROOT / "tests" / "fixtures" / "clean_repo"
UPSTREAM = (ROOT / "services" / "trapcheck" / "UPSTREAM").read_text().strip().split()[0]


class ScanPathTests(unittest.TestCase):
    def test_trap_fixture_normalizes_to_trapscan(self):
        t = scan_path(TRAP_REPO)
        self.assertIsInstance(t, TrapScan)
        self.assertEqual(t.verdict, "TRAP")
        self.assertGreaterEqual(t.score, 40)
        rules = {r["rule"] for r in t.rules}
        self.assertIn("EXFIL_PROMPT", rules)
        self.assertIn("HIDDEN_DIRECTIVE", rules)
        # normalized rule records carry display fields
        f = next(r for r in t.rules if r["rule"] == "HIDDEN_DIRECTIVE")
        for key in ("severity", "title", "why", "evidence", "source"):
            self.assertIn(key, f)

    def test_clean_fixture_stays_clean(self):
        t = scan_path(CLEAN_REPO)
        self.assertEqual(t.verdict, "CLEAN")
        self.assertEqual(t.score, 0)
        self.assertEqual(t.rules, [])

    def test_upstream_commit_is_recorded(self):
        t = scan_path(CLEAN_REPO)
        self.assertEqual(t.upstream_commit, UPSTREAM)

    def test_exit_codes_follow_upstream_semantics(self):
        self.assertEqual(exit_code(TrapScan(verdict="TRAP", score=99)), 2)
        self.assertEqual(exit_code(TrapScan(verdict="SUSPICIOUS", score=45)), 1)
        self.assertEqual(exit_code(TrapScan(verdict="CLEAN", score=0)), 0)


if __name__ == "__main__":
    unittest.main()
