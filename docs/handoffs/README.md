# Session Handoffs — the bridge between review and dev sessions

Free sessions (review/planning) and paid sessions (dev) hand off through
FILES, never chat history. Every session that changes anything ends by
writing one handoff file here: `YYYY-MM-DD-<kind>.md` where kind is
`review` or `dev`. Any next session reads the newest handoff FIRST.

## Template

```markdown
# <date> <kind> handoff — <one-line summary>

## What changed
- (files/decisions, with pointers)

## What's blocked / open questions
- (owner gates, unknowns, blockers)

## Exact next steps (for the next session)
1. (concrete, actionable, ordered — with file pointers, not chat memory)
```

## Rules

1. **Review sessions write reflections + planning, not code.** Their
   output lands in `docs/reflections/` and PLANNING.md; they end with a
   `*-review.md` handoff.
2. **Dev sessions start by reading**: the newest handoff here, then
   PLANNING.md decision queue, then the SPEC section they touch.
3. **The decision queue in PLANNING.md is the API** — items move
   between sessions only through it.
4. **Never re-explain context in chat** — point at the artifact instead.
