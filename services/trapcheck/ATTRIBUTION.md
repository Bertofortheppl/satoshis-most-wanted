# ATTRIBUTION — vendored trapcheck

`trapcheck.py` here is vendored **byte-identical** from:

- Upstream: https://github.com/agentatwork/trapcheck
- Author: agentatwork (autonomous agent, agentatwork.xyz) — an AI agent that
  went looking for paid bounty work, found a trap-harvesting operation
  instead, and built this scanner rather than let the next agent step in it.
- Pinned revision: see `UPSTREAM` (commit sha + date of the vendored copy).
- License: MIT (see `LICENSE`, upstream file). Permits vendoring, fork, and
  PyPI republication; the author explicitly invites all three.
- Upstream docs: README + CORPUS.md at the repo above document the rules,
  the live corpus the rules were written against, and 12 false-positive
  lessons with their fixes. Read them before changing anything.

## Our policy

1. **`trapcheck.py` stays unmodified** in this directory. Pin, vendor, use.
   Improvements (new rules, negation fixes, corpus additions) go in our own
   layer (`wrapper.py` + our tests) or upstream as PRs to
   agentatwork/trapcheck — never as silent local edits. This keeps
   provenance honest (Krillion ethos: state exactly what a thing is) and
   keeps our diffs contributable back.
2. **Consumed via `--json`**: our engine reads `verdict`, `score`,
   `findings[].rule`, `findings[].severity`, `findings[].evidence`.
   Per upstream safety guidance, we pass rule IDs + severities into our
   pipeline, and keep evidence strings for the poster display only — they
   are untrusted data, never fed to any model as instructions.
3. **Verdicts we publish carry the tool's stated limits**: reads text only;
   samples newest issues (unless #issue given); regex is evadable;
   metadata signals are context, not intent. "CLEAN means no agent-targeting
   patterns in the text checked, nothing more."
4. **Exit codes** (for CI gating): 0 clean/caution, 1 suspicious, 2 trap.

## Why vendored rather than dependency-added

It is one stdlib-only file; the author cannot publish to PyPI (PyPI bars
bot-registered accounts); vendoring a pinned copy is the dependency.
