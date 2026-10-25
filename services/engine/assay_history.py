"""The Assay's historical layer — industry track records from source data.

v1: the Lightning Bounties feed carries its own history (85 lifetime
bounties at 2026-10-24: awarded items include winner, claim date, and
total_reward_sats). This module reads ALL feed items (the live adapter
skips closed ones) and builds:

- platform totals (industry snapshot)
- rewarder cards from history: touched / awarded / open / award rate /
  sats awarded / median days-to-award
- hunter cards: who actually wins bounties (wins, sats)

HONEST METHOD (rendered alongside the data):
- "awarded" = the platform records a designated winner + claim; we do NOT
  independently verify payment settlement.
- crowdfunding: items list up to three funders (last/second/third rewarder);
  an item counts toward every listed funder (deduped per item).
"""
from __future__ import annotations

import datetime as dt
import statistics


def _funders(item) -> list[str]:
    names = []
    for key in ("last_rewarder_data", "second_last_rewarder_data",
                "third_last_rewarder_data"):
        u = ((item.get(key) or {}).get("github_username") or "").strip()
        if u and u not in names:
            names.append(u)
    return names or ["unknown"]


def _days_between(a, b):
    try:
        return (dt.date.fromisoformat((b or "")[:10]) -
                dt.date.fromisoformat((a or "")[:10])).days
    except Exception:
        return None


def build_lb_history(items) -> dict:
    platform = {"lifetime": 0, "awarded": 0, "open": 0, "sats_awarded": 0}
    rewarders: dict = {}
    hunters: dict = {}
    for it in items:
        platform["lifetime"] += 1
        awarded = bool(it.get("winner_data"))
        sats = (it.get("total_reward_sats")
                or it.get("unexpired_total_rewards") or 0) or 0
        if awarded:
            platform["awarded"] += 1
            platform["sats_awarded"] += sats
        elif not it.get("is_closed"):
            platform["open"] += 1
        days = None
        if awarded:
            days = _days_between(it.get("created_at"), it.get("claimed_at")
                                 or it.get("modified_at"))
        for name in _funders(it):
            card = rewarders.setdefault(name, {
                "rewarder": name, "touched": 0, "awarded": 0, "open": 0,
                "sats_awarded": 0, "days_to_award": [],
            })
            card["touched"] += 1
            if awarded:
                card["awarded"] += 1
                card["sats_awarded"] += sats
                if days is not None:
                    card["days_to_award"].append(days)
            elif not it.get("is_closed"):
                card["open"] += 1
        if awarded:
            winner = ((it.get("winner_data") or {}).get("github_username")
                      or "unknown")
            h = hunters.setdefault(winner, {"hunter": winner, "wins": 0,
                                            "sats": 0})
            h["wins"] += 1
            h["sats"] += sats
    cards = []
    for c in rewarders.values():
        days = c.pop("days_to_award")
        c["award_rate"] = round(c["awarded"] / c["touched"], 2) if c["touched"] else 0
        c["median_days_to_award"] = int(statistics.median(days)) if days else None
        cards.append(c)
    cards.sort(key=lambda c: (-c["sats_awarded"], -c["awarded"]))
    hunters = sorted(hunters.values(), key=lambda h: (-h["sats"], -h["wins"]))
    return {"platform": platform, "rewarders": cards, "hunters": hunters}
