"""Escalation tool: hand the trajectory to a human owner."""

from __future__ import annotations


def escalate(reason: str, owner: str = "human-reviewer") -> dict:
    """Produce a structured escalation record (no side effects)."""
    return {
        "action": "escalate",
        "owner": owner,
        "reason": reason,
    }
