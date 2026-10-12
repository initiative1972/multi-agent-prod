from __future__ import annotations

from multi_agent_prod.hitl import apply_hitl, requires_hitl
from multi_agent_prod.state import Blackboard, Decision, HitlStatus


def _draft_bb():
    bb = Blackboard(goal="g")
    bb.draft = "a grounded draft [COMMS-01]"
    bb.decision = Decision.DRAFT
    return bb


def test_requires_hitl_for_draft_and_escalate():
    bb = _draft_bb()
    assert requires_hitl(bb)
    bb.decision = Decision.ESCALATE
    assert requires_hitl(bb)
    bb.decision = Decision.REFUSE
    assert not requires_hitl(bb)


def test_approve_makes_customer_ready():
    bb = _draft_bb()
    apply_hitl(bb, "approve")
    assert bb.hitl_status == HitlStatus.APPROVED
    assert bb.customer_ready == bb.draft


def test_reject_blocks_customer_ready():
    bb = _draft_bb()
    apply_hitl(bb, "reject")
    assert bb.hitl_status == HitlStatus.REJECTED
    assert bb.customer_ready is None


def test_edit_uses_edited_text():
    bb = _draft_bb()
    apply_hitl(bb, "edit", edited_text="human-edited copy")
    assert bb.hitl_status == HitlStatus.EDITED
    assert bb.customer_ready == "human-edited copy"


def test_escalate_is_pending_not_sendable():
    bb = _draft_bb()
    bb.decision = Decision.ESCALATE
    apply_hitl(bb, "approve")  # even "approve" cannot send an escalation
    assert bb.hitl_status == HitlStatus.PENDING
    assert bb.customer_ready is None
