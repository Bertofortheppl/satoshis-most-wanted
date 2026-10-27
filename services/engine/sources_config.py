"""Verified sources (v1, D2/D6). Data-driven: a new org board is a config
entry, not new code. Only sources whose queries we have verified live are
enabled; disabled entries are kept with notes for tuning.

Fields per source:
  kind            adapter to use
  source          stable Poster.source prefix
  source_label     display name
  escrow          purse locked on-platform? (True/None)
  paying_schedule documented paying program without escrow? (bool)
  negotiated      contact-first, terms TBD (D6: never earns a wall poster)
  claim_mechanics per-platform "how you actually get paid" (RESEARCH.md)
  query           adapter-specific (GitHub search query / feed URL)
  enabled         verified live?
"""

LB_CLAIM_MECHANICS = {
    "steps": [
        "Log in to app.lightningbounties.com with GitHub BEFORE submitting your PR",
        "PR body must include `close #<issue>` and the Lightning Bounties issue URL",
        "PR must pass the repo's checks and be merged (not draft)",
        "Click 'Claim Reward' on your dashboard after merge",
    ],
    "payment": "automatic on verified merge",
    "gotchas": "missing login-first or wrong close syntax = no payout; bounty lock-time can expire",
}

SN_CLAIM_MECHANICS = {
    "steps": [
        "Pick an open issue labeled difficulty:* (schedule: 20k good-first → 1M hard sats, x priority 0.5-3)",
        "Comment your intent, get maintainer engagement before building",
        "PR merged to stackernews/stacker.news pays per the published schedule",
    ],
    "payment": "manual by maintainers after merge, per published schedule",
    "gotchas": "lane is episodic — often zero open bounty issues; watch, don't camp",
}

ALBY_CLAIM_MECHANICS = {
    "steps": [
        "Contact-first: comment on the issue offering to take it under the bounty program",
        "Maintainer confirms scope and terms BEFORE any code",
        "Deliver PR; payout negotiated on completion",
    ],
    "payment": "negotiated, no escrow",
    "gotchas": "cold-contact lane: our own record is 0/3 maintainer replies in 2+ months",
}

FLASH_CLAIM_MECHANICS = {
    "steps": [
        "Comment on the issue to claim and share your Lightning address (required before it can be marked In Progress)",
        "Maintainer labels it In Progress (multiple hunters may hold it until a winner is chosen)",
        "Join their public Discord #public-development and get maintainer approval BEFORE opening the PR",
        "PR passes three review rounds; payment goes to your lightning address on merge",
    ],
    "payment": "maintainer-approved, direct to your lightning address on merge",
    "gotchas": "Discord approval gate; 'claimed' can still mean contested until a winner is chosen",
}

SOURCES = [
    {
        "kind": "lb",
        "source": "lightning_bounties",
        "source_label": "Lightning Bounties",
        "escrow": True,
        "paying_schedule": False,
        "negotiated": False,
        "query": "https://app.lightningbounties.com/api/issues/",
        "min_reward": 2000,
        "claim_mechanics": LB_CLAIM_MECHANICS,
        "enabled": True,
    },
    {
        "kind": "github",
        "source": "sn_repo",
        "source_label": "Stacker News repo bounties",
        "escrow": None,
        "paying_schedule": True,   # documented 20k-1M sats-by-difficulty schedule
        "negotiated": False,
        "query": 'repo:stackernews/stacker.news is:issue is:open label:"{label}"',
        "labels": {
            "difficulty:good-first-issue": 20_000,
            "difficulty:easy": 100_000,
            "difficulty:medium": 250_000,
            "difficulty:medium-hard": 500_000,
            "difficulty:hard": 1_000_000,
        },
        "priority": {
            "priority:low": 0.5, "priority:medium": 1.5,
            "priority:high": 2.0, "priority:urgent": 3.0,
        },
        "claim_mechanics": SN_CLAIM_MECHANICS,
        "enabled": True,
    },
    {
        "kind": "github",
        "source": "getalby",
        "source_label": "getAlby bounty program",
        "escrow": None,
        "paying_schedule": False,
        "negotiated": True,          # D6: tracked, never on the wall
        "query": 'org:getAlby is:issue is:open label:"good first issue"',
        "claim_mechanics": ALBY_CLAIM_MECHANICS,
        "enabled": True,
    },
    {
        "kind": "github",
        "source": "flash",
        "source_label": "Flash bounty board",
        "escrow": None,
        "paying_schedule": True,   # documented on-merge direct payment (board + CONTRIBUTING)
        "negotiated": False,
        "query": 'org:lnflash is:issue is:open label:"💰 bounty"',
        # VERIFIED 2026-10-24 from the board's own script.js: org lnflash,
        # label "💰 bounty"; board currently EMPTY (0 open, 0 paid) — enabled
        # and dormant. sats amounts live in issue bodies; body extraction
        # lands with the bounty-label sweep (Sprint 2) — until then items
        # track with "no sats purse".
        # OUTCOME HOOK: Flash maintains a `paid` label on completed bounties
        # (label:"paid" label:"💰 bounty" state:closed) — observable
        # awarded/paid transitions for The Assay once outcome detection is
        # wired (PLANNING.md not-yet list).
        "claim_mechanics": FLASH_CLAIM_MECHANICS,
        "enabled": True,
    },
    {
        # D10 queue #2 — THE BOUNTY-LABEL SWEEP: the wild `💎 Bounty` corpus
        # where the prompt-harvest trap population lives (RESEARCH.md: 16%
        # of 563 bounty-labeled issues ask agents to disclose their own
        # instructions). Primary purpose: feed Most Wanted. Secondary:
        # honest listings land in open data (most carry no verifiable sats
        # field, so they track rather than post — extraction comes later).
        # Bounded to the 100 most-recently-updated open issues per run;
        # enrichment + trap scans hit only NEW repos (verdict ledger D8 +
        # cached reads keep the 3h cadence inside rate limits).
        "kind": "github",
        "source": "bounty_sweep",
        "source_label": "Bounty-label sweep (GitHub-wide)",
        "escrow": None,
        "paying_schedule": False,
        "negotiated": False,
        "query": 'is:issue is:open label:"💎 Bounty"',
        "claim_mechanics": {
            "steps": ["Wild listings: terms are whatever the issue says — read every",
                      "requirement carefully; run the repo through a trap scan",
                      "(that is what this board is for) before committing anything."],
            "payment": "varies by issuer; unverified",
            "gotchas": "this corpus is where the prompt-harvest traps live; never paste "
                       "your agent configuration into a PR",
        },
        "enabled": True,
    },
]
