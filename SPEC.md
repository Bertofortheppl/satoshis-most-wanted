# Satoshi's Most Wanted — Product Spec (v2)

> Status: v2 — north star (three doors) owner-confirmed 2026-10-24.
> Evidence base: RESEARCH.md. Shape decisions: DECISIONS.md.
> Open items marked OPEN (D6) — resolved before sprint gates.

## Identity

We protect a niche market: people (and the agents they fire at GitHub) who
want to *really contribute or learn* — by highlighting projects that pay
real sats, and exposing the traps set for them. Free, open data from day
one (D6), donation-funded. Neutral institutional voice; automation disclosed
in the footer (D6).

**Ethos (Krillion study, RESEARCH.md):** one engine, many doors — each door
owns exactly one job and states honestly what it is. The engine and the
outcomes database are the assets; doors are acquisition surfaces we can add
or retire without re-architecting.

## North star — the three doors

| Door | Job | Ranks by |
|---|---|---|
| **Most Wanted** | the worst traps — exposure | scanner severity + victim count |
| **Honest Work** | verified clean opportunities | opportunity score (+ The Young Gun) |
| **The Assay** | rewarder report cards, best→worst leaderboard | paid ratio, time-to-award, totals |

Front page: Top 5 Most Wanted + The Young Gun (freshest clean listing, outlaw
nickname). Filters + keyword search per door. Click-through to the source.

## Engine (Sprint 1 — the product IS the data)

- **Unified poster schema** (open JSON, committed in-repo): id, source, title,
  url, sats (or `negotiable`), escrow, contested_prs (+ contest quality),
  repo_last_push, maintainer_response (last maintainer reply age),
  rewarder, rewarder_trust, language, first_seen, last_checked, score,
  score_breakdown, trap_verdict, trap_findings (rule IDs + severities,
  evidence kept separate), claim_mechanics (per-platform "how you actually
  get paid").
- **Trap rules vendored with attribution** (from agentatwork/trapcheck, MIT;
  rule IDs preserved — provenance honesty). Verdicts published WITH evidence
  and the tool's stated limits. Severity-40 rule = never listed on Honest
  Work; traps feed Most Wanted.
- **Outcomes ledger from day one:** every ingested listing tracked to its
  end — awarded? paid? time-to-award? rewarder? Compounds into The Assay's
  report cards (nobody else has this data).
- **Signals (deterministic only):** escrow status, open-PR contest count +
  junk-PR quality, repo freshness, maintainer responsiveness, rewarder
  history. No agent improvisation in the data path.
- **Exclusions (never listed):** HUMAN_ONLY / bank-card "agent" lanes; SN
  micro-contest bounties (2–5k content/gaming — not dev work); archived or
  stale repos; TRAP-verdict repos; negotiated contact-first lanes (D6).

## Ethics guardrails (binding, constitution §2)

Evidence-first posters (verdict + rules + quoted findings + limits);
repos/orgs/behavior, never persons; posters come DOWN when the repo changes
(re-check cadence); public dispute path for maintainers; attribution on
every verdict. "SUSPICIOUS" is a score, not an accusation.

## Sources — v1 (D2)

Lightning Bounties feed, Stacker News repo bounty issues (episodic — lane
verified empty 2026-10-23), SN community bounty posts (SN GraphQL), org
bounty boards (getAlby `good first issue` + Flash-style labeled issues —
pattern generalizes). Growth toward everything-sats only while quality
holds.

## Donations (D2)

Plain tip jar: `littlecamel691929@getalby.com` (verified E2E 2026-10-23,
ledger txn 53) + nostr zaps when the bot exists. Upgrade path: branded
handle on the `satsmostwanted` sub-wallet (Alby Pro, parked).

## Infrastructure

Deterministic scripts; GitHub Actions cron (3h) — never the owner's laptop;
fly.io static site (bertoforthepeople account); `health.py` monitoring →
Telegram from day one; self-hosted stats only.

## Sprints (owner gate at every end)

- **S1 — Engine + reviewable data artifacts:** schema, vendored trap rules,
  source adapters, outcomes ledger, tests. Deliverable for review: JSON +
  rendered markdown reports of all three doors (review the DATA before any
  chrome). Honest Work bar STRICT per D6 (escrow/paying schedule, trap-clean,
  repo active, maintainer responsive, contest low); negotiated lanes excluded
  from the wall (tracked in open data only).
- **S2 — Site:** Astro static board on fly, the three doors, search/filters,
  evidence popouts. Trap scanner spin-out decision (D4) lands here.
- **S3 — Distribution (each action owner-gated):** nostr bot, public TG
  channel, RSS, listings, SN launch post.
- **S4 — Monitoring + public stats:** health.py, outcomes dashboard,
  "what we track / how many paid" transparency page.

## NOT building in v1

Accounts, escrow, claims, comments, auto-submission. Pure signal, zero
liability.

## Dependencies

GitHub PAT rotation (pipeline secret), public repo creation (owner gate,
OPEN D6), fly deploy at S2, hub uptime for tip-jar liveness.
