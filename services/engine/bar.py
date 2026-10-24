"""The bar — DECISIONS.md D6 as executable logic, plus door assignment.

D6 (owner 2026-10-24): STRICT wall. A poster on Honest Work requires ALL
gates. Everything else is tracked in open data without a poster.

Doors (SPEC v2):
  most_wanted  trap-verdict posters (the wall of outlaws)
  honest_work  strict-bar survivors (the wall of honest work)
  tracked      everything else (open data only — no poster)

Every failure reason is recorded and rendered, so a reader can always ask
"why isn't X on the wall?" and get an answer.
"""
from __future__ import annotations

# ---- The strict bar (D6). Every knob documented; changes require a
# ---- DECISIONS.md entry with rationale.
MIN_SATS = 2000                # floor: below this is noise, not work
MAX_CONTESTED_PRS = 1          # 0 ideal; 1 tolerated only if fresh
MAX_PR_AGE_DAYS = 30          # an old open PR = silent queue (Primal #206)
MAX_REPO_STALE_DAYS = 90      # ghost-town guard (Branta lesson)
MAX_RESPONDER_AGE_DAYS = 60   # someone alive on the other side, recently
REQUIRE_ESCROW_OR_SCHEDULE = True
REQUIRE_TRAP_CLEAN = True     # CLEAN only; CAUTION/SUSPICIOUS tracked, not posted
REQUIRE_RESPONDED = True
RESCAN_NOTE = "trap scans re-run weekly (cache in state/)"
BATTLE_SCARS_BLOCK_AT = 3        # D7: >2 dead attempts = no poster (owner wording)
MERGED_ATTEMPT_BLOCKS = True     # D7: merged fix = purse likely claimed
EXCLUDE_NEGOTIATED = False       # D7: negotiated included IF maintainer engaged
EXCLUDED_SOURCES = set()      # e.g. SN micro-contest lanes if ever ingested


def trap_door(trap) -> str:
    """TRAP verdicts go to Most Wanted; anything softer stays tracked."""
    if trap is not None and trap.verdict == "TRAP":
        return "most_wanted"
    return "tracked"


def check(p) -> tuple[str, list[str], list[str]]:
    """Returns (door, pass_reasons, fail_reasons)."""
    fails: list[str] = []
    passes: list[str] = []

    # Traps first: a TRAP verdict is terminal — it can never be honest work.
    if p.trap is not None and p.trap.verdict == "TRAP":
        rules = ", ".join(p.trap.decisive_rules()) or "aggregate"
        return "most_wanted", [f"trap verdict: {p.trap.verdict} ({rules})"], []

    if p.source in EXCLUDED_SOURCES:
        fails.append(f"source excluded: {p.source}")
    cm = p.claim_mechanics or {}
    negotiated = bool(cm.get("negotiated"))
    if negotiated:
        # D7: negotiated lanes earn posters only when the maintainer is
        # talking. Silence is where effort goes to die (our own 0/3 record).
        engaged = bool(p.maintainer_responded) and (
            p.maintainer_last_reply_age_days is None
            or p.maintainer_last_reply_age_days <= MAX_RESPONDER_AGE_DAYS)
        if engaged:
            passes.append("negotiated lane, maintainer engaged (D7)")
        else:
            fails.append("negotiated lane with no maintainer engagement (D7)")
    elif p.sats is None:
        fails.append("no sats purse (negotiable/unknown)")
    elif p.sats < MIN_SATS:
        fails.append(f"purse {p.sats} < floor {MIN_SATS}")
    else:
        passes.append(f"purse {p.sats} sats")
        if REQUIRE_ESCROW_OR_SCHEDULE:
            if p.escrow:
                passes.append("purse locked in escrow")
            elif cm.get("paying_schedule"):
                passes.append("documented paying schedule")
            else:
                fails.append("unescrowed purse, no documented paying schedule")
    if MERGED_ATTEMPT_BLOCKS and p.merged_attempts > 0:
        fails.append(f"{p.merged_attempts} merged fix attempt(s) — purse "
                     f"likely already claimed (D7)")
    if p.dead_attempts >= BATTLE_SCARS_BLOCK_AT:
        fails.append(f"{p.dead_attempts} prior attempts died unmerged "
                     f"(battle scars, D7)")
    if REQUIRE_TRAP_CLEAN:
        if p.trap is None:
            fails.append("trap scan missing")
        elif p.trap.verdict != "CLEAN":
            fails.append(f"trap verdict {p.trap.verdict} (wall requires CLEAN)")
        else:
            passes.append("trap scan CLEAN")
    if p.repo_archived:
        fails.append("repo archived (payout was never coming)")
    else:
        if p.repo_last_push:
            import datetime as dt
            age = (dt.date.today() - dt.date.fromisoformat(p.repo_last_push)).days
            if age > MAX_REPO_STALE_DAYS:
                fails.append(f"repo last push {age}d ago (> {MAX_REPO_STALE_DAYS}d)")
            else:
                passes.append(f"repo pushed {age}d ago")
        else:
            fails.append("repo freshness unknown")
    if REQUIRE_RESPONDED:
        if not p.maintainer_responded:
            fails.append("no responder signal on the thread")
        elif p.maintainer_last_reply_age_days is not None \
                and p.maintainer_last_reply_age_days > MAX_RESPONDER_AGE_DAYS:
            fails.append(f"last reply {p.maintainer_last_reply_age_days}d ago (> {MAX_RESPONDER_AGE_DAYS}d)")
        else:
            passes.append("responded recently")
    if p.contested_prs > MAX_CONTESTED_PRS:
        fails.append(f"contested by {p.contested_prs} open PRs (> {MAX_CONTESTED_PRS})")
    elif p.contested_prs == 1:
        age = max((pr.get("age_days") or 0) for pr in p.contest_detail) if p.contest_detail else 0
        if age > MAX_PR_AGE_DAYS:
            fails.append(f"1 open PR but {age}d old (> {MAX_PR_AGE_DAYS}d)")
        else:
            passes.append("lightly contested (1 fresh PR)")
    else:
        passes.append("uncontested")
    if p.rewarder_trust == "low-trust":
        fails.append("low-trust rewarder")
    else:
        passes.append("rewarder ok/unknown")

    if fails:
        return "tracked", passes, fails
    return "honest_work", passes, fails


def opportunity_score(p) -> tuple[float, dict]:
    """Honest Work ranking. Additive, documented, published per poster."""
    parts: dict = {}
    sats = p.sats or 0
    parts["purse"] = min(50.0, sats / 1000.0)                     # 20k sats → 20
    parts["uncontested"] = 30.0 if p.contested_prs == 0 else 15.0
    fresh = 0.0
    if p.repo_last_push:
        import datetime as dt
        age = (dt.date.today() - dt.date.fromisoformat(p.repo_last_push)).days
        fresh = 10.0 if age <= 14 else (5.0 if age <= 30 else 0.0)
    parts["repo_freshness"] = fresh
    parts["responder"] = 10.0 if p.maintainer_responded else 0.0
    parts["escrow"] = 10.0 if p.escrow else (2.0 if p.claim_mechanics.get("negotiated") else 5.0)
    parts["battle_scars"] = -5.0 * min(p.dead_attempts, 4)   # D7: visible, scored
    return sum(parts.values()), parts


def rank_doors(posters):
    """Returns (most_wanted, honest_work, young_gun, tracked).

    most_wanted: TRAP posters, worst score first.
    honest_work: strict-bar survivors, opportunity score desc.
    young_gun:   newest first_seen among bar survivors.
    """
    mw, hw, tracked = [], [], []
    for p in posters:
        door, passes, fails = check(p)
        if door == "most_wanted":
            p.kind = "trap"
            mw.append((p, passes, fails))
        elif door == "honest_work":
            p.kind = "opportunity"
            p.score, p.score_breakdown = opportunity_score(p)
            hw.append((p, passes, fails))
        else:
            tracked.append((p, passes, fails))
    mw.sort(key=lambda t: -(t[0].trap.score if t[0].trap else 0))
    hw.sort(key=lambda t: -(t[0].score or 0))
    young_gun = None
    if hw:
        young_gun = max(hw, key=lambda t: t[0].first_seen)
    return mw, hw, young_gun, tracked
