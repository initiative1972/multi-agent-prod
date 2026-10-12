"""Critic / reflection pattern.

Produce a candidate, have a critic judge it, and revise within a bounded number
of rounds. The loop can only end three ways: the critic *passes* it, the critic
*escalates* it to a human, or the round budget runs out (which we also treat as
escalate upstream). There is no unbounded "keep trying" — that is the difference
between a pattern that survives production and a demo that loops forever.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

# produce() -> candidate text
# critique(candidate) -> (verdict, reason) where verdict in {pass, revise, escalate}
Produce = Callable[[], str]
Critique = Callable[[str], tuple[str, str]]


@dataclass
class ReflectionResult:
    output: str
    verdict: str
    reason: str
    rounds: int


def reflect(
    produce: Produce,
    critique: Critique,
    max_rounds: int,
    tracer: Optional[object] = None,
) -> ReflectionResult:
    output = ""
    verdict, reason = "revise", "not yet produced"
    rounds = 0
    while rounds < max(1, max_rounds):
        rounds += 1
        if tracer is not None:
            with tracer.span("reflection_round", agent="critic", round=rounds):
                output = produce()
                verdict, reason = critique(output)
        else:
            output = produce()
            verdict, reason = critique(output)
        if verdict in ("pass", "escalate"):
            break
    return ReflectionResult(output=output, verdict=verdict, reason=reason, rounds=rounds)
