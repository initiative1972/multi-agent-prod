"""Orchestrator-worker pattern.

The orchestrator owns a registry of workers and drives execution. It does not
do the work itself; it decides *what runs next* (by consulting a controller),
enforces the hop budget, traces every step, and stops when the controller says
there is nothing left to do. Workers are interchangeable and only touch the
blackboard, so new capabilities are added by registering a worker — not by
editing the control loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from multi_agent_prod.patterns.blackboard import BlackboardController
from multi_agent_prod.state import Blackboard

# A worker reads/writes the blackboard given a context object.
Worker = Callable[[Blackboard, object], None]


@dataclass
class Orchestrator:
    workers: dict[str, Worker]

    def run(self, bb: Blackboard, controller: BlackboardController, ctx: object) -> Blackboard:
        max_hops = getattr(ctx, "settings").max_hops
        tracer = getattr(ctx, "tracer")
        while bb.hops < max_hops:
            action = controller.next_action(bb)
            if action is None:
                break
            worker = self.workers.get(action)
            if worker is None:
                tracer.event("unknown_task", agent="orchestrator", task=action)
                break
            bb.tick()
            with tracer.span("worker", agent=action, task=action, hop=bb.hops):
                worker(bb, ctx)
        else:
            tracer.event("budget_exhausted", agent="orchestrator", hops=bb.hops)
        return bb
