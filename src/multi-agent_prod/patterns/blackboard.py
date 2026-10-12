"""Blackboard pattern: control flow is driven by the shared memory, not by a
fixed script.

The controller inspects the blackboard and decides what should happen next. If
retrieval already refused, there is nothing left to do. If there is a customer
but contact rules have not been checked, check them. If there is grounding but
no draft, draft-and-review. This makes the trajectory adaptive and keeps the
"what next?" decision in one small, testable place.
"""

from __future__ import annotations

from multi_agent_prod.state import Blackboard, Decision


class BlackboardController:
    """Chooses the next worker to run by reading the blackboard state."""

    def next_action(self, bb: Blackboard) -> str | None:
        # A terminal decision ends the agenda.
        if bb.decision in (Decision.REFUSE, Decision.ESCALATE):
            return None
        if not bb.read("retrieved"):
            return "retrieve"
        if bb.customer_id and not bb.read("contact_checked"):
            return "contact_check"
        if bb.draft is None:
            return "draft_review"
        return None

    def declared_agenda(self, bb: Blackboard) -> list[str]:
        """A dry projection of the agenda for the trace (no side effects)."""
        agenda = ["retrieve"]
        if bb.customer_id:
            agenda.append("contact_check")
        agenda.append("draft_review")
        return agenda
