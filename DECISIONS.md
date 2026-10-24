# Decision Log — Satoshi's Most Wanted

> Every product-shape decision: context, options, decision, rationale, and
> the trigger to revisit. Append-only; new entries on top. Owner sign-off
> recorded per entry. Ties to RESEARCH.md evidence by section.

## D8 — Scan caching: the verdict ledger is committed data — DECIDED (owner 2026-10-24, "best practices in mind")

**Context:** Actions runners are ephemeral; the gitignored state/ scan cache
meant every 3-hour run re-scanned every repo — API-heavy and blind to the
weekly rescan policy.

**Decision:** two-layer, by data class:
1. **Trap verdicts → `data/trap_scans.json`, committed public data** ("the
   verdict ledger"). CI inherits it via git checkout — no cache service, no
   cold starts, the weekly rescan policy finally works everywhere, and
   verdict history becomes an auditable git trail (a repo scanned clean in
   October and dirty in December shows exactly when, by whom — evidence
   ethos). One-time migration from the old state/ location; grows
   monotonically (accepted: entries are small and stale verdicts are
   context, not clutter).
2. **Raw GitHub API responses → ephemeral** (`state/gh_cache.json`, kept out
   of the public repo; warmed across runs via `actions/cache` with a unique
   save-key per run + prefix restore). Publishing third-party API blobs was
   never reviewed for release; TTLs inside the file gracefully expire
   anything stale, so a restored old cache can only help, never mislead.

**Pinned by tests:** second run with the same corpus performs ZERO scans
(`test_second_run_emits_no_first_seen`); ledger presence in data/ asserted.
**Revisit trigger:** if the verdict ledger ever exceeds ~1MB or a verdict
format change is needed, split by month instead of pruning history.

## D7 — Battle scars + conditional negotiated lanes — DECIDED (owner 2026-10-24)

**Context:** First live run review. The strict wall held 2 posters of 43;
the lnbits#2581 flag exposed contest-blindness to attempt history. D6's
negotiated-lane revisit-trigger fired with live data in hand (30 getAlby
candidates excluded by category; ~a third show maintainer engagement).

**Decisions (owner 2026-10-24):**
1. **Battle scars are blocking.** Dead-attempt history (closed-unmerged
   PRs referencing the issue) is fetched per listing, shown on posters,
   penalized in the score. Owner wording: "block them with more than 2
   dead attempts" → **3+ dead attempts = no poster.** 1–2 scars display
   and ding the score.
2. **Negotiated lanes included CONDITIONALLY.** A negotiated (🤝, no
   escrow) listing earns a poster ONLY when the maintainer has recently
   engaged on the thread — the same responsiveness bar as everything
   else. Silent negotiated threads (our own 0/3 graveyard) never post.
3. **Merged attempts block too** (added during implementation when live
   verification showed lnbits#2581 with a MERGED fix from Sep 2026 while
   the platform listing still shows open): a merged fix attempt means the
   purse is likely already claimed — the listing is tracked as a probable
   zombie, never posted. Verifies via PR search `merged_at` (one cached
   call per issue).

**Rationale:** the wall's promise is "every poster is real"; spent purses
and rejection graveyards break that promise as surely as traps do.

**Revisit trigger:** if the wall drops below 5 posters for two consecutive
runs despite negotiated inclusion, revisit source breadth before
loosening gates.

## D6 — Sprint 1 intent: data public, strict bar, negotiated excluded, neutral voice — DECIDED (owner 2026-10-24)

**Context:** pre-Sprint-1 check-in (owner: "quality over speed and checking
in with thoughtful questions to nail my intent"). Four forks resolved:

1. **Data publicity: PUBLIC from day one.** The repo IS the open data —
   listings, outcomes ledger, trap verdicts, all public from first commit.
   No secrets ever land in it (enforced by design: secrets only in
   ops/.env / secrets.json, both gitignored).
2. **Honest Work bar: STRICT.** A poster requires ALL of: sats-paying dev
   work with escrow or a documented paying schedule, trap-scan clean, repo
   active, maintainer responsive, contest low. Expected wall size 5–15.
   Grey area lives in open data + The Assay — not on the wall.
3. **Negotiated/contact-first lanes: EXCLUDED from the wall (v1).** Owner:
   "highest signal and value for now, even if it's a smaller pool." They
   remain tracked in open data and feed The Assay; revisit when evidence
   shows maintainers engaging with cold contacts.
4. **Voice: NEUTRAL institutional, automation disclosure in the footer.**
   No persona fatigue; constitution §2.5 satisfied.

**Revisit triggers:** wall starves (<5 posters for 2 weeks) → consider
relaxing contest/maintainer gates one at a time; negotiated lane shows
maintainer engagement signal → reconsider inclusion.

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
