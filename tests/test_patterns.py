from __future__ import annotations

from types import SimpleNamespace

from multi_agent_prod.config import get_settings
from multi_agent_prod.patterns import BlackboardController, Orchestrator, reflect
from multi_agent_prod.state import Blackboard, Decision
from multi_agent_prod.trace import Tracer


# ---- reflection -------------------------------------------------------
def test_reflection_revises_then_passes():
    calls = {"n": 0}

    def produce():
        calls["n"] += 1
        return f"v{calls['n']}"

    def critique(draft):
        return ("pass", "ok") if draft.endswith("2") else ("revise", "again")

    res = reflect(produce, critique, max_rounds=3)
    assert res.rounds == 2
    assert res.verdict == "pass"


def test_reflection_stops_on_escalate():
    res = reflect(lambda: "x", lambda d: ("escalate", "nope"), max_rounds=5)
    assert res.rounds == 1
    assert res.verdict == "escalate"


def test_reflection_respects_round_budget():
    res = reflect(lambda: "x", lambda d: ("revise", "again"), max_rounds=2)
    assert res.rounds == 2
    assert res.verdict == "revise"


# ---- blackboard controller -------------------------------------------
def test_controller_agenda_order():
    ctrl = BlackboardController()
    bb = Blackboard(goal="g", customer_id="RIVER001")
    assert ctrl.next_action(bb) == "retrieve"
    bb.write("w", "retrieved", True)
    assert ctrl.next_action(bb) == "contact_check"
    bb.write("w", "contact_checked", True)
    assert ctrl.next_action(bb) == "draft_review"
    bb.draft = "done"
    assert ctrl.next_action(bb) is None


def test_controller_stops_on_terminal_decision():
    ctrl = BlackboardController()
    bb = Blackboard(goal="g")
    bb.decision = Decision.REFUSE
    assert ctrl.next_action(bb) is None


# ---- orchestrator -----------------------------------------------------
def test_orchestrator_dispatches_in_agenda_order():
    order = []

    def retrieve_w(bb, ctx):
        order.append("retrieve")
        bb.write("w", "retrieved", True)

    def contact_w(bb, ctx):
        order.append("contact")
        bb.write("w", "contact_checked", True)

    def draft_w(bb, ctx):
        order.append("draft")
        bb.draft = "d"
        bb.decision = Decision.DRAFT

    workers = {"retrieve": retrieve_w, "contact_check": contact_w, "draft_review": draft_w}
    ctx = SimpleNamespace(tracer=Tracer(), settings=get_settings())
    bb = Blackboard(goal="g", customer_id="RIVER001")
    Orchestrator(workers).run(bb, BlackboardController(), ctx)
    assert order == ["retrieve", "contact", "draft"]
    assert bb.hops == 3


def test_orchestrator_respects_hop_budget():
    def loop_w(bb, ctx):
        bb.write("w", "noop", bb.hops)  # never satisfies the controller

    # controller that always wants to retrieve -> would loop without a budget
    class AlwaysRetrieve(BlackboardController):
        def next_action(self, bb):
            return "retrieve"

    ctx = SimpleNamespace(tracer=Tracer(), settings=get_settings())
    bb = Blackboard(goal="g")
    Orchestrator({"retrieve": loop_w}).run(bb, AlwaysRetrieve(), ctx)
    assert bb.hops == ctx.settings.max_hops
