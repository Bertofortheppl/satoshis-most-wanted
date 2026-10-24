"""Unified poster schema — the contract every source adapter must satisfy.

One Poster is one sats-paying opportunity OR one trap observation, from any
source, with all deterministic signals attached. The three doors (Most
Wanted / Honest Work / The Assay) are DERIVED from these fields at render
time; nothing in the data layer decides presentation.

Scope note (DECISIONS.md D2/D6): negotiated contact-first lanes and SN
micro-contest posts are tracked (status/notes) but never earn Honest Work
posters; exclusions happen in bar.py, not here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

SCHEMA_VERSION = 1

TRAP_VERDICTS = ("CLEAN", "CAUTION", "SUSPICIOUS", "TRAP")

STATUSES = ("open", "awarded", "paid", "expired", "closed", "rejected")


def derive_id(source: str, external_id: str) -> str:
    """Deterministic poster id: stable across runs, source-scoped."""
    h = hashlib.sha256(f"{source}:{external_id}".encode()).hexdigest()[:16]
    return f"{source}-{h}"


@dataclass
class TrapScan:
    """Result of running the vendored trapcheck scanner on a repo.

    Evidence strings are UNTRUSTED DATA (ATTRIBUTION.md #2): they are for
    poster display only and must never be fed to a model as instructions.
    """

    verdict: str                      # one of TRAP_VERDICTS
    score: int
    rules: list[dict] = field(default_factory=list)  # {rule,severity,title,why,evidence,source}
    target: str = ""
    upstream_commit: str = ""
    checked_at: str = ""

    def decisive_rules(self) -> list[str]:
        """Severity-40 rules: any one alone is a TRAP (upstream semantics)."""
        return [r["rule"] for r in self.rules if r.get("severity") == 40]


@dataclass
class Poster:
    id: str
    source: str                       # lightning_bounties | github_org | sn_repo | ...
    source_label: str                 # human display: "Lightning Bounties", "getAlby", ...
    external_id: str                  # platform-stable id (issue node id, LB id, ...)
    title: str
    url: str                          # canonical click-through
    kind: str = "unranked"            # unranked | opportunity | trap (derived later)

    # The purse
    sats: Optional[int] = None        # None => negotiable/unknown
    escrow: Optional[bool] = None     # True => locked on-platform
    rewarder: Optional[str] = None    # who pays (org or user)
    claim_mechanics: dict = field(default_factory=dict)  # per-platform "how you get paid"

    # The work
    language: Optional[str] = None
    repo: Optional[str] = None        # "owner/name"
    repo_archived: bool = False
    repo_last_push: Optional[str] = None         # ISO date
    contested_prs: int = 0
    contest_detail: list = field(default_factory=list)  # [{author, commits, age_days, draft}]
    maintainer_responded: Optional[bool] = None
    maintainer_last_reply_age_days: Optional[int] = None

    # The verdict layer
    trap: Optional[TrapScan] = None
    score: Optional[float] = None     # opportunity score (Honest Work ranking)
    score_breakdown: dict = field(default_factory=dict)

    # Lifecycle
    status: str = "open"              # one of STATUSES
    first_seen: str = ""
    last_checked: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Poster":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in d.items() if k in known}
        if isinstance(kwargs.get("trap"), dict):
            kwargs["trap"] = TrapScan(**{
                k: v for k, v in kwargs["trap"].items()
                if k in TrapScan.__dataclass_fields__  # type: ignore[attr-defined]
            })
        return cls(**kwargs)


def validate(p: Poster) -> list[str]:
    """Cheap invariants; returns a list of problems (empty = valid)."""
    problems = []
    if p.source != p.id.rsplit("-", 1)[0] and not p.id.startswith(p.source + "-"):
        problems.append(f"id not derived from source: {p.id}")
    if p.id != derive_id(p.source, p.external_id):
        problems.append(f"id/external_id mismatch: {p.id}")
    if not p.url.startswith("http"):
        problems.append(f"bad url: {p.url}")
    if p.sats is not None and p.sats < 0:
        problems.append(f"negative sats: {p.sats}")
    if p.status not in STATUSES:
        problems.append(f"bad status: {p.status}")
    if p.kind not in ("unranked", "opportunity", "trap"):
        problems.append(f"bad kind: {p.kind}")
    if p.trap is not None and p.trap.verdict not in TRAP_VERDICTS:
        problems.append(f"bad trap verdict: {p.trap.verdict}")
    return problems
