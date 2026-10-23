# Satoshi's Most Wanted — Sprint 0 Product Spec

> Status: APPROVED 2026-10-22 (owner; The Young Gun confirmed). Nothing ships, deploys, or posts
> without the owner's gate (constitution §4).

## One-liner

The sheriff's office wall for every sats-paying dev opportunity — verified,
badged with honest signal, free for the whole town. The gap we fill: nobody
aggregates across platforms AND tells you if a bounty is worth your time.
The platforms are silos; we're the wall they all get pinned to.

## Front page (first thing you see)

- **TOP 5 MOST WANTED** — big type, poster-style, straight to the point.
  Ranked by opportunity score (below). Each poster: title, sats purse, source,
  badges, and a one-line "why it's on the wall."
- **The Young Gun** — one slot for the freshest clean listing (new,
  uncontested, alive repo). Each pick gets a rotating outlaw nickname
  ("Babyface Jack just rode in — 20k sats, nobody's on it").
  (Owner-confirmed 2026-10-22.)

## The wall (scroll content)

- Full listing, newest-check first, poster cards with sats, source, badges,
  age, language.
- Filters: source, badge, language, sats range, escrow status.
- Keyword search (client-side, no search infra).
- Click-through goes straight to the GitHub issue / SN post / platform page.

## Badges (the honest-signal layer — the moat)

| Badge | Meaning |
|---|---|
| 🔒 Purse Locked | reward escrowed on-platform (Lightning Bounties) |
| ⚠ Contested | N open PRs already chasing it |
| 💀 Ghost Town | repo archived or stale — payout unlikely |
| 🚩 Short Trail | rewarder with thin/no payout history (low trust) |
| 🤝 Negotiable | contact-first, terms TBD (Alby-style programs) |
| ✅ Pays Out | rewarder has verified paid history (stretch goal) |

## Poster data schema (open JSON, committed in-repo)

`id, source, title, url, sats (or "negotiable"), escrow, contested_prs,
repo_last_push, rewarder, rewarder_trust, language, first_seen, last_checked,
score, score_breakdown`

## Sources — v1 (owner decision 2026-10-22)

GitHub + Stacker News lane, chosen for verified-pay density over breadth:

1. Lightning Bounties feed (existing scout source)
2. Stacker News repo bounty issues — difficulty/priority labels (existing)
3. Stacker News community bounty posts — via SN public GraphQL API (new)
4. Org bounty boards — getAlby `good first issue` (existing) + Flash-style
   GitHub-labeled bounty issues (new, pattern generalizes to any org)

Growth path (owner-approved direction, quality-gated): nostr-native bounties
(Catalax etc.) → eventually everything sats-earning. Add sources only while
v1 quality stays high — no rush.

## Ranking — opportunity score

`score = f(sats, uncontested, repo_activity, escrow)` — weights documented in
the repo, breakdown shown per poster (no black box). A big contested
ghost-town purse loses to a smaller clean one. That judgment IS the product.

## Donations (owner decision: plain tip jar)

Zap QR + lightning address on the site; nostr zaps on auto-posted notes.
No goal bar, no tiers. Rails blocked until Alby Hub is back (dedicated
sub-wallet, Phase 2). Zero take-rate, forever.

## Infrastructure & scheduling (lesson-driven design)

- Pipeline: deterministic scripts (scout.py extended to unified schema),
  no agent improvisation in the data path
- Scheduler: **GitHub Actions cron (every 3h)** — NOT the owner's laptop;
  commits updated JSON + triggers rebuild
- Site: **Astro** static build on **fly.io** (proven deploy pattern)
- Data: listings JSON committed in-repo = open data, beacon ethos
- Monitoring from day one: `health.py` — pipeline freshness, site up,
  hub node status (when back) → Telegram alert. The 7-weeks-dark failure
  mode must be structurally impossible.

## Distribution (later sprint, each external action owner-gated)

Nostr bot (every fresh clean bounty → zappable note), public Telegram
channel (existing bot goes public), RSS, listings on nostr.net / BOLT.fun /
gigs.sh, SN launch post.

## Metrics

Listings/day by source, % with clean badges, alert latency (found→posted),
tip jar sats (when live), self-hosted traffic stats only (no trackers).

## NOT building in v1 (prudence)

No accounts, no escrow, no claims, no comments, no auto-submission.
Pure signal, zero liability. Those are where competitors die.

## Owner gates

Spec approval (now) → each sprint review → anything external (deploys,
posts, listings). Pending dependencies: Alby Hub re-auth (donation rail +
balance verify), fly SSO (board deploy; also ReviewDesk teardown decision),
GitHub PAT rotation (pipeline secret for Actions).
