"""Tracing: nested spans over a whole trajectory.

Every agent step runs inside a span. Spans nest (orchestrator > worker >
tool-call > llm-call) so a run becomes a tree you can read top-down. The core
emits plain dicts; an optional exporter ships the same spans to Langfuse /
OpenTelemetry in the live layer (lazy import, never required for CI).

A ``clock`` can be injected to make durations deterministic in tests.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator


@dataclass
class Span:
    span_id: int
    parent_id: int | None
    name: str
    agent: str
    start_ms: float
    attributes: dict[str, Any] = field(default_factory=dict)
    end_ms: float | None = None

    @property
    def duration_ms(self) -> float:
        if self.end_ms is None:
            return 0.0
        return round(self.end_ms - self.start_ms, 3)

    def set(self, **attributes: Any) -> None:
        self.attributes.update(attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "agent": self.agent,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
        }


class Tracer:
    """Collects nested spans for one trajectory."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or (lambda: time.perf_counter() * 1000.0)
        self._counter = 0
        self._stack: list[int] = []
        self.spans: list[Span] = []

    @contextmanager
    def span(self, name: str, agent: str, **attributes: Any) -> Iterator[Span]:
        self._counter += 1
        span = Span(
            span_id=self._counter,
            parent_id=self._stack[-1] if self._stack else None,
            name=name,
            agent=agent,
            start_ms=self._clock(),
            attributes=dict(attributes),
        )
        self.spans.append(span)
        self._stack.append(span.span_id)
        try:
            yield span
        finally:
            span.end_ms = self._clock()
            self._stack.pop()

    def event(self, name: str, agent: str, **attributes: Any) -> Span:
        """A zero-duration marker (decisions, flags, routing)."""
        self._counter += 1
        now = self._clock()
        span = Span(
            span_id=self._counter,
            parent_id=self._stack[-1] if self._stack else None,
            name=name,
            agent=agent,
            start_ms=now,
            attributes=dict(attributes),
            end_ms=now,
        )
        self.spans.append(span)
        return span

    def to_list(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.spans]

    def write_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_list(), indent=2), encoding="utf-8")
        return p

    def export_langfuse(self, trace_name: str) -> bool:  # pragma: no cover
        """Best-effort export to Langfuse. Lazy import; never required.

        Returns True if spans were shipped, False if the SDK/credentials are
        absent. This keeps the live layer honest: tracing is designed and
        wired, but CI never depends on an external service.
        """
        try:
            from langfuse import Langfuse  # type: ignore
        except Exception:
            return False
        client = Langfuse()
        trace = client.trace(name=trace_name)
        for s in self.spans:
            trace.span(
                name=s.name,
                metadata={"agent": s.agent, **s.attributes},
            )
        client.flush()
        return True
