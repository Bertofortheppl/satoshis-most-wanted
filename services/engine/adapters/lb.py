"""Lightning Bounties feed adapter.

Feed field mapping lifted from MejorQueNada/bounty-agent scout.py (MIT, our
lineage) — two months of unattended live runs validated the field names.
"""
from __future__ import annotations

import datetime as dt

from ..schema import Poster, derive_id


def fetch(fetch_fn, config, today=None) -> list[Poster]:
    """fetch_fn: paginating feed getter (url, skip, limit) -> list[dict].

    Ingests ALL items with honest statuses (D10): winner_data -> 'awarded'
    (designated winner + claim recorded; settlement unverified), is_closed
    without winner -> 'expired' (purse withdrawn/reclaimed), else 'open'.
    Previously awarded items were skipped at ingest — they VANISHED, which
    could emit false 'expired' outcome events and starved The Assay's live
    tracking of awarded transitions.
    """
    today = today or dt.date.today().isoformat()
    min_reward = config.get("min_reward", 2000)
    feed = fetch_fn(config["query"])
    posters = []
    for it in feed:
        repo = (it.get("repository_data") or {}).get("full_name") or ""
        if not repo:
            continue
        issue_number = it.get("issue_number")
        if issue_number is None:
            continue
        if it.get("winner_data"):
            status = "awarded"
            reward = it.get("total_reward_sats") or it.get("unexpired_total_rewards") or 0
        elif it.get("is_closed"):
            status = "expired"
            reward = it.get("unexpired_total_rewards") or 0
        else:
            status = "open"
            reward = it.get("unexpired_total_rewards") or 0
        if reward < min_reward:
            continue
        rewarder = ((it.get("last_rewarder_data") or {}).get("github_username")) or ""
        posters.append(Poster(
            id=derive_id(config["source"], f"lb-{issue_number}-{repo}"),
            source=config["source"],
            source_label=config["source_label"],
            external_id=f"lb-{issue_number}-{repo}",
            title=(it.get("title") or "").strip(),
            url=it.get("html_url") or "",
            sats=reward,
            escrow=config["escrow"],
            rewarder=rewarder or None,
            claim_mechanics={
                **config.get("claim_mechanics", {}),
                "negotiated": bool(config.get("negotiated")),
                "paying_schedule": bool(config.get("paying_schedule")),
            },
            repo=repo,
            first_seen=today,
            last_checked=today,
            status=status,
        ))
    return posters
