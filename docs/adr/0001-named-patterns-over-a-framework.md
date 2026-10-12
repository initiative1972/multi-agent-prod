# ADR 0001 — Name the patterns; don't hide them in a framework

**Status:** accepted

## Context
The brief for this repo is "production agent engineer, not demo-ware". The
easy path is to import a big agent framework and wire a graph. That hides the
three decisions that actually matter in production — *what runs next*, *how do
we revise safely*, and *where does shared state live* — inside library magic.

## Decision
Implement three **named, separable** patterns in plain Python:

- **orchestrator-worker** (`patterns/orchestrator.py`) — owns the control loop,
  the hop budget, and tracing.
- **critic / reflection** (`patterns/reflection.py`) — bounded produce→critique
  →revise.
- **blackboard** (`patterns/blackboard.py` + `state.py`) — the single shared
  memory and the "what next?" controller.

Each is independently unit-tested. The runtime composes them.

## Consequences
- Every control decision is in a small, testable place.
- The repo reads as *engineering*, not configuration.
- A framework (LangGraph, etc.) can later back the same interfaces; the pattern
  boundaries would not move. That is the point.
