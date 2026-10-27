# Planning & Reflection — Satoshi's Most Wanted

> Living document, updated at milestones (not per sprint): where we are,
> what the data says, risks, the owner's review guide, and the decision
> queue. The retrospective arc lives at the bottom.

## Where we are — end of Sprint 1 (2026-10-24)

- Pipeline fully live: GitHub Actions cron every 3h, run #1 green, data
  auto-commits, email-on-failure monitoring. The laptop is out of the
  critical path.
- 46+ hermetic tests pin the engine; scan caching landed per D8 (verdict
  ledger committed as data; raw API cache ephemeral + actions/cache warm).
- **The wall: 1 poster** (getAlby#151, negotiated-engaged 🤝) — thin and
  honest.
- **Most Wanted: 0 traps** — the current sources (LB feed, getAlby) don't
  surface the wild `💎 Bounty`-label population; that source is unwired.
- **The Assay: 30 rewarder cards, all zeros** — day one of compounding.
- **Verdict ledger: 30+ repos scanned.** First-day findings: 11 zombie
  purses (merged fix, still listed open), graveyards of 7 and 3 dead
  attempts, getAlby lane measured cold (4/30 with ≤60d engagement).

## What the first data says (observation → implication)

1. **11 of the LB items with attempt history are zombie purses** → LB's
   feed cannot be trusted at face value; our merged-attempt block is the
   differentiator nobody else has. Consider surfacing "zombie" as an
   explicit tracked status in the site, not just a fail reason.
2. **getAlby lane is real but narrow** (4/30 engaged) → expect 1–3
   negotiated posters at any time, not 10. The D7 condition has teeth.
3. **The wall's thinness is a source problem, not a bar problem** → D7
   revisit-trigger armed: widen sources before loosening gates.
4. **SN repo bounty lane is empty today** (episodic by nature) → keep
   tracking; it feeds The Assay's SN rewarder card when it wakes.
5. **The three most-wanted-worthy traps are not ingested** — the trap
   population lives in the wild bounty-label space (ClankerNation & the
   16% harvest pattern). Source breadth fixes both doors at once.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| LB public feed changes shape (undocumented API) | Adapter isolated; E2E corpus pins the mapping; failure = visible email, not silence |
| GitHub rate limits as sources widen | D8 verdict ledger + warm gh cache + per-read pacing; watch 403s in run logs |
| Trap freshness (7-day rescan window) | Posters always carry scanned-at; site can visually age stale verdicts; decisive-rule bar keeps shame posters strict |
| Scanner false positives on a public shame wall | Severity-40-only decisive rules, evidence always published, dispute path + takedown-on-change (D5 guardrails, binding) |
| Wall under 5 posters looks dead to visitors | The doors frame: Assay + tracked data are content too; source breadth (not gate loosening) is the fix; revisit-trigger formalized |
| Single-maintainer bus factor | Everything deterministic + DECISIONS.md is the bus — any future agent/dev can resume from the docs alone |
| PAT expiry ~2027-01-22 breaks the cron | Logged in parent NOTES + AGENTS.md; GitHub emails the owner on failure; rotate on the reminder |
| Publishing something wrong on the shame wall | Evidence-first + tool limits always quoted + neutral voice (D5/D6); corrections via public dispute issue |

## Owner review guide (what to look at, and the questions worth sitting with)

1. **Actions tab** — the runs, every 3 hours. Real work, green, visible.
2. **`docs/reports/honest_work.md`** — is the 🤝 poster what you expected
   "every poster is real" to mean?
3. **`data/posters.json`** — open any tracked item, find
   `bar_fail_reasons`: is the explanation honest, and would it have saved
   you an afternoon?
4. **`docs/reports/the_assay.md`** — day-one zeros; does the framing
   promise the right thing?
5. **Questions to sit with:** Do you trust the wall? What's missing from
   "real"? Is the strictness the right personality for the town?

## Reflections (external review sessions land here)

- **2026-10-25 third-party review** (`docs/reflections/third-party-review-2026-10-25.md`):
  positioning = "consumer protection layer for Bitcoin dev bounties";
  confirms outcomes-wiring + bounty-label-sweep as the top two moves;
  adds "market the avoid angle first" for distribution. Competitive map
  (OnlyDust/Algora/Superteam/LB/SN) folded into RESEARCH.md.

## Decision queue (awaiting owner)

- **#1 Wire LB awarded/paid outcomes** (confirmed by third-party review
  2026-10-25): ingest awarded LB items as status="awarded" — also fixes a
  latent bug where awarded items vanish and could emit false "expired"
  events. The Assay's live tracking gets real receipts.
- **#2 Bounty-label sweep** (`💎 Bounty` label corpus) — feeds Most Wanted
  + Honest Work; sweep cadence weekly with rate-limit pacing.
- Public board-update notifications — PUNTED (owner 2026-10-24) to the
  distribution sprint. Mechanisms: public TG channel, RSS, nostr notes.
  Distribution should market the AVOID angle first (review 2026-10-25).
- health.py → Telegram operator alert (small sprint).
- Parent `satonomous` repo — PUSHED 2026-10-24. Done.

## Growth direction — teaching the market to exist (owner instinct 2026-10-24)

"If we have to educate people about how to build bounties that will be
seen and posted, that's fine — it's a marketing angle that creates the
market and incentivizes best practices." The bar's fail reasons ARE the
curriculum: a future "bounty poster's guide" (how to escrow, write
acceptance criteria, keep maintainers responsive — derived from the
strict-bar gates and The Assay's cards) turns the engine's judgment into
public education. Logged as a later-sprint direction, not current scope.

## The arc — why this design, honestly

The 2026-10-22 autopsy of the failed venture set five design laws:
(1) monitor the service path itself; (2) never couple liveness to the
owner's laptop or attention; (3) demand evidence before building;
(4) deterministic backbone over agent improvisation; (5) owner gates on
external actions. Sprint 1 is those laws as architecture — cron on
GitHub's clock (2), email-on-failure (1), evidence-first posters +
RESEARCH.md before any build (3), 48 hermetic tests and no LLM anywhere in
the data path (4), DECISIONS.md with recorded rationale at every fork (5).

**Not yet law-proofed (honest list):** the tip-jar rail still depends on
the hub/box being awake (the uptime caveat survives); `health.py →
Telegram` lands next sprint; outcome detection currently sees open/closed
only — awarded/paid transitions (LB `winner_data`) must be wired before
The Assay can show a single nonzero honestly; and Most Wanted stays empty
until the bounty-label sweep exists.
