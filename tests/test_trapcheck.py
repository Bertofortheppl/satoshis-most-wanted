"""Hermetic tests for the vendored trapcheck scanner (Sprint 1).

Runs the scanner in --path mode against local fixtures: no network, no
token, deterministic. These tests pin BOTH the fixture behavior and the
upstream rule engine we depend on — if upstream regresses (we re-vendor a
newer pinned copy), these tests tell us before any verdict is published.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "services" / "trapcheck" / "trapcheck.py"
TRAP_REPO = ROOT / "tests" / "fixtures" / "trap_repo"
CLEAN_REPO = ROOT / "tests" / "fixtures" / "clean_repo"


def scan(path: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCANNER), "--path", str(path), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError(
            f"scanner produced no JSON (rc={proc.returncode}): "
            f"{proc.stdout[:300]} {proc.stderr[:300]}"
        )


class TrapRepoTests(unittest.TestCase):
    """The miniature ClankerNation-pattern fixture must be a TRAP."""

    @classmethod
    def setUpClass(cls):
        cls.res = scan(TRAP_REPO)

    def test_verdict_is_trap(self):
        self.assertEqual(self.res["verdict"], "TRAP")

    def test_severity_40_rules_fired(self):
        rules = {f["rule"] for f in self.res["findings"]}
        self.assertIn("EXFIL_PROMPT", rules)
        self.assertIn("HIDDEN_DIRECTIVE", rules)

    def test_env_exfil_also_fires(self):
        rules = {f["rule"] for f in self.res["findings"]}
        self.assertIn("EXFIL_ENV", rules)

    def test_findings_carry_rule_metadata(self):
        for f in self.res["findings"]:
            self.assertIn("rule", f)
            self.assertIsInstance(f["severity"], int)
            self.assertTrue(f.get("evidence"))
        self.assertTrue(any(f["severity"] == 40 for f in self.res["findings"]))

    def test_score_reaches_trap_threshold(self):
        self.assertGreaterEqual(self.res["score"], 40)


class CleanRepoTests(unittest.TestCase):
    """An honest repo — including the 'never commit your API key' sentence
    that ate 32 false positives upstream — must stay CLEAN."""

    @classmethod
    def setUpClass(cls):
        cls.res = scan(CLEAN_REPO)

    def test_verdict_is_clean(self):
        self.assertEqual(self.res["verdict"], "CLEAN")

    def test_score_is_zero(self):
        self.assertEqual(self.res["score"], 0)

    def test_no_findings(self):
        self.assertEqual(self.res["findings"], [])


class ContractTests(unittest.TestCase):
    """The JSON contract our engine consumes (ATTRIBUTION.md #2)."""

    @classmethod
    def setUpClass(cls):
        cls.res = scan(TRAP_REPO)

    def test_required_keys_present(self):
        for key in ("verdict", "score", "findings", "target"):
            self.assertIn(key, self.res)

    def test_version_reported(self):
        self.assertTrue(self.res.get("version"))


if __name__ == "__main__":
    unittest.main()
