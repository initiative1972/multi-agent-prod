"""Runtime: wire the three patterns into one observable trajectory.

    planner (safety decomposition)
       -> orchestrator-worker  (drives execution)
          -> blackboard controller  (decides what runs next)
             -> retrieve / contact_check / draft_review(critic+reflection)
       -> HITL gate  (a human owns anything customer-facing or escalated)
       -> trace + blackboard persisted for later evaluation

Everything is deterministic under the mock model, so the exact same call runs
in CI and against a self-hosted model (swap the provider, not the code).
"""

from __future__ import annotations

import json
from pathlib import Path

from multi_agent_prod.agents.context import Context
from multi_agent_prod.agents.planner import make_plan
from multi_agent_prod.agents.workers import default_workers
from multi_agent_prod.config import Settings, get_settings
from multi_agent_prod.guardrails import ToolBroker, redact_pii
from multi_agent_prod.hitl import apply_hitl, requires_hitl
from multi_agent_prod.llm import LLMClient, get_llm
from multi_agent_prod.patterns.blackboard import BlackboardController
from multi_agent_prod.patterns.orchestrator import Orchestrator
from multi_agent_prod.state import Blackboard, Decision, HitlStatus
from multi_agent_prod.trace import Tracer


def run_desk(
    goal: str,
    *,
    customer_id: str | None = None,
    hitl_action: str | None = None,
    hitl_notes: str | None = None,
    hitl_edited_text: str | None = None,
    settings: Settings | None = None,
    llm: LLMClient | None = None,
    tracer: Tracer | None = None,
    persist: bool = True,
) -> Blackboard:
    settings = settings or get_settings()
    llm = llm or get_llm(settings)
    tracer = tracer or Tracer()

    clean_goal = redact_pii(goal) if settings.enable_pii_redaction else goal
    bb = Blackboard(goal=clean_goal, customer_id=customer_id)

    with tracer.span("trajectory", agent="runtime", provider=settings.provider):
        with tracer.span("planner", agent="planner"):
            plan = make_plan(bb, enable_injection_scan=settings.enable_injection_scan)
            tracer.event("plan", agent="planner", tasks=plan.tasks)

        if plan.short_circuit is not None:
            decision, reason, flag_code = plan.short_circuit
            bb.decision = Decision(decision)
            bb.reason = reason
            bb.add_flag(flag_code, reason, "high")
            tracer.event("short_circuit", agent="planner", reason=reason, flag=flag_code)
        else:
            ctx = Context(
                llm=llm,
                tracer=tracer,
                broker=ToolBroker(),
                settings=settings,
            )
            orchestrator = Orchestrator(workers=default_workers())
            orchestrator.run(bb, BlackboardController(), ctx)
            if bb.decision == Decision.PENDING:
                bb.decision = Decision.REFUSE
                bb.reason = "trajectory ended without a grounded draft"

        _run_hitl_gate(bb, settings, tracer, hitl_action, hitl_notes, hitl_edited_text)

        tracer.event(
            "final",
            agent="runtime",
            decision=bb.decision.value,
            hitl=bb.hitl_status.value,
            hops=bb.hops,
            reflection_rounds=bb.reflection_rounds,
            customer_ready=bb.customer_ready is not None,
        )

    if persist:
        _persist(bb, tracer, settings)
    return bb


def _run_hitl_gate(
    bb: Blackboard,
    settings: Settings,
    tracer: Tracer,
    hitl_action: str | None,
    hitl_notes: str | None,
    hitl_edited_text: str | None,
) -> None:
    if not requires_hitl(bb):
        bb.hitl_status = HitlStatus.NOT_REQUIRED
        return
    action = hitl_action
    if action is None and settings.auto_approve_hitl and bb.decision == Decision.DRAFT:
        action = "approve"
        hitl_notes = hitl_notes or "auto-approved for demo/CI only"
    apply_hitl(
        bb,
        action,
        notes=hitl_notes,
        edited_text=hitl_edited_text,
        tracer=tracer,
    )


def _persist(bb: Blackboard, tracer: Tracer, settings: Settings) -> None:
    traces_dir = Path(settings.traces_dir)
    traces_dir.mkdir(parents=True, exist_ok=True)
    tracer.write_json(traces_dir / f"{bb.run_id}.trace.json")
    (traces_dir / f"{bb.run_id}.blackboard.json").write_text(
        json.dumps(bb.to_dict(), indent=2), encoding="utf-8"
    )
