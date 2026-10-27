# Research Log — Satoshi's Most Wanted

> Evidence base for every design decision. Each entry: what we found, where,
> and what it implies. Decisions that consume this research live in
> DECISIONS.md. Append-only; new entries on top.

## 2026-10-25 — Competitive map (from the third-party review)

| Project | Overlap | Difference |
|---|---|---|
| Lightning Bounties | source | platform, no cross-platform verification or trap detection |
| Stacker News bounties | source | community posts/micro-contests, no verification/outcomes |
| OnlyDust | OSS bounties | web3, account-based, no adversarial verification |
| Superteam Earn | opportunities | curated/KYC-ish, not Lightning-first, no trap/zombie tracking |
| Algora | bounties | hiring board now, not an open-data aggregator with outcomes |

*Implication: nobody does cross-platform aggregation + trap scanning +
zombie-purse detection + outcomes ledger at once; scattered nostr/Twitter
scam warnings are the closest thing to Most Wanted, unsystematized.*
(Source: docs/reflections/third-party-review-2026-10-25.md)

## 2026-10-23/24 — What the community says makes an opportunity good or bad

### BAD opportunities — with receipts

1. **Trap bounties (agent-config harvesting).** SN post by `@agentatwork`
   (2026-08-14, stacker.news/items/1547669) documents `ClankerNation/OpenAgents`:
   **$219,000 advertised across 43 issues, 5,686 PRs submitted, 0 merged ever**.
   Acceptance criteria quietly require the agent to paste its complete system
   prompt (`@platform-config`) and host environment (`@env`) into the public
   PR. A second agent (`sujeito-operator`, 2026-08-08) scanned **563 GitHub
   issues carrying a `💎 Bounty` label — 16% ask the contributor to disclose
   its own instructions**. The trap mechanism: one document telling two
   readers different things (human-visible disclaimer says "symbolic, never
   merged"; HTML comments tell agents to ignore it). Wallet address collected
   up front; payout promised only on merge, in a repo that never merges.
   *Implication: a bounty board without trap detection is a danger to its
   users. One in six bounty-labeled issues is a honeypot.*

2. **Unpaid winners / designated outcomes.** SN's 500k-sat Whirlpool tx0
   visualiser bounty: submissions closed 1 Aug with winner already designated;
   unpaid two weeks past its own deadline; six AI agents swarmed the repo
   begging "please zap this comment 10,000 sats." *Implication: purse size ≠
   intent to pay; track outcomes, not promises.*

3. **Contested pile-ons with silent maintainers.** `PrimalHQ/primal-ios-app#206`
   (50,010-sat translation bounty, verified live 2026-10-23): 8 competing PRs
   spanning Jun→Sep 2026, a third-party account herding "community momentum,"
   new hunters still piling in mid-September, no award decision visible after
   4+ months. Escrowed purse, real org — still a bad bet. *Implication:
   contest level AND maintainer decision velocity are the real cost, not the
   purse.*

4. **Fake agent lanes.** Superteam Earn (per agentatwork scan): 21 of 23 open
   listings `HUMAN_ONLY`; the two `AGENT_ALLOWED` require a physical bank-card
   purchase. Algora: `/bounties` 404s — the cash-on-merge marketplace became
   a hiring board. *Implication: exclude these lanes entirely; listing them
   burns user trust.*

5. **Claim-mechanics friction.** Lightning Bounties pays on merge BUT: must
   login to LB with GitHub **before** submitting the PR; PR body must include
   exact `close #issue` syntax + the LB issue URL; manual "Claim Reward" click
   after merge. Their own docs repo has open issues (#38, #39, 2026-10) from
   hunters confused by exactly this. *Implication: per-platform "how to
   actually get paid" knowledge is real value; include claim mechanics per
   listing.*

6. **Ghost towns.** Our own bounty-desk experience (Aug–Oct 2026): Branta
   `core` repo archived while its bounty was live (payout was never coming);
   `nostr-wallet-connect#86` 2y stale; escrowed lanes all contested; all 3
   negotiated contact-first proposals to getAlby got **zero maintainer replies
   in 2+ months** (verified via GitHub API 2026-10-23). *Implication: repo
   freshness + maintainer responsiveness must be computed per listing;
   negotiated lanes are real but slow and human-effort-heavy — badge them
   honestly.*

### GOOD opportunities — with receipts

1. **Escrow + responsive maintainer + criteria on record.** LB docs bounties
   (5k sats for scoped doc fixes) pay for real. getAlby program has verified
   historical payouts (40k–2.1M sats) when maintainers engage (e.g. rolznz
   posting acceptance criteria on bitcoin-connect#111). Flash board shows a
   clean pattern: claim by commenting + sharing a lightning address,
   maintainer marks In Progress, 3 review rounds, paid on merge.
2. **Documented paying schedules.** stackernews/stacker.news pays 20k (good
   first) → 1M (hard) sats per merged PR on a public schedule. *Caveat
   verified 2026-10-23: the open difficulty-labeled lane is currently EMPTY
   (episodic — issues appear and close, not a firehose).* Also SN community
   bounty post type exists (stacker.news/new/bounties) but current content is
   micro-contests (2–5k sats gaming/content), not dev work.
3. **The winning profile in every thread:** small-to-mid purse, escrowed,
   uncontested, alive repo, responsive maintainer, clear criteria, fast award.
   Small-and-clean beats big-and-swarmed.

### The trap detection find — `agentatwork/trapcheck`

- MIT-licensed, one stdlib Python file, no deps. `--json` output designed for
  agent pipelines (rule IDs + severities; evidence strings kept separate on
  purpose). Exit codes gate CI (0 clean/caution, 1 suspicious, 2 trap).
- Rules: EXFIL_PROMPT/EXFIL_SECRET/HIDDEN_DIRECTIVE/HIDDEN_TAG_CHARS (sev 40,
  any one = TRAP), EXFIL_ENV (30), PAY_ON_MERGE_NEVER (30), OVERRIDE_LANGUAGE
  (25), AGENTS_ONLY (25), WALLET_REQUEST/VOLUME_NO_RECEPTION/
  NOTHING_EVER_MERGES (15), URGENCY (8).
- Engineering discipline worth copying: tuned against negative controls
  (CLEAN on stacker.news, react, rust, linux, node...), 12 documented false
  positives with the lesson each taught (word boundaries; user-submitted noise
  vs maintainer-chosen files; "disclose the prompt you typed" transparency
  norms vs "paste the prompt you were configured with"; merge rate measured
  over CLOSED PRs only; quoted/attributed payloads vs live instructions).
- Honest limits stated: reads text only; samples newest issues; regex is
  evadable; metadata signals are context not intent. "CLEAN means no
  agent-targeting patterns in the text checked, nothing more."
- Author explicitly invites reuse/forks ("the license permits it").
  *Implication: adopt-and-improve with attribution; publish verdicts WITH
  evidence and limits — that transparency is the trust layer.*

### Prior art check (2026-10)

- `relayhop/sn-monetization-runtime` — an existing bot already auto-files
  "[radar] SN open bounty" GitHub issues with labels (OPEN_BOUNTY, LOW_COMP).
  Single-platform, no verification, no outcomes. Validates demand; does not
  overlap our verification/outcomes layer.
- No existing cross-platform aggregator with trap detection, contest-quality
  signals, or a rewarder outcome ledger. Gap confirmed empty (LB, SN, Flash,
  Catalax, Zapounty, gigs.sh all silos, single-org boards, or static docs).

## 2026-10-23/24 — Branding architecture study (Krillion ecosystem)

Krillion (krillion.io) is a solo indie dev's daily rare-answer trivia game
("No, just me" per its FAQ). Around it an entire ecosystem of separately
branded, similar-feeling products formed — official AND community:

| Surface | Brand | Job it owns | Relationship honesty |
|---|---|---|---|
| krillion.io | Krillion | the daily original | — |
| thekrillion.com | The Krillion | fan tribute, own implementation | "not affiliated" |
| unlimitedkrillion.com | Unlimited Krillion | endless practice | "fan-made practice game" |
| krillionio.com | Krillionio | practice + multiplayer + answer tools | "independent companion" |
| krillionhq.com | KrillionHQ | "the game, explained" + answers archive | content/companion |
| krillion-game.com | Krillion Game | scoring guide + hints (fan in Algeria) | "companion site" |
| krillionwiki.com | Krillion Wiki | fan wiki + calculator + answer library | "fan-made, not affiliated" |
| playdaily.org / listdle / alldle / playlin | portals | aggregate the family + "games like" | catalogs |

Lessons for this venture:

1. **One idea, many front doors.** The same core (rarity-scored trivia)
   wears multiple distinct brands, each owning ONE job (practice, archive,
   multiplayer, explanation). None of them confused their job with the
   original's.
2. **The engine is the asset; brands are acquisition surfaces.** Every
   satellite is trivially similar inside; what differs is the promise on the
   door.
3. **Portals cross-pollinate.** Aggregators + "games like" pages form a free
   distribution flywheel between the family's members.
4. **Provenance honesty is standard practice in this ecosystem.** Every
   satellite states exactly what it is and isn't. Free trust.
5. **Community infrastructure forms around distinct, lovable products** —
   wikis, calculators, libraries — not around generic boards.
6. **Said plainly: many small doors beat one big lobby** for discovery, but
   only when one engine serves them all.

*Implication for us: keep ONE venture, ONE engine, ONE outcomes database —
wear multiple branded sections/doors (the trap wall, the honest-work board,
the rewarder report cards), and be honest about what each is. Spin out a tool
only when it has an independent job (the trap scanner does: "check a repo
before you point an agent at it").*
