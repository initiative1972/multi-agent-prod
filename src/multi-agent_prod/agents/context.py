"""Execution context passed to every worker (keeps worker signatures uniform)."""

from __future__ import annotations

from dataclasses import dataclass

from multi_agent_prod.config import Settings
from multi_agent_prod.guardrails import ToolBroker
from multi_agent_prod.llm.base import LLMClient
from multi_agent_prod.trace import Tracer


@dataclass
class Context:
    llm: LLMClient
    tracer: Tracer
    broker: ToolBroker
    settings: Settings
