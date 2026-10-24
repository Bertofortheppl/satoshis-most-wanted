"""Outcomes ledger — the compounding asset (SPEC v2, D6).

Append-only JSONL in-repo (data/outcomes.jsonl). Every poster's life gets
recorded: first_seen, status transitions, disappearance. The Assay's
rewarder report cards are pure aggregation over this file — nobody else
tracks whether rewarders actually pay.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def append(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(event) + "\n")


def diff(prev: list, curr: list) -> list[dict]:
    """prev/curr: lists of Poster.to_dict(). Emits transition events."""
    prev_by_id = {p["id"]: p for p in prev}
    curr_by_id = {p["id"]: p for p in curr}
    events = []
    for pid, p in curr_by_id.items():
        old = prev_by_id.get(pid)
        if old is None:
            events.append({"ts": _now(), "id": pid, "event": "first_seen",
                           "to": p["status"], "source": p["source"]})
        elif old.get("status") != p.get("status"):
            events.append({"ts": _now(), "id": pid, "event": "status",
                           "from": old.get("status"), "to": p.get("status"),
                           "source": p["source"]})
    for pid, old in prev_by_id.items():
        if pid not in curr_by_id and old.get("status") == "open":
            events.append({"ts": _now(), "id": pid, "event": "status",
                           "from": "open", "to": "expired",
                           "source": old.get("source")})
    return events


def report_cards(posters: list, events: list) -> list[dict]:
    """Aggregate per rewarder: listed / awarded / paid / time-to-award.

    HONEST LIMITATION (v1): 'awarded'/'paid' transitions are only observable
    for sources whose feeds expose them (LB winner_data). Until outcome
    detection deepens (later sprint), cards honestly show tracked counts and
    observed transitions only — no invented payout numbers, ever.
    """
    by_rewarder: dict = {}
    for p in posters:
        r = p.get("rewarder") or "unknown"
        card = by_rewarder.setdefault(r, {
            "rewarder": r, "listed": 0, "awarded": 0, "paid": 0,
            "expired": 0, "seen_transitions": 0,
        })
        card["listed"] += 1
    id_to_rewarder = {p["id"]: (p.get("rewarder") or "unknown") for p in posters}
    for e in events:
        r = id_to_rewarder.get(e.get("id")) or "unknown"
        card = by_rewarder.setdefault(r, {
            "rewarder": r, "listed": 0, "awarded": 0, "paid": 0,
            "expired": 0, "seen_transitions": 0,
        })
        if e["event"] == "status":
            card["seen_transitions"] += 1
            if e.get("to") == "awarded":
                card["awarded"] += 1
            elif e.get("to") == "paid":
                card["paid"] += 1
            elif e.get("to") == "expired":
                card["expired"] += 1
    return sorted(by_rewarder.values(), key=lambda c: (-c["paid"], -c["awarded"]))
