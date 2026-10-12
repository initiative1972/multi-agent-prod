# ADR 0003 — Trajectory evals are the CI gate

**Status:** accepted

## Context
Single-turn evals ("is this one answer good?") miss the failures that hurt in
production: the agent that drafts when it should refuse, that sends when a
human must approve, that acts on injected instructions, or that loops forever.

## Decision
`evals/run_evals.py` runs **whole multi-step trajectories** and asserts
properties of the *run*, not of a token:

- `decision` — draft / refuse / escalate as expected
- `grounded` — a draft is backed by retrieved evidence (never invented)
- `customer_ready` — anything sendable passed through a human
- `flags` — the right policy/safety flags were raised
- `bounded` — reflection stayed within its round budget

The script exits non-zero on any failure and is wired as a required CI step
(`.github/workflows/ci.yml`).

## Consequences
- Regressions in *behaviour* (not just syntax) fail the build.
- The eval cases double as living documentation of the contract.
- New behaviours are added by adding a case + the property it must satisfy.
