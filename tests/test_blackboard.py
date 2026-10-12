from __future__ import annotations

from multi_agent_prod.state import Blackboard, Decision


def test_versioned_writes_are_attributed():
    bb = Blackboard(goal="hi")
    assert bb.write("a", "k", 1) == 1
    assert bb.write("b", "k", 2) == 2
    assert bb.read("k") == 2
    assert [c.source for c in bb.history] == ["a", "b"]
    assert [c.version for c in bb.history] == [1, 2]


def test_flags_and_severity():
    bb = Blackboard(goal="hi")
    bb.add_flag("CR-OPT", "opted out", "high")
    bb.add_flag("CR-FREQ", "cap", "medium")
    assert bb.has_flag("CR-OPT")
    assert not bb.has_flag("SEC-INJECTION")
    assert [f.code for f in bb.high_severity_flags()] == ["CR-OPT"]


def test_to_dict_roundtrips_core_fields():
    bb = Blackboard(goal="hi", customer_id="RIVER001")
    bb.decision = Decision.DRAFT
    bb.tick()
    d = bb.to_dict()
    assert d["goal"] == "hi"
    assert d["customer_id"] == "RIVER001"
    assert d["decision"] == "draft"
    assert d["hops"] == 1
