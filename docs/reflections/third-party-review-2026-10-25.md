# Third-Party Review — Satoshi's Most Wanted (2026-10-25)

> Source: a free opencode review session on `casa` (fresh third-party eyes,
> crawled the public repo). Transcript pulled via Tailscale SSH from casa's
> opencode session database — no copy-paste. Preserved verbatim in
> structure; this is now a first-class artifact any session can read.

## Positioning (the reviewer's one-liner)

> "The value isn't 'another board', it's a **consumer protection layer for
> Bitcoin dev bounties**. The trap detection + outcomes ledger are the
> signal. Everything else is noise until those two are actually live and
> compounding."

## What's actually good (the signal)

- **The verification layer is the moat** — zombie-purse detection
  (merged/dead attempts), timeline-authoritative signals, battle scars.
  "This issue was already fixed 2 months ago but still listed as open" is
  immediately useful and novel.
- **Trap detection is the wedge** — the 16% prompt-harvest research;
  vendored trapcheck with attribution + evidence + limits; "Most Wanted"
  (avoid-first) framing beats "here's more work" in a space full of grifters.
- **Disciplined engineering** — DECISIONS/RESEARCH/PLANNING maturity,
  deterministic data path (no LLM), committed verdict ledger, hermetic
  tests, cron not dependent on the laptop, explicit bar fail reasons.
- **Three-door model** — avoid (Most Wanted) + find (Honest Work) +
  reputation (The Assay) from one dataset.
- **Claim mechanics matter** — documenting "login to LB before your PR" is
  more valuable than the sats amount; builds trust instantly.

## What's weak or missing (the noise)

- **Inventory is thin** (4 posters) — prioritize the bounty-label sweep and
  sources before any gate loosening or UI polish.
- **The Assay is unproven** — the live-tracking side needs awarded/paid
  wiring (LB winner_data → events). With receipts it becomes citable.
- **Frontend doesn't exist** — fine for data verification; discoverability
  needs S2 eventually.
- **Negotiated lanes hard to verify** — conditional inclusion is the
  correct conservative choice; don't loosen it.
- **Shame wall carries legal/reputational risk** — keep reproducible
  queries + tool limits prominent in any UI; guardrails must be visible,
  not just documented.

## Comparable projects (reviewer's map)

| Project | Overlap | Difference |
|---|---|---|
| Lightning Bounties | source | platform, no cross-platform verification or trap detection |
| Stacker News bounties | source | community posts/micro-contests, no verification/outcomes |
| OnlyDust | OSS bounties | web3, account-based, no adversarial verification |
| Superteam Earn | opportunities | curated/KYC-ish, not Lightning-first, no trap/zombie tracking |
| Algora | bounties | hiring board now, not an open-data aggregator with outcomes |

Nothing does cross-platform aggregation + trap scanning + zombie-purse
detection + outcomes ledger at once. Scattered nostr/Twitter scam warnings
are the closest thing to Most Wanted; nobody systematized it.

## Recommendations (reviewer's order)

1. **Wire outcomes before UI** — LB `winner_data` → awarded/paid events.
2. **Bounty-label sweep next** — feeds both doors without lowering the bar.
3. **Market the "avoid" angle first** — "don't get scammed by bounty traps"
   spreads faster than "find bounties"; Most Wanted examples to nostr/TG
   with evidence attached; the education angle is free marketing.
4. **Keep reports as the source of truth** — review data before chrome.
5. **Spin the scanner earlier if it picks up traction** (D4) — standalone
   trapcheck-style CLI has its own audience beyond bounty hunters.

## Session-workflow design (from the same review session)

Review/planning sessions (free): read repo state; output ARTIFACTS ONLY
(reflections, PLANNING updates, SPEC changes, research); never chat-only
feedback. Dev sessions (paid): read handoff artifacts first → todos →
implement; end by writing a handoff file. The task queue (PLANNING decision
queue + docs/handoffs/) is the contract between sessions. Implemented in
`docs/handoffs/README.md`.
