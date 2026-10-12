"""Blackboard: the single shared memory every agent reads from and writes to.

This is the *blackboard pattern*. Agents never message each other directly;
they contribute to (and consume from) a versioned shared workspace. That makes
the whole run observable: every write is attributed to a source and timestamped,
so a trajectory can be reconstructed and evaluated after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class Decision(str, Enum):
    PENDING = "pending"
    DRAFT = "draft"          # grounded answer produced; needs human sign-off
    REFUSE = "refuse"        # nothing to ground on; declined
    ESCALATE = "escalate"    # routed to a human (policy/safety/scope)


class HitlStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


@dataclass
class Evidence:
    source_id: str
    title: str
    excerpt: str
    score: float


@dataclass
class Flag:
    code: str          # e.g. CR-OPT, CR-FREQ, CR-VULN, SEC-INJECTION
    detail: str
    severity: str = "medium"   # low | medium | high


@dataclass
class Contribution:
    source: str
    key: str
    version: int
    ts: str


@dataclass
class Blackboard:
    """Versioned shared workspace for a single trajectory."""

    goal: str
    customer_id: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex[:12])

    entries: dict[str, Any] = field(default_factory=dict)
    history: list[Contribution] = field(default_factory=list)

    evidence: list[Evidence] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    draft: str | None = None
    customer_ready: str | None = None

    decision: Decision = Decision.PENDING
    reason: str | None = None
    hitl_status: HitlStatus = HitlStatus.NOT_REQUIRED
    hitl_notes: str | None = None

    hops: int = 0
    reflection_rounds: int = 0

    disclaimer: str = (
        "DEMO ONLY - synthetic data. Not a send, not a decision about any "
        "real person. A human must approve before anything is customer-ready."
    )

    # ---- blackboard protocol -------------------------------------------
    def write(self, source: str, key: str, value: Any) -> int:
        """Record an attributed, versioned write and return the new version."""
        version = sum(1 for c in self.history if c.key == key) + 1
        self.entries[key] = value
        self.history.append(
            Contribution(
                source=source,
                key=key,
                version=version,
                ts=datetime.now(timezone.utc).isoformat(),
            )
        )
        return version

    def read(self, key: str, default: Any = None) -> Any:
        return self.entries.get(key, default)

    def add_flag(self, code: str, detail: str, severity: str = "medium") -> None:
        self.flags.append(Flag(code=code, detail=detail, severity=severity))

    def has_flag(self, code: str) -> bool:
        return any(f.code == code for f in self.flags)

    def high_severity_flags(self) -> list[Flag]:
        return [f for f in self.flags if f.severity == "high"]

    def tick(self) -> int:
        self.hops += 1
        return self.hops

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "customer_id": self.customer_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "hitl_status": self.hitl_status.value,
            "hitl_notes": self.hitl_notes,
            "hops": self.hops,
            "reflection_rounds": self.reflection_rounds,
            "evidence": [vars(e) for e in self.evidence],
            "flags": [vars(f) for f in self.flags],
            "draft": self.draft,
            "customer_ready": self.customer_ready,
            "history": [vars(c) for c in self.history],
            "disclaimer": self.disclaimer,
        }
