"""Workers: the units the orchestrator dispatches.

Each worker reads/writes only the blackboard and calls tools through the broker
(least privilege). The draft/critic step is the critic-reflection pattern made
concrete: produce a grounded draft, critique it, revise within budget, and route
to a human on any policy/safety/flag concern.
"""

from __future__ import annotations

from multi_agent_prod.agents.context import Context
from multi_agent_prod.guardrails import scan_injection
from multi_agent_prod.patterns.reflection import reflect
from multi_agent_prod.state import Blackboard, Decision
from multi_agent_prod.tools import check_contact_rules, load_customer, retrieve

_DRAFTER_SYSTEM = (
    "ROLE: drafter. Write a plain-language customer message using ONLY the "
    "cited policy evidence. Never guarantee outcomes, never apply pressure, "
    "never send. Output 'DRAFT: <text>' then 'DECISION: draft'."
)
_CRITIC_SYSTEM = (
    "ROLE: critic. Check the draft is grounded in cited policy and policy-safe, "
    "and respect any contact-rule / safety flags. Output 'VERDICT: "
    "pass|revise|escalate' then 'REASON: <text>'."
)


def _parse_tag(text: str, tag: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(tag.lower()):
            return stripped[len(tag):].strip()
    return ""


# ---- workers -----------------------------------------------------------
def retrieve_worker(bb: Blackboard, ctx: Context) -> None:
    evidence = ctx.broker.invoke(
        "retrieve", {"retrieve"}, retrieve, bb.goal, ctx.settings.retrieval_top_k
    )
    bb.write("retrieve_worker", "retrieved", True)

    if ctx.settings.enable_injection_scan:
        for item in evidence:
            hits = scan_injection(item.excerpt)
            if hits:
                bb.add_flag("SEC-INJECTION", f"in {item.source_id}: '{hits[0]}'", "high")
                ctx.tracer.event(
                    "injection_blocked", agent="guardrails", source=item.source_id
                )

    top = evidence[0].score if evidence else 0.0
    if not evidence or top < ctx.settings.grounding_threshold:
        bb.decision = Decision.REFUSE
        bb.reason = "no sufficiently grounded policy to answer; declining to invent one"
        ctx.tracer.event("grounded_or_refuse", agent="retriever", grounded=False, top_score=top)
        return

    bb.evidence = evidence
    ctx.tracer.event(
        "grounded_or_refuse", agent="retriever", grounded=True, top_score=top, n=len(evidence)
    )


def contact_check_worker(bb: Blackboard, ctx: Context) -> None:
    customer = load_customer(bb.customer_id)
    flags = check_contact_rules(customer)
    bb.flags.extend(flags)
    bb.write("contact_check_worker", "contact_checked", True)
    ctx.tracer.event("contact_rules", agent="policy", flags=[f.code for f in flags])


def _drafter(bb: Blackboard, ctx: Context) -> str:
    ids = [e.source_id for e in bb.evidence[:2]]
    user = (
        f"GOAL: {bb.goal}\n"
        f"EVIDENCE: {', '.join('[' + i + ']' for i in ids)}"
    )
    raw = ctx.llm.complete(_DRAFTER_SYSTEM, user)
    body = _parse_tag(raw, "DRAFT:") or raw.strip()
    cites = " ".join(f"[{i}]" for i in ids)
    return f"{body} {cites}".strip()


def _critic(bb: Blackboard, ctx: Context, draft: str) -> tuple[str, str]:
    flag_codes = ",".join(f.code for f in bb.flags) or "none"
    ids = ",".join(e.source_id for e in bb.evidence) or "none"
    user = f"DRAFT: {draft}\nFLAGS: {flag_codes}\nEVIDENCE_IDS: {ids}"
    raw = ctx.llm.complete(_CRITIC_SYSTEM, user)
    verdict = (_parse_tag(raw, "VERDICT:") or "revise").lower()
    reason = _parse_tag(raw, "REASON:") or ""
    return verdict, reason


def draft_review_worker(bb: Blackboard, ctx: Context) -> None:
    if bb.decision in (Decision.REFUSE, Decision.ESCALATE):
        return

    result = reflect(
        produce=lambda: _drafter(bb, ctx),
        critique=lambda draft: _critic(bb, ctx, draft),
        max_rounds=ctx.settings.max_reflection_rounds,
        tracer=ctx.tracer,
    )
    bb.reflection_rounds = result.rounds
    bb.draft = result.output

    if result.verdict == "pass":
        bb.decision = Decision.DRAFT
        bb.reason = result.reason
    elif result.verdict == "escalate":
        bb.decision = Decision.ESCALATE
        bb.reason = result.reason
    else:  # revise budget exhausted without convergence
        bb.decision = Decision.ESCALATE
        bb.reason = "critic did not converge within the reflection budget; routing to a human"

    ctx.tracer.event(
        "draft_review",
        agent="critic",
        verdict=result.verdict,
        rounds=result.rounds,
        decision=bb.decision.value,
    )


def default_workers() -> dict:
    return {
        "retrieve": retrieve_worker,
        "contact_check": contact_check_worker,
        "draft_review": draft_review_worker,
    }
