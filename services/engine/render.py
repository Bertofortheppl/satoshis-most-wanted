"""Render — the three doors as data (Sprint 1 review artifact).

Writes data/posters.json (the open data) + three markdown reports under
docs/reports/. No chrome: these ARE the product until Sprint 2.
"""
from __future__ import annotations

import json
from pathlib import Path

TRAP_LIMITS = ("Reads text only; samples newest issues; regex patterns are "
               "evadable; metadata signals are context, not intent. CLEAN "
               "means no agent-targeting patterns in the text checked, "
               "nothing more. (vendored trapcheck — see "
               "services/trapcheck/ATTRIBUTION.md)")

WALL_RULES = ("Strict bar (DECISIONS.md D6): escrow or documented paying "
              "schedule, trap scan CLEAN, repo alive and pushed recently, "
              "someone responded recently, contest at most one fresh PR, "
              "rewarder not low-trust, purse at least 2000 sats. Fail any "
              "gate and the item is tracked in open data without a poster.")


def _md(s) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def write_posters(posters_with_meta, outdir: Path) -> Path:
    """posters_with_meta: list of (poster, door, passes, fails)."""
    data = []
    for p, door, passes, fails in posters_with_meta:
        d = p.to_dict()
        d["door"] = door
        d["bar_pass_reasons"] = passes
        d["bar_fail_reasons"] = fails
        data.append(d)
    path = outdir / "posters.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"posters": data}, indent=2) + "\n")
    return path


def render_most_wanted(mw, outdir: Path) -> Path:
    lines = [
        "# Most Wanted — the traps",
        "",
        f"> {len(mw)} trap-verdict repositories. Scanner: vendored trapcheck, MIT,",
        "> agentatwork (agentatwork.xyz) — verdict limits apply:",
        f"> {TRAP_LIMITS}",
        "",
        "| Repo | Score | Decisive rules | Purse advertised | First seen |",
        "|---|---|---|---|---|",
    ]
    for p, _passes, _fails in mw:
        rules = ", ".join(p.trap.decisive_rules()) if p.trap else "aggregate"
        lines.append(
            f"| [{_md(p.repo)}]({_md(p.url)}) | {p.trap.score if p.trap else '?'} "
            f"| {_md(rules)} | {p.sats or 'n/a'} sats | {_md(p.first_seen)} |")
    lines += ["", "## Evidence", ""]
    for p, _passes, _fails in mw:
        if not p.trap:
            continue
        lines.append(f"### {_md(p.repo)} (score {p.trap.score})")
        for r in p.trap.rules[:5]:
            lines.append(f"- **{r['rule']}** (sev {r['severity']}): "
                          f"`{_md(r['evidence'])[:160]}`")
        lines.append(f"- scanned at `{_md(p.trap.checked_at)}` "
                     f"upstream `{p.trap.upstream_commit[:8]}`")
        lines.append("")
    path = outdir / "most_wanted.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def render_honest_work(hw, young_gun, outdir: Path) -> Path:
    lines = [
        "# Honest Work — verified clean opportunities",
        "",
        f"> {len(hw)} posters passed the strict bar. {WALL_RULES}",
        "",
    ]
    if young_gun:
        p, _passes, _fails = young_gun
        lines += [
            "## The Young Gun — freshest clean listing",
            "",
            f"- **[{_md(p.title)}]({_md(p.url)})** — {p.sats} sats, "
            f"{_md(p.source_label)}, uncontested, first seen {_md(p.first_seen)}",
            "",
            "## The wall",
            "",
            "| Score | Listing | Purse | Source | Contest | Repo pushed |",
            "|---|---|---|---|---|---|",
        ]
    for p, _passes, _fails in hw:
        contest = "clean" if p.contested_prs == 0 else f"{p.contested_prs} PR"
        lines.append(
            f"| {p.score:.0f} | [{_md(p.title)}]({_md(p.url)}) | {p.sats} sats "
            f"| {_md(p.source_label)} | {contest} | {_md(p.repo_last_push)} |")
    lines += [
        "",
        "## How you actually get paid (per source)",
        "",
    ]
    seen = set()
    for p, _passes, _fails in hw:
        if p.source in seen:
            continue
        seen.add(p.source)
        cm = p.claim_mechanics or {}
        lines.append(f"### {_md(p.source_label)}")
        for step in cm.get("steps", []):
            lines.append(f"- {step}")
        if cm.get("payment"):
            lines.append(f"- Payment: {cm['payment']}")
        if cm.get("gotchas"):
            lines.append(f"- Gotchas: {cm['gotchas']}")
        lines.append("")
    path = outdir / "honest_work.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def render_assay(cards, outdir: Path) -> Path:
    lines = [
        "# The Assay — rewarder report cards",
        "",
        "> Aggregated from the outcomes ledger (data/outcomes.jsonl). Honest",
        "> limitation: v1 observes only transitions our sources expose — no",
        "> invented payout numbers. The cards compound as tracking continues.",
        "",
        "| Rewarder | Listed | Awarded (observed) | Paid (observed) | Expired | Transitions seen |",
        "|---|---|---|---|---|---|",
    ]
    for c in cards:
        lines.append(
            f"| {_md(c['rewarder'])} | {c['listed']} | {c['awarded']} "
            f"| {c['paid']} | {c['expired']} | {c['seen_transitions']} |")
    path = outdir / "the_assay.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path
