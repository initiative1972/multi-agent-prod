# Tracing

Every trajectory is a tree of spans (`src/multi_agent_prod/trace.py`). A span
has an id, a parent id, an agent, a name, timing, and attributes. Nesting is
automatic via a context manager:

```
trajectory
  planner
    plan (event)
  worker[retrieve]
    grounded_or_refuse (event)
  worker[contact_check]
  worker[draft_review]
    reflection_round
  hitl_shown / hitl_decision (events)
  final (event)
```

## Local (default, in CI)
Spans are collected in-process and written to
`traces/<run_id>.trace.json` plus a `traces/<run_id>.blackboard.json` snapshot.
Committed samples live at `traces/sample_*.json`. No service required.

## Live export (optional)
`Tracer.export_langfuse(trace_name)` lazily imports the Langfuse SDK and ships
the same spans. It returns `False` (no-op) if the SDK or credentials are absent,
so **CI never depends on an external service**.

```python
from multi_agent_prod.trace import Tracer
tracer = Tracer()
# ... run_desk(..., tracer=tracer) ...
tracer.export_langfuse("comms-desk-prod")   # True if shipped, False if not configured
```

OpenTelemetry export would follow the same shape: map each `Span` to an OTel
span with `parent_id` as the parent context. The span model here is
deliberately OTel-friendly (id / parent_id / name / attributes / duration).

## Why this matters
Tracing is the difference between "the agent did something" and "here is the
exact path, what it was grounded on, which guardrail fired, and what the human
saw before approving". That record is what makes an agent *operable* and
*auditable* — and it is what the trajectory evals assert against.
