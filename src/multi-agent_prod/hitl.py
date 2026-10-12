"""Human-in-the-loop gate for consequential outputs.

A draft is never customer-ready on its own. If the trajectory produced a draft,
a human must approve / edit / reject it. The gate records exactly what the human
saw (draft + the evidence ids it was grounded on) so the decision is auditable.
"""

from __future__ import annotations

from multi_agent_prod.state import Blackboard, Decision, HitlStatus
from multi_agent_prod.trace import Tracer


def requires_hitl(bb: Blackboard) -> bool:
    """A human is required for anything customer-facing or escalated."""
    return bb.decision in (Decision.DRAFT, Decision.ESCALATE)


def apply_hitl(
    bb: Blackboard,
    action: str | None,
    *,
    notes: str | None = None,
    edited_text: str | None = None,
    tracer: Tracer | None = None,
) -> Blackboard:
    """Apply a human decision. ``action`` in {approve, edit, reject, None}."""
    shown = {
        "draft": bb.draft,
        "evidence_ids": [e.source_id for e in bb.evidence],
        "decision": bb.decision.value,
        "flags": [f.code for f in bb.flags],
    }
    if tracer is not None:
        tracer.event("hitl_shown", agent="hitl", **shown)

    # Escalations are already a human's call; a draft needs explicit approval.
    if bb.decision == Decision.ESCALATE:
        bb.hitl_status = HitlStatus.PENDING
        bb.hitl_notes = notes or "escalated to a human owner"
        return bb

    if action is None:
        bb.hitl_status = HitlStatus.PENDING
        return bb

    if action == "approve":
        bb.hitl_status = HitlStatus.APPROVED
        bb.customer_ready = bb.draft
    elif action == "edit":
        bb.hitl_status = HitlStatus.EDITED
        bb.customer_ready = edited_text or bb.draft
    elif action == "reject":
        bb.hitl_status = HitlStatus.REJECTED
        bb.customer_ready = None
    else:
        bb.hitl_status = HitlStatus.PENDING

    bb.hitl_notes = notes
    if tracer is not None:
        tracer.event(
            "hitl_decision",
            agent="hitl",
            action=action,
            status=bb.hitl_status.value,
        )
    return bb
