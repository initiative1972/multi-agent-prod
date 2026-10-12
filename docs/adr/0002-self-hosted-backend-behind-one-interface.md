# ADR 0002 — Self-hosted backend behind a one-method interface

**Status:** accepted

## Context
The portfolio theme is open-weight / self-hosted operations. Agents must run
against a model you host (vLLM / TGI), not a managed API. But CI must stay fast,
free, deterministic, and offline.

## Decision
Depend on a single interface, `LLMClient.complete(system, user)` (`llm/base.py`).
Two implementations:

- `DeterministicLLM` (default) — no weights, no network, no randomness. Reads
  the role tag + a few markers and returns the structured output agents parse.
- `OpenAICompatLLM` — a thin, lazy-`httpx` client for any OpenAI-compatible
  server. Selected by `MAP_PROVIDER=openai_compat` + `MAP_BASE_URL`.

## Consequences
- CI and tests are reproducible to the byte and need no GPU.
- Swapping to a live self-hosted model is configuration, not code.
- **Honesty:** behaviour and evals are verified against the mock. Live numbers
  depend on the operator's hardware and weights and are not claimed here.
