"""multi-agent-prod: production-shaped multi-agent patterns.

Three named patterns, one shared memory, one trace, one eval gate:

* orchestrator-worker  (``patterns.orchestrator``)
* critic / reflection  (``patterns.reflection``)
* blackboard           (``patterns.blackboard`` + ``state.Blackboard``)

The ``core`` runs on CPU with a deterministic mock model so tests, evals and
CI are reproducible and need no GPU or network. A self-hosted, OpenAI-compatible
model (vLLM / TGI) can be swapped in via ``llm.openai_compat`` without touching
agent logic. Synthetic data only.
"""

from __future__ import annotations

__version__ = "0.1.0"
