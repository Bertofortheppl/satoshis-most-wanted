# Decision Log — Satoshi's Most Wanted

> Every product-shape decision: context, options, decision, rationale, and
> the trigger to revisit. Append-only; new entries on top. Owner sign-off
> recorded per entry. Ties to RESEARCH.md evidence by section.

## D5 — Flip "Most Wanted" to the traps; split best/worst — DECIDED (owner 2026-10-24, "the table is our north star")

**Context:** Owner observation (2026-10-24): the old-west theme fits *outlaws*
better than job openings; research (RESEARCH.md "BAD opportunities") shows the
community's deepest unmet need is knowing what to AVOID. Shame and shout-out
are two different psychological products.

**Options:**
- A. One wall of everything (listings + traps mixed) — rejected: mixing
  "work here" and "never work here" in one list dilutes both jobs.
- B. Most Wanted = worst traps (exposure); separate section for best
  opportunities; rewarder report cards as a third section.
- C. Shame-only product (traps site only) — rejected: starves the honest-work
  job that motivated the venture (beacon of wealth-sharing).

**Decision (owner, 2026-10-24):** B. Front page = Top 5 Most Wanted traps +
The Young Gun (freshest clean listing). Sections: Most Wanted (traps), Honest
Work (verified opportunities), The Assay (rewarder report cards / best-to-worst
leaderboard). **Rationale:** WANTED posters are literally for criminals; the
two-sided reputation system (expose worst, celebrate best) matches the
beacon ethos; evidence-first shame keeps it honest, not cruel.

**Ethics guardrails (constitution §2, binding for the trap wall):**
- Evidence-first: every poster shows the scanner verdict, rule IDs, severities,
  quoted findings, reproducible queries, and the tool's stated limits.
  "SUSPICIOUS" is a score, not an accusation — show the breakdown.
- Repos/orgs/behavior only, never persons; no doxxing.
- Posters come DOWN when the repo changes (re-check cadence) — the wall is
  current, not eternal punishment.
- Dispute path: a public issue template for maintainers to contest a listing;
  corrections logged openly.
- Attribution to the tool and its author at every verdict.

**Revisit trigger:** legal/conduct friction, or scanner false-positive rate
materially damages an innocent repo.

## D4 — Trap scanner strategy: adopt + improve, spin out as a tool — DECIDED (owner 2026-10-24)

**Context:** RESEARCH.md (trapcheck find). The scanner is arguably "the real
gem" (owner's words) alongside the outcomes ledger. Options: adapt inside the
venture repo; fork as standalone tool repo; contribute upstream only.

**Decision (owner, 2026-10-24, pending final sign-off):** Vendor the rules into
the engine with attribution now (MIT permits); spin the improved scanner out
as its own public tool repo when Sprint 2 lands (independent name, own README,
CI-action mode — its job: "check a repo before you point an agent at it");
contribute fixes upstream to agentatwork/trapcheck as we learn. **Rationale:**
mirrors the house pattern proven Aug 16 ("three repos, three distinct jobs":
tool vs ops-state vs product); a tool others embed earns independent
credibility the boards can't; upstream contribution is the beacon ethos.

**Revisit trigger:** if tool maintenance distracts from the board for 2+
sprints, freeze the fork and vendor-snapshot instead.

## D3 — Venture architecture: morph, don't split — DECIDED (owner 2026-10-24, "keep with the krillion ethos")

**Context:** Product grew from "bounty board" to three interlocking products
(trap wall, honest-work board, outcomes/report cards) + one engine. Question:
one venture or several? (Krillion study in RESEARCH.md.)

**Options:**
- A. Morph this venture into "the town": one repo, one engine, one outcomes
  DB, one destination site with three branded sections; trap scanner spins
  out later per D4. *(Recommended.)*
- B. Scanner + boards + leaderboard as three separate ventures/repos/sites.
  Maximum brand surface; splits the data asset (the actual moat), triples ops
  for one infrastructure guy + agents, and the outcomes ledger is worthless
  split across repos.
- C. Everything in one repo including the tool. Simplest start; the tool
  loses independent identity/credibility and dies with the board if the board
  fails.

**Decision (owner, 2026-10-24, pending final sign-off):** A. **Rationale:** the
compounding asset is the outcomes database — it must be singular; sections are
cheap, repos are cheap, data silos are fatal; Krillion study shows one engine
wearing many doors wins, and doors can be added later without re-architecture.
**Revisit trigger:** if any single section's traffic/usage dominates >80% for a
month, split it into its own repo with its own door and keep the data link.

## D2 — v1 scope, ranking, tip jar, name — DECIDED (2026-10-22, owner)

Scope: GitHub + SN bounties first (quality-gated growth toward
everything-sats-earning). Ranking: opportunity score; Top 5 Most Wanted front
page + one fresh-clean slot ("The Young Gun", outlaw nicknames, confirmed).
Donations: plain tip jar (no goal bar). Name: Satoshi's Most Wanted.
(See SPEC.md; superseded in part by D5 on ranking placement — score now ranks
Honest Work; traps rank by scanner severity + victim count.)

## D1 — Launch the venture — DECIDED (2026-10-22, owner)

Pivot from the failed PR-workshop/bounty-desk lanes to a free, open-data,
donation-funded public utility. Rationale: owner is an infrastructure builder,
not a dev; aggregator + verification + beacon beats grinding PRs.
Context: 2026-10-22 audit (zero lifetime revenue; negotiated lane dead;
aggregation+verification gap confirmed empty).
