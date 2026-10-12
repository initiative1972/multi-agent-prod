# Model / System Card — multi-agent-prod

## What this is
A multi-agent system that **drafts** grounded marketing-comms copy and routes
anything consequential to a human. It is a *system* card more than a *model*
card: the behaviour comes from the orchestration, guardrails, and HITL around
the model, not only from the model.

## Intended use
- Demonstrate production multi-agent patterns (orchestrator-worker, critic/
  reflection, blackboard) with tracing and trajectory evals.
- Draft grounded, policy-safe copy for a human to review and send.

## Out of scope / prohibited
- **Not a send.** The system never contacts anyone.
- **Not a decision** about any real person (no credit, pricing, eligibility, or
  account action).
- No real customer data. Synthetic corpus and synthetic customers only.

## Model
- Default: `DeterministicLLM` (a rules-based mock) for reproducibility.
- Optional: any OpenAI-compatible self-hosted model (vLLM / TGI) via
  `llm/openai_compat.py`. Choice of weights is the operator's.

## Data
- `data/corpus/*.md` — synthetic product/policy snippets, authored for this repo.
- `data/customers.json` — two synthetic customer profiles.

## Guardrails
- Content-side prompt-injection scanning (goal + retrieved content).
- Out-of-scope demand detection (goal).
- Least-privilege tool broker.
- Grounded-or-refuse retrieval threshold.
- Human-in-the-loop gate on anything customer-facing or escalated.
- PII redaction on the incoming goal.

## Evaluation
Trajectory-level evals (`evals/`) assert decision, grounding, human-gating,
flags, and bounded reflection across four scenarios. Run as the CI gate.

## Known limitations
- The mock model is deterministic by design; it does not represent the quality
  or failure modes of a real LLM. Live behaviour depends on the chosen weights.
- Retrieval is deterministic token-overlap, not a production hybrid retriever.
- The corpus is tiny and illustrative.

## Honesty statement
Patterns, guardrails, and evals were designed and verified against the mock.
"Runs vs design" is kept explicit: what runs in CI is stated; what requires a
GPU/live model is flagged and not claimed as measured here.
