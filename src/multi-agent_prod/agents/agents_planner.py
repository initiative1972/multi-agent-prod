"""Planner: the safety-first decomposition step.

Before any tool runs, the planner classifies the request. If it carries an
instruction-injection, or an out-of-scope demand ("send now", "skip opt-in",
"guarantee returns"), the trajectory short-circuits straight to a human — the
agent never gets the chance to act on it. Otherwise it declares the agenda the
orchestrator/blackboard will execute.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from multi_agent_prod.guardrails import scan_injection, scan_scope
from multi_agent_prod.state import Blackboard


@dataclass
class Plan:
    tasks: list[str] = field(default_factory=list)
    # (decision, reason, flag_code) when the request must not proceed; else None.
    short_circuit: tuple[str, str, str] | None = None


def make_plan(bb: Blackboard, enable_injection_scan: bool = True) -> Plan:
    if enable_injection_scan:
        injection = scan_injection(bb.goal)
        if injection:
            return Plan(
                short_circuit=(
                    "escalate",
                    f"instruction-injection in request: '{injection[0]}'",
                    "SEC-INJECTION",
                )
            )
        scope = scan_scope(bb.goal)
        if scope:
            return Plan(
                short_circuit=(
                    "escalate",
                    f"out-of-scope demand the agent must not fulfil: '{scope[0]}'",
                    "OOS-SCOPE",
                )
            )
    tasks = ["retrieve"]
    if bb.customer_id:
        tasks.append("contact_check")
    tasks.append("draft_review")
    return Plan(tasks=tasks)
