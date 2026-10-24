"""GitHub issue-board adapter (org boards + labeled repo bounties).

Generic by configuration: the query and optional sats-award tables live in
sources_config.py. Emits Posters with paying-schedule sats (sn_repo) or
negotiated markers (getalby). Enrichment is NOT done here.
"""
from __future__ import annotations

import datetime as dt
import urllib.parse

from ..schema import Poster, derive_id
from .. import github as ghmod


def _search_url(query: str) -> str:
    return ("https://api.github.com/search/issues?q="
            + urllib.parse.quote(query) + "&per_page=100&sort=updated&order=desc")


def _award(labels: list[str], config) -> tuple[int | None, bool]:
    """sats from label tables; None when the source is negotiated."""
    if config.get("negotiated"):
        return None, False
    tables = config.get("labels") or {}
    prios = config.get("priority") or {}
    sats = None
    prio = 1.0
    for lb in labels:
        name = lb.get("name", "")
        if name in tables:
            sats = tables[name]
        if name in prios:
            prio = prios[name]
    if sats is not None:
        sats = int(sats * prio)
    return sats, True


def fetch(gh, config, today=None) -> list[Poster]:
    today = today or dt.date.today().isoformat()
    # a label-template query fans out to one search per label (proven scout
    # pattern — GitHub search takes one label per query); items dedupe by id.
    if "{label}" in config["query"] and config.get("labels"):
        queries = [config["query"].replace("{label}", lb) for lb in config["labels"]]
    else:
        queries = [config["query"]]
    items, seen = [], set()
    for q in queries:
        try:
            data = gh.gh(_search_url(q))
        except Exception:
            continue
        for it in data.get("items") or []:
            if it.get("html_url") and it["html_url"] not in seen:
                seen.add(it["html_url"])
                items.append(it)
    posters = []
    for it in items:
        number = it.get("number")
        repo_url = (it.get("repository_url") or "")
        repo = repo_url.rsplit("repos/", 1)[-1] if "repos/" in repo_url else ""
        if not repo or number is None:
            continue
        labels = it.get("labels") or []
        sats, _ = _award(labels, config)
        posters.append(Poster(
            id=derive_id(config["source"], f"{repo}#{number}"),
            source=config["source"],
            source_label=config["source_label"],
            external_id=f"{repo}#{number}",
            title=(it.get("title") or "").strip(),
            url=it.get("html_url") or "",
            sats=sats,
            escrow=config["escrow"],
            rewarder=repo.split("/")[0],
            claim_mechanics={
                **config.get("claim_mechanics", {}),
                "negotiated": bool(config.get("negotiated")),
                "paying_schedule": bool(config.get("paying_schedule")),
            },
            repo=repo,
            status="open" if it.get("state") == "open" else "closed",
            first_seen=today,
            last_checked=today,
        ))
    return posters
