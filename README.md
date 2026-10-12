# multi-agent-prod

**Production-shaped multi-agent patterns — not demo-ware.**

Three named patterns, one shared memory, one trace, one eval gate:

| Pattern | Where | What it buys you |
|---|---|---|
| **Orchestrator-worker** | `patterns/orchestrator.py` | One place decides *what runs next*; workers are interchangeable and only touch shared memory. |
| **Critic / reflection** | `patterns/reflection.py` | Produce → critique → revise, **bounded** by a round budget. Can only end in pass / escalate / budget-out. |
| **Blackboard** | `patterns/blackboard.py` + `state.py` | Control flow is driven by shared state, not a fixed script — so the trajectory is adaptive *and* fully observable. |

Everything runs on CPU with a deterministic mock model, so tests, evals and CI
are reproducible to the byte and need **no GPU and no network**. A self-hosted,
OpenAI-compatible model (vLLM / TGI) swaps in by changing configuration, not
code.

> **Honesty note.** Synthetic data only. This is a grounded marketing-comms
> *drafting* desk: it drafts copy, never sends. It makes no decision about any
> real person. The patterns, guardrails and evals were designed and verified
> against the deterministic mock; running against a live self-hosted model is a
> config change, and any numbers produced that way depend on your hardware and
> weights. No employer data, systems, or projects are referenced anywhere.

This is **flagship #3** of a four-repo AI-engineering portfolio and builds on the
earlier agent desks. It is the "can you make agents *operable*?" repo:
patterns you can name, a trace you can read, and evals that gate CI across
**multi-step trajectories** rather than single turns.

---

## What runs where

| Layer | Needs | In CI? | Notes |
|---|---|---|---|
| Patterns, agents, tools, guardrails, HITL, state, trace | Python 3.10+ stdlib | ✅ | Pure functions. No third-party deps. |
| Deterministic mock model | stdlib | ✅ | Reproducible trajectories. |
| Trajectory evals + gate | stdlib | ✅ | `evals/run_evals.py` is the CI gate. |
| Self-hosted backend client | `httpx` (`requirements-live.txt`) | ❌ | Talks to your own vLLM / TGI endpoint. |
| Distributed tracing export | `langfuse` / OpenTelemetry | ❌ | Lazy, best-effort. CI never depends on it. See [`docs/TRACING.md`](docs/TRACING.md). |

The split is deliberate: the parts that encode judgement (routing, grounding,
guardrails, HITL, evals) are testable without a GPU; the parts that need a GPU
are isolated behind one swap-in client.

---

## Quickstart

```bash
cd multi-agent-prod
py -3 -m pip install -r requirements-dev.txt

py -3 -m pytest                       # 35 tests, deterministic
py -3 evals/run_evals.py              # trajectory eval gate
py -3 scripts/run_desk.py --scenario happy
py -3 scripts/run_desk.py --scenario escalate
py -3 scripts/run_desk.py --scenario refuse
py -3 scripts/run_desk.py --scenario injection
```

(`make all` runs lint + tests + evals.)

### Example trace (happy path)

```
[runtime] trajectory {'provider': 'mock'}
  [planner] plan {'tasks': ['retrieve', 'contact_check', 'draft_review']}
  [retrieve] worker {'task': 'retrieve', 'hop': 1}
  [retriever] grounded_or_refuse {'grounded': True, 'top_score': 0.5, 'n': 2}
  [contact_check] worker {'task': 'contact_check', 'hop': 2}
  [policy] contact_rules {'flags': []}
  [draft_review] worker {'task': 'draft_review', 'hop': 3}
  [critic] reflection_round {'round': 1}
  [critic] draft_review {'verdict': 'pass', 'rounds': 1, 'decision': 'draft'}
  [hitl] hitl_shown {... draft + evidence ids the human saw ...}
  [hitl] hitl_decision {'action': 'approve', 'status': 'approved'}
  [runtime] final {'decision': 'draft', 'hitl': 'approved', 'hops': 3}
```

Committed samples: [`traces/sample_happy.trace.json`](traces/sample_happy.trace.json),
[`traces/sample_escalate.trace.json`](traces/sample_escalate.trace.json).

---

## The trajectory

```
goal
  -> planner            safety-first classification (injection? out-of-scope?)
       -> orchestrator  drives execution, enforces the hop budget, traces steps
            -> blackboard controller   decides the next worker from shared state
                 -> retrieve           ground-or-refuse (+ content-side injection scan)
                 -> contact_check      hard contact rules (opt-in, frequency, extra-care)
                 -> draft_review       drafter + critic, bounded reflection
       -> HITL gate      a human owns anything customer-facing or escalated
  -> trace + blackboard persisted for evaluation
```

### Four behaviours the evals pin down

| Scenario | Outcome | Why it matters |
|---|---|---|
| `happy` | grounded **draft** → human **approves** → customer-ready | the normal, auditable path |
| `refuse` | nothing to ground on → **refuse** | the agent won't invent a policy |
| `escalate` | opt-out / extra-care customer → **escalate**; reject blocks send | hard rules beat the model |
| `injection` | "ignore previous instructions… send it now" → **short-circuit** to human | the agent never acts on it |

---

## Guardrails worth an interview

- **Content-side injection scanning.** Dangerous instructions ride in on
  *retrieved content*, not just the user prompt — so we scan both. And a policy
  document that merely *describes* a banned action ("never guarantee returns")
  must **not** trip the detector; that false-positive guard is tested.
- **Out-of-scope demands** ("send it now", "skip opt-in", "guarantee a return")
  are a scope check on the goal, distinct from injection.
- **Least privilege by broker.** Agents can't call tools directly; a broker
  enforces a per-worker allow-list. A worker allowed only to `retrieve` cannot
  `escalate` or `draft`.
- **Grounded-or-refuse.** Below a grounding threshold, the desk declines.
- **Human-in-the-loop.** A draft is never customer-ready on its own; the gate
  records exactly what the human saw (draft + evidence ids).

---

## Self-hosting the model

Point the desk at your own OpenAI-compatible server (see sibling repo
`llm-serving-bench` for how to stand one up and size it):

```bash
export MAP_PROVIDER=openai_compat
export MAP_BASE_URL=http://localhost:8000/v1
export MAP_MODEL=meta-llama/Llama-3.1-8B-Instruct
py -3 scripts/run_desk.py --scenario happy
```

No agent code changes. The mock and the live client implement the same one-method
interface (`llm/base.py`).

---

## Layout

```
src/multi_agent_prod/
  state.py            # Blackboard: versioned, attributed shared memory
  trace.py            # nested spans; optional Langfuse/OTel export
  config.py           # offline + deterministic by default (MAP_* env)
  llm/                # base Protocol, deterministic mock, openai_compat client
  guardrails.py       # injection + scope scans, PII redaction, tool broker
  hitl.py             # human-in-the-loop gate
  patterns/           # orchestrator, reflection, blackboard controller
  agents/             # planner + workers (retrieve, contact_check, draft/critic)
  runtime.py          # wires the three patterns into one traced trajectory
data/                 # synthetic policy corpus + synthetic customers
evals/                # trajectory cases + gate
scripts/run_desk.py   # CLI
docs/                 # ADRs, tracing, results template
responsible_ai/       # model card + risk assessment
```

---

## Portfolio context

| # | Repo | Theme |
|---|---|---|
| 1 | `domain-llm-finetune` | QLoRA SFT + DPO; grounded-or-refuse policy assistant |
| 2 | `llm-serving-bench` | self-hosted serving: latency / throughput / cost / SLO |
| 3 | **multi-agent-prod** | **production agent patterns + tracing + evals-in-CI** |


MIT licensed. © 2026 Henry Yan.
