"""The one interface agents depend on."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return the model completion for a (system, user) prompt pair."""
        ...
