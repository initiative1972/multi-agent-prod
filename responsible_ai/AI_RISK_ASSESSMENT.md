# AI Risk Assessment — multi-agent-prod

Lightweight, portfolio-level assessment. Synthetic data; no production use.

| # | Risk | Likelihood | Impact | Mitigation (in this repo) |
|---|---|---|---|---|
| R1 | Agent sends / acts autonomously | Low | High | No send capability exists. HITL gate; "draft is never customer-ready" is enforced and tested. |
| R2 | Ungrounded / fabricated claims | Med | High | Grounded-or-refuse threshold; critic requires a cited policy or returns `revise`; eval `grounded` check. |
| R3 | Prompt injection via user or retrieved content | Med | High | Content-side injection scan on goal **and** excerpts; short-circuit to human; eval `injection` case. False-positive guard on policy text that *describes* bans. |
| R4 | Contacting opted-out / vulnerable customers | Med | High | Hard contact-rule checks (opt-in, frequency, extra-care); critic escalates on any flag; eval `escalate` case. |
| R5 | Over-broad tool access | Low | Med | Least-privilege broker with per-worker allow-list; `ToolNotAllowed` tested. |
| R6 | Unbounded loops / runaway cost | Low | Med | Hop budget on the orchestrator; bounded reflection rounds; both tested. |
| R7 | PII leakage into prompts/logs | Low | Med | PII redaction on the incoming goal; traces store evidence ids and decisions, not raw PII. |
| R8 | Unobservable behaviour | Med | Med | Full span trace + blackboard snapshot persisted per run; trajectory evals in CI. |

## Residual risk
This is a demonstration on synthetic data with a mock model by default. It is
not approved for, and must not be used for, real customer communication or any
decision about a real person. Before any real use, the model, corpus, retrieval,
and guardrails would need independent review and sign-off.
