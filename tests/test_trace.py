from __future__ import annotations

from multi_agent_prod.trace import Tracer


def _counter_clock():
    state = {"t": 0.0}

    def clock() -> float:
        state["t"] += 1.0
        return state["t"]

    return clock


def test_spans_nest_with_parent_ids():
    tracer = Tracer(clock=_counter_clock())
    with tracer.span("outer", agent="runtime"):
        with tracer.span("inner", agent="worker"):
            tracer.event("marker", agent="worker")
    names = {s.span_id: s for s in tracer.spans}
    outer = next(s for s in tracer.spans if s.name == "outer")
    inner = next(s for s in tracer.spans if s.name == "inner")
    marker = next(s for s in tracer.spans if s.name == "marker")
    assert outer.parent_id is None
    assert inner.parent_id == outer.span_id
    assert marker.parent_id == inner.span_id
    assert names  # sanity


def test_durations_are_deterministic_with_injected_clock():
    tracer = Tracer(clock=_counter_clock())
    with tracer.span("a", agent="x"):
        pass
    span = tracer.spans[0]
    assert span.duration_ms == 1.0


def test_write_json(tmp_path):
    tracer = Tracer(clock=_counter_clock())
    with tracer.span("a", agent="x"):
        pass
    path = tracer.write_json(tmp_path / "t.json")
    assert path.exists()
    assert '"name": "a"' in path.read_text(encoding="utf-8")
