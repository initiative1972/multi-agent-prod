"""LLM layer: deterministic mock (default) + self-hosted OpenAI-compatible."""

from __future__ import annotations

from multi_agent_prod.config import Settings, get_settings
from multi_agent_prod.llm.base import LLMClient
from multi_agent_prod.llm.mock import DeterministicLLM


def get_llm(settings: Settings | None = None) -> LLMClient:
    """Return the configured client. Falls back to the mock when the live
    backend is not fully configured, so the default path is always runnable.
    """
    settings = settings or get_settings()
    if settings.provider == "openai_compat" and settings.base_url:
        from multi_agent_prod.llm.openai_compat import OpenAICompatLLM

        return OpenAICompatLLM(settings)
    return DeterministicLLM()


__all__ = ["LLMClient", "DeterministicLLM", "get_llm"]
