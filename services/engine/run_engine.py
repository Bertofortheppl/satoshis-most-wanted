"""One-shot engine assembly: ingest → enrich → trap-scan → bar → outcomes
→ render. Fully injectable for hermetic E2E (tests/test_e2e.py).

Live usage:  python3 -m services.engine.run_engine --live
  reads GITHUB_TOKEN from the environment for GitHub rate limits
  state/  (gitignored) caches; data/ is the committed open data.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from . import github as ghmod
from . import outcomes as outcomes_mod
from . import render as render_mod
from . import bar as bar_mod
from .adapters import lb as lb_adapter
from .adapters import github_org as gh_adapter
from .sources_config import SOURCES
from .schema import Poster, TrapScan

RESCAN_DAYS = 7


def _issue_number(p: Poster):
    ext = p.external_id
    if ext.startswith("lb-"):
        try:
            return int(ext[3:].split("-")[0])
        except ValueError:
            return None
    if "#" in ext:
        try:
            return int(ext.rsplit("#", 1)[1])
        except ValueError:
            return None
    return None


def _load_scan_cache(state_dir: Path) -> dict:
    f = state_dir / "trap_scans.json"
    return json.loads(f.read_text()) if f.exists() else {}


def _save_scan_cache(state_dir: Path, cache: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    f = state_dir / "trap_scans.json"
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2))
    tmp.replace(f)


def enrich(posters, gh, today=None):
    for p in posters:
        if not p.repo:
            continue
        num = _issue_number(p)
        health = ghmod.repo_health(gh, p.repo)
        p.repo_archived = health["archived"]
        p.repo_last_push = health["last_push"]
        if health.get("stars") is not None:
            pass  # stars reserved for the poster page later
        if num is not None:
            prs = ghmod.find_open_prs(gh, p.repo, num)
            p.contested_prs = len(prs)
            p.contest_detail = prs
            thread = ghmod.issue_thread(gh, p.repo, num)
            p.maintainer_responded = bool(thread["replies"])
            p.maintainer_last_reply_age_days = thread["last_reply_age_days"]
        if p.rewarder:
            p.rewarder_trust = ghmod.rate_rewarder(gh, p.rewarder)
        lang, _ = ghmod.language_of(gh, p.repo)
        p.language = lang
        p.last_checked = today or dt.date.today().isoformat()
    return posters


def trap_scan(posters, scan_repo, state_dir: Path, today=None, rescan_days=RESCAN_DAYS):
    today = today or dt.date.today().isoformat()
    cache = _load_scan_cache(state_dir)
    t = dt.date.fromisoformat(today)
    for p in posters:
        if not p.repo:
            continue
        hit = cache.get(p.repo)
        fresh = False
        if hit and hit.get("checked_date"):
            try:
                fresh = (t - dt.date.fromisoformat(hit["checked_date"])).days <= rescan_days
            except ValueError:
                fresh = False
        if not fresh:
            trap = scan_repo(p.repo)
            if trap is not None:
                cache[p.repo] = {
                    "verdict": trap.verdict, "score": trap.score,
                    "rules": trap.rules, "target": trap.target,
                    "upstream_commit": trap.upstream_commit,
                    "checked_at": trap.checked_at, "checked_date": today,
                }
                hit = cache[p.repo]
        if hit:
            p.trap = TrapScan(
                verdict=hit["verdict"], score=hit["score"],
                rules=hit.get("rules", []), target=hit.get("target", ""),
                upstream_commit=hit.get("upstream_commit", ""),
                checked_at=hit.get("checked_at", ""),
            )
    _save_scan_cache(state_dir, cache)
    return posters


def run(fetch_lb, gh, scan_repo, workdir: Path, today=None) -> dict:
    """Returns a summary dict; writes data/ + docs/reports/."""
    today = today or dt.date.today().isoformat()
    data_dir = workdir / "data"
    state_dir = workdir / "state"
    reports_dir = workdir / "docs" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)

    posters: list[Poster] = []
    for cfg in SOURCES:
        if not cfg.get("enabled"):
            continue
        if cfg["kind"] == "lb":
            posters.extend(lb_adapter.fetch(fetch_lb, cfg, today=today))
        elif cfg["kind"] == "github":
            posters.extend(gh_adapter.fetch(gh, cfg, today=today))

    posters = enrich(posters, gh, today=today)
    posters = trap_scan(posters, scan_repo, state_dir, today=today)

    mw, hw, young_gun, tracked = bar_mod.rank_doors(posters)

    prev = []
    prev_path = data_dir / "posters.json"
    if prev_path.exists():
        try:
            prev = json.loads(prev_path.read_text())["posters"]
        except Exception:
            prev = []
    curr = [p.to_dict() for p in posters]
    events = outcomes_mod.diff(prev, curr)
    for e in events:
        outcomes_mod.append(data_dir / "outcomes.jsonl", e)
    all_events = outcomes_mod.load(data_dir / "outcomes.jsonl")
    cards = outcomes_mod.report_cards(curr, all_events)

    write = lambda p, d, pa, f: (p, d, pa, f)  # noqa: E731
    all_meta = ([write(p, "most_wanted", pa, f) for p, pa, f in mw]
                + [write(p, "honest_work", pa, f) for p, pa, f in hw]
                + [write(p, "tracked", pa, f) for p, pa, f in tracked])
    files = {
        "posters": str(render_mod.write_posters(all_meta, data_dir)),
        "most_wanted": str(render_mod.render_most_wanted(mw, reports_dir)),
        "honest_work": str(render_mod.render_honest_work(hw, young_gun, reports_dir)),
        "the_assay": str(render_mod.render_assay(cards, reports_dir)),
    }
    return {
        "ingested": len(posters),
        "most_wanted": len(mw),
        "honest_work": len(hw),
        "tracked": len(tracked),
        "events": len(events),
        "files": files,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Satoshi's Most Wanted engine")
    ap.add_argument("--live", action="store_true", help="run against live sources")
    ap.add_argument("--workdir", default=str(Path(__file__).resolve().parents[2]))
    args = ap.parse_args(argv)
    if not args.live:
        ap.print_help()
        return 2

    token = os.environ.get("GITHUB_TOKEN", "")
    gh = ghmod.GhCache(Path(args.workdir) / "state", token=token)

    def fetch_lb(url):
        items, skip, page = [], 0, 100
        while True:
            batch = ghmod.http_json(f"{url}?distinct_issues=true&skip={skip}&limit={page}")
            if not batch:
                break
            items.extend(batch)
            if len(batch) < page:
                break
            skip += page
        return items

    from .trapscan import scan_github
    scan = lambda repo: scan_github(repo, token=token or None)  # noqa: E731
    summary = run(fetch_lb, gh, scan, Path(args.workdir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
