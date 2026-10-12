# Results (template)

Fill this in after a run. Keep "design vs measured" explicit.

## CI (deterministic, mock model) — reproducible
- Unit tests: `__ / 35` passing
- Trajectory evals: `__ / 4` cases passing
- flake8: clean

Paste the latest `evals/reports/last_run.json` summary:

```json
{ "passed": 4, "total": 4 }
```

## Live self-hosted run (optional) — environment-dependent
> These numbers depend on your hardware and weights. They are **measured on the
> operator's setup**, not claimed by this repo.

| Field | Value |
|---|---|
| Model / weights | e.g. Llama-3.1-8B-Instruct |
| Server | vLLM / TGI, version |
| Hardware | e.g. 1× A10G 24 GB |
| Scenario | happy / refuse / escalate / injection |
| Decision | |
| Grounded? | |
| Human-gated? | |
| Trajectory latency (ms) | |
| Reflection rounds | |

## Trace artefacts
- `traces/sample_happy.trace.json`
- `traces/sample_escalate.trace.json`
- (optional) Langfuse trace link
