"""The three named multi-agent patterns, as separable building blocks."""

from __future__ import annotations

from multi_agent_prod.patterns.blackboard import BlackboardController
from multi_agent_prod.patterns.orchestrator import Orchestrator
from multi_agent_prod.patterns.reflection import ReflectionResult, reflect

__all__ = ["Orchestrator", "BlackboardController", "reflect", "ReflectionResult"]
