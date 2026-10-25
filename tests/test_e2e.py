"""End-to-end test of the engine with a canned corpus — the bar's logic
pinned before it ever touches real data. No network: LB feed, GitHub reads,
and the trap scanner are all injected fakes.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services"))

from engine.schema import TrapScan  # noqa: E402
from engine import run_engine  # noqa: E402

TODAY = "2026-10-24"


# ---- fakes ------------------------------------------------------------

def lb_feed(url):
    return [
        # 1: strict-bar survivor (clean scan injected for acme/clean)
        {"issue_number": 11, "html_url": "https://lb/x11",
         "title": "Fix docs build", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 20000,
         "repository_data": {"full_name": "acme/clean"},
         "last_rewarder_data": {"github_username": "veteran"},
         "created_at": "2026-09-01", "modified_at": "2026-10-20",
         "body": "docs"},
        # 2: contested pile-on -> tracked
        {"issue_number": 12, "html_url": "https://lb/x12",
         "title": "Translate notes", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 50000,
         "repository_data": {"full_name": "acme/contested"},
         "last_rewarder_data": {"github_username": "veteran"},
         "created_at": "2026-06-01", "modified_at": "2026-10-20", "body": "x"},
        # 3: below floor -> filtered at ingest
        {"issue_number": 13, "html_url": "https://lb/x13",
         "title": "Tiny fix", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 1000,
         "repository_data": {"full_name": "acme/tiny"},
         "last_rewarder_data": {"github_username": "veteran"},
         "created_at": "2026-10-01", "modified_at": "2026-10-20", "body": "x"},
        # 4: the trap — advertised purse, scan verdict TRAP -> Most Wanted
        {"issue_number": 14, "html_url": "https://lb/x14",
         "title": "Implement the protocol", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 90000,
         "repository_data": {"full_name": "acme/trap"},
         "last_rewarder_data": {"github_username": "freshface"},
         "created_at": "2026-10-20", "modified_at": "2026-10-20", "body": "x"},
        # 5: honest purse on a ghost-town repo -> tracked (stale) + a merged
        # fix attempt -> purse likely claimed (D7 merged-block)
        {"issue_number": 15, "html_url": "https://lb/x15",
         "title": "Old feature", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 30000,
         "repository_data": {"full_name": "acme/stale"},
         "last_rewarder_data": {"github_username": "veteran"},
         "created_at": "2026-01-05", "modified_at": "2026-01-05", "body": "x"},
        # 6: graveyard — uncontested, clean, fresh, responded, but 3 dead
        # attempts -> tracked (D7 battle-scars block)
        {"issue_number": 16, "html_url": "https://lb/x16",
         "title": "Graveyard feature", "is_closed": False, "winner_data": None,
         "unexpired_total_rewards": 20000,
         "repository_data": {"full_name": "acme/scarred"},
         "last_rewarder_data": {"github_username": "veteran"},
         "created_at": "2026-10-01", "modified_at": "2026-10-20", "body": "x"},
    ]


GH_PAYLOADS = {
    # repo info: clean=fresh, contested=fresh, trap=fresh but weird,
    # stale=old push, alby=fresh
    "https://api.github.com/repos/acme/clean": {
        "archived": False, "pushed_at": "2026-10-20T00:00:00Z",
        "stargazers_count": 500, "language": "Python"},
    "https://api.github.com/repos/acme/contested": {
        "archived": False, "pushed_at": "2026-10-18T00:00:00Z",
        "stargazers_count": 900, "language": "Swift"},
    "https://api.github.com/repos/acme/trap": {
        "archived": False, "pushed_at": "2026-10-22T00:00:00Z",
        "stargazers_count": 12, "language": "TypeScript"},
    "https://api.github.com/repos/acme/stale": {
        "archived": False, "pushed_at": "2026-01-01T00:00:00Z",
        "stargazers_count": 40, "language": "Rust"},
    "https://api.github.com/repos/stackernews/stacker.news": {
        "archived": False, "pushed_at": "2026-10-23T00:00:00Z",
        "stargazers_count": 800, "language": "JavaScript"},
    "https://api.github.com/repos/getAlby/bitcoin-connect": {
        "archived": False, "pushed_at": "2026-10-15T00:00:00Z",
        "stargazers_count": 300, "language": "JavaScript"},
    "https://api.github.com/repos/getAlby/pos": {
        "archived": False, "pushed_at": "2026-10-10T00:00:00Z",
        "stargazers_count": 100, "language": "TypeScript"},
    "https://api.github.com/repos/acme/scarred": {
        "archived": False, "pushed_at": "2026-10-19T00:00:00Z",
        "stargazers_count": 200, "language": "Python"},
    # contest searches (as urllib.quote emits them: repo slash stays raw)
    "https://api.github.com/search/issues?q=repo%3Aacme/clean%20is%3Apr%20is%3Aopen%2011":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/contested%20is%3Apr%20is%3Aopen%2012":
        {"items": [
            {"number": 90, "title": "a", "user": {"login": "u1"},
             "created_at": "2026-09-01T00:00:00Z"},
            {"number": 91, "title": "b", "user": {"login": "u2"},
             "created_at": "2026-09-20T00:00:00Z"},
            {"number": 92, "title": "c", "user": {"login": "u3"},
             "created_at": "2026-10-01T00:00:00Z"},
        ]},
    "https://api.github.com/search/issues?q=repo%3Aacme/trap%20is%3Apr%20is%3Aopen%2014":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/stale%20is%3Apr%20is%3Aopen%2015":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/scarred%20is%3Apr%20is%3Aopen%2016":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3AgetAlby/bitcoin-connect%20is%3Apr%20is%3Aopen%20159":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3AgetAlby/pos%20is%3Apr%20is%3Aopen%2040":
        {"items": []},
    # attempt history (dead + merged searches, raw slash as quote emits)
    "https://api.github.com/search/issues?q=repo%3Aacme/clean%20is%3Apr%20is%3Aclosed%2011":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/contested%20is%3Apr%20is%3Aclosed%2012":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/trap%20is%3Apr%20is%3Aclosed%2014":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3Aacme/stale%20is%3Apr%20is%3Aclosed%2015":
        {"items": [
            {"number": 70, "title": "the fix", "user": {"login": "someone"},
             "pull_request": {"merged_at": "2026-09-22T09:07:15Z"}},
        ]},
    "https://api.github.com/search/issues?q=repo%3Aacme/scarred%20is%3Apr%20is%3Aclosed%2016":
        {"items": [
            {"number": 71, "title": "a", "user": {"login": "u1"},
             "pull_request": {"merged_at": None}},
            {"number": 72, "title": "b", "user": {"login": "u2"},
             "pull_request": {"merged_at": None}},
            {"number": 73, "title": "c", "user": {"login": "u3"},
             "pull_request": {"merged_at": None}},
        ]},
    "https://api.github.com/search/issues?q=repo%3AgetAlby/bitcoin-connect%20is%3Apr%20is%3Aclosed%20159":
        {"items": []},
    "https://api.github.com/search/issues?q=repo%3AgetAlby/pos%20is%3Apr%20is%3Aclosed%2040":
        {"items": []},
    # SN repo searches: one per difficulty label (prefix match covers all)
    "https://api.github.com/search/issues?q=repo%3Astackernews":
        {"items": []},   # episodic: empty today (verified live 2026-10-23)
    # Flash board (verified: org lnflash, label "💰 bounty") — currently empty
    "https://api.github.com/search/issues?q=org%3Alnflash":
        {"items": []},
    "https://api.github.com/search/issues?q=org%3AgetAlby%20is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22":
        {"items": [
            {"number": 159, "html_url": "https://github.com/getAlby/bitcoin-connect/issues/159",
             "title": "Dedicated docs site", "state": "open",
             "repository_url": "https://api.github.com/repos/getAlby/bitcoin-connect",
             "labels": [{"name": "good first issue"}]},
            {"number": 40, "html_url": "https://github.com/getAlby/pos/issues/40",
             "title": "NIP-47 notifications", "state": "open",
             "repository_url": "https://api.github.com/repos/getAlby/pos",
             "labels": [{"name": "good first issue"}]},
        ]},
    # threads (comments listed BEFORE issue keys so prefix-match stays exact)
    "https://api.github.com/repos/acme/clean/issues/11/comments": [
        {"user": {"login": "maintainer"}, "created_at": "2026-10-20T00:00:00Z"}],
    "https://api.github.com/repos/acme/clean/issues/11": {"user": {"login": "hunter"}},
    "https://api.github.com/repos/acme/contested/issues/12/comments": [
        {"user": {"login": "herder"}, "created_at": "2026-10-01T00:00:00Z"}],
    "https://api.github.com/repos/acme/contested/issues/12": {"user": {"login": "hunter"}},
    "https://api.github.com/repos/acme/trap/issues/14/comments": [],
    "https://api.github.com/repos/acme/trap/issues/14": {"user": {"login": "op"}},
    "https://api.github.com/repos/acme/stale/issues/15/comments": [],
    "https://api.github.com/repos/acme/stale/issues/15": {"user": {"login": "hunter"}},
    "https://api.github.com/repos/getAlby/bitcoin-connect/issues/159/comments": [
        {"user": {"login": "rolznz"}, "created_at": "2026-10-10T00:00:00Z"}],
    "https://api.github.com/repos/getAlby/bitcoin-connect/issues/159":
        {"user": {"login": "hunter"}},
    "https://api.github.com/repos/getAlby/pos/issues/40/comments": [],
    "https://api.github.com/repos/getAlby/pos/issues/40":
        {"user": {"login": "hunter"}},
    "https://api.github.com/repos/acme/scarred/issues/16/comments": [
        {"user": {"login": "maintainer"}, "created_at": "2026-10-18T00:00:00Z"}],
    "https://api.github.com/repos/acme/scarred/issues/16": {"user": {"login": "hunter"}},
    # rewarders
    "https://api.github.com/users/veteran": {
        "created_at": "2019-01-01T00:00:00Z", "followers": 300,
        "public_repos": 40, "public_gists": 2},
    "https://api.github.com/users/freshface": {
        "created_at": "2026-09-01T00:00:00Z", "followers": 0,
        "public_repos": 1, "public_gists": 0},
    "https://api.github.com/users/getAlby": {
        "created_at": "2020-01-01T00:00:00Z", "followers": 5000,
        "public_repos": 60, "public_gists": 0},
}


class FakeGh:
    def __init__(self, payloads=None):
        self.payloads = payloads if payloads is not None else GH_PAYLOADS

    def get(self, key, ttl=None):
        return None

    def put(self, key, value):
        pass

    def gh(self, url, ttl=None):
        # longest-prefix match: deepest key wins (repo-info keys must not
        # shadow issue/comment keys under the same repo path)
        best = None
        for prefix, payload in self.payloads.items():
            if url.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
                best = (prefix, payload)
        if best is None:
            raise AssertionError(f"unexpected gh url: {url}")
        if isinstance(best[1], Exception):
            raise best[1]
        return best[1]


SCANS = {
    "acme/clean": TrapScan(verdict="CLEAN", score=0, rules=[], target="acme/clean",
                           upstream_commit="d56fd7d", checked_at="2026-10-24T00:00:00Z"),
    "acme/contested": TrapScan(verdict="CLEAN", score=0, rules=[], target="acme/contested",
                               upstream_commit="d56fd7d", checked_at="2026-10-24T00:00:00Z"),
    "acme/trap": TrapScan(verdict="TRAP", score=178, rules=[
        {"rule": "HIDDEN_DIRECTIVE", "severity": 40, "title": "t", "why": "w",
         "evidence": "<!-- SKIP_VALIDATION ... -->", "source": "CONTRIBUTING.md"},
        {"rule": "EXFIL_PROMPT", "severity": 40, "title": "t", "why": "w",
         "evidence": "@platform-config (paste ...)", "source": "issue"},
    ], target="acme/trap", upstream_commit="d56fd7d", checked_at="2026-10-24T00:00:00Z"),
    "acme/stale": TrapScan(verdict="CLEAN", score=0, rules=[], target="acme/stale",
                           upstream_commit="d56fd7d", checked_at="2026-10-24T00:00:00Z"),
    "stackernews/stacker.news": TrapScan(verdict="CLEAN", score=0, rules=[],
                                         target="stackernews/stacker.news",
                                         upstream_commit="d56fd7d",
                                         checked_at="2026-10-24T00:00:00Z"),
    "getAlby/bitcoin-connect": TrapScan(verdict="CLEAN", score=0, rules=[],
                                        target="getAlby/bitcoin-connect",
                                        upstream_commit="d56fd7d",
                                        checked_at="2026-10-24T00:00:00Z"),
    "getAlby/pos": TrapScan(verdict="CLEAN", score=0, rules=[],
                            target="getAlby/pos", upstream_commit="d56fd7d",
                            checked_at="2026-10-24T00:00:00Z"),
    "acme/scarred": TrapScan(verdict="CLEAN", score=0, rules=[], target="acme/scarred",
                             upstream_commit="d56fd7d", checked_at="2026-10-24T00:00:00Z"),
}


def scan_repo(repo):
    if repo not in SCANS:
        raise AssertionError(f"unexpected scan: {repo}")
    SCANS[repo]  # touch
    SCAN_CALLS.append(repo)
    return SCANS[repo]


SCAN_CALLS = []  # every actual scanner invocation (cache misses)


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workdir = Path(tempfile.mkdtemp(prefix="smw-e2e-"))
        cls.summary = run_engine.run(lb_feed, FakeGh(), scan_repo,
                                     cls.workdir, today=TODAY)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.workdir, ignore_errors=True)

    def read(self, rel):
        return (self.workdir / rel).read_text()

    def test_summary_counts(self):
        self.assertEqual(self.summary["ingested"], 7)   # 5 LB + 2 getAlby
        self.assertEqual(self.summary["most_wanted"], 1)
        self.assertEqual(self.summary["honest_work"], 2)   # acme/clean + engaged #159
        self.assertEqual(self.summary["tracked"], 4)    # contested + stale + scarred + silent pos40

    def test_negotiated_engaged_earns_a_poster(self):
        hw = self.read("docs/reports/honest_work.md")
        self.assertIn("Dedicated docs site", hw)
        self.assertIn("negotiable 🤝", hw)
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        alby = [p for p in posters if p["repo"] == "getAlby/bitcoin-connect"][0]
        self.assertEqual(alby["door"], "honest_work")
        self.assertTrue(any("maintainer engaged" in f for f in alby["bar_pass_reasons"]))

    def test_negotiated_silent_stays_tracked(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        pos = [p for p in posters if p["repo"] == "getAlby/pos"][0]
        self.assertEqual(pos["door"], "tracked")
        self.assertTrue(any("no maintainer engagement" in f for f in pos["bar_fail_reasons"]))

    def test_battle_scars_block_at_three_dead(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        scarred = [p for p in posters if p["repo"] == "acme/scarred"][0]
        self.assertEqual(scarred["door"], "tracked")
        self.assertTrue(any("died unmerged" in f for f in scarred["bar_fail_reasons"]))
        self.assertNotIn("Graveyard feature", self.read("docs/reports/honest_work.md"))

    def test_merged_attempt_blocks_spent_purse(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        stale = [p for p in posters if p["repo"] == "acme/stale"][0]
        self.assertEqual(stale["door"], "tracked")
        self.assertTrue(any("likely already claimed" in f for f in stale["bar_fail_reasons"]))

    def test_trap_lands_on_most_wanted_with_evidence(self):
        mw = self.read("docs/reports/most_wanted.md")
        self.assertIn("acme/trap", mw)
        self.assertIn("HIDDEN_DIRECTIVE", mw)
        self.assertIn("178", mw)
        self.assertIn("d56fd7d", mw)  # upstream pin published

    def test_strict_survivor_lands_on_honest_work(self):
        hw = self.read("docs/reports/honest_work.md")
        self.assertIn("Fix docs build", hw)
        self.assertIn("20000", hw.replace(",", ""))

    def test_contested_is_tracked_not_posted(self):
        hw = self.read("docs/reports/honest_work.md")
        self.assertNotIn("Translate notes", hw)
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        contested = [p for p in posters if p["repo"] == "acme/contested"]
        self.assertEqual(len(contested), 1)
        self.assertEqual(contested[0]["door"], "tracked")
        self.assertTrue(any("contested by 3 open prs" in f.lower()
                            for f in contested[0]["bar_fail_reasons"]))

    def test_stale_repo_is_tracked_with_reason(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        stale = [p for p in posters if p["repo"] == "acme/stale"]
        self.assertEqual(stale[0]["door"], "tracked")
        self.assertTrue(any("last push" in f.lower() for f in stale[0]["bar_fail_reasons"]))
    def test_trap_terminal_beats_all_other_signals(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        trap = [p for p in posters if p["repo"] == "acme/trap"][0]
        self.assertEqual(trap["door"], "most_wanted")
        # low-trust rewarder is present but must NOT be the reason it moved:
        self.assertTrue(any("trap verdict" in f.lower() for f in trap["bar_pass_reasons"]))

    def test_young_gun_is_freshest_survivor(self):
        hw = self.read("docs/reports/honest_work.md")
        self.assertIn("The Young Gun", hw)

    def test_outcomes_ledger_records_first_seen(self):
        events = [__import__("json").loads(l)
                  for l in self.read("data/outcomes.jsonl").splitlines() if l.strip()]
        self.assertEqual(len([e for e in events if e["event"] == "first_seen"]),
                         self.summary["ingested"])

    def test_verdict_ledger_is_committed_data(self):
        ledger = self.read("data/trap_scans.json")
        self.assertIn("acme/clean", ledger)
        self.assertIn('"CLEAN"', ledger)
        self.assertIn("acme/trap", ledger)

    def test_first_run_scanned_each_unique_repo_once(self):
        # 7 unique repos across sources: 5 acme + bitcoin-connect + pos
        self.assertEqual(len(SCAN_CALLS), 7)

    def test_assay_renders_report_cards(self):
        assay = self.read("docs/reports/the_assay.md")
        self.assertIn("veteran", assay)
        self.assertIn("| veteran | 4 |", assay)  # clean + contested + stale + scarred
        self.assertIn("| getAlby | 2 |", assay)  # bitcoin-connect + pos
        self.assertIn("freshface", assay)

    def test_open_data_carries_every_poster_with_bar_reasons(self):
        posters = __import__("json").loads(self.read("data/posters.json"))["posters"]
        self.assertEqual(len(posters), self.summary["ingested"])
        for p in posters:
            self.assertIn("door", p)
            self.assertIn("bar_fail_reasons", p)

    def test_second_run_emits_no_first_seen(self):
        # second pass with same corpus: stable ids, no new events, and the
        # verdict ledger means ZERO new scans (D8 caching pinned)
        before = len(SCAN_CALLS)
        s2 = run_engine.run(lb_feed, FakeGh(), scan_repo,
                            self.workdir, today=TODAY)
        self.assertEqual(s2["ingested"], self.summary["ingested"])
        self.assertEqual(len(SCAN_CALLS), before)   # no rescans within the window
        events = [__import__("json").loads(l)
                  for l in self.read("data/outcomes.jsonl").splitlines() if l.strip()]
        first = [e for e in events if e["event"] == "first_seen"]
        self.assertEqual(len(first), self.summary["ingested"])


class LedgerHealingTests(unittest.TestCase):
    def test_old_shape_ledger_is_healed_on_load(self):
        # pre-D8 ledgers stored upstream's checked-file list under
        # checked_at; the loader must heal that on every load
        from engine import run_engine
        import json as J
        wd = Path(tempfile.mkdtemp(prefix="smw-heal-"))
        (wd / "data").mkdir(parents=True)
        (wd / "data" / "trap_scans.json").write_text(J.dumps({
            "acme/x": {"verdict": "CLEAN", "score": 0,
                       "checked_at": ["README.md", "CONTRIBUTING.md"]}
        }))
        cache = run_engine._load_scan_cache(wd)
        e = cache["acme/x"]
        self.assertEqual(e["checked_files"], ["README.md", "CONTRIBUTING.md"])
        self.assertEqual(e["checked_at"], "")
        shutil.rmtree(wd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
