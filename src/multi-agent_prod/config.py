"""Runtime configuration. Offline + deterministic by default.

Everything is overridable by environment variable (prefix ``MAP_``) so the
same code path serves CI (mock model) and a live self-hosted backend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CORPUS_DIR = BASE_DIR / "data" / "corpus"
CUSTOMERS_FILE = BASE_DIR / "data" / "customers.json"
TRACES_DIR = BASE_DIR / "traces"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    """Immutable-ish settings bag (plain stdlib, no third-party deps)."""

    # Model provider: "mock" (deterministic, default) or "openai_compat".
    provider: str = "mock"

    # Self-hosted OpenAI-compatible endpoint (e.g. vLLM / TGI). Live layer only.
    base_url: str | None = None
    api_key: str | None = None
    model: str = "local-model"
    request_timeout_s: float = 60.0

    # Trajectory budgets / guardrails.
    max_hops: int = 8
    max_reflection_rounds: int = 2
    retrieval_top_k: int = 3
    grounding_threshold: float = 0.12
    enable_pii_redaction: bool = True
    enable_injection_scan: bool = True

    # Human-in-the-loop.
    auto_approve_hitl: bool = False  # CI/demo convenience only; never in prod.

    # Paths.
    corpus_dir: Path = CORPUS_DIR
    customers_file: Path = CUSTOMERS_FILE
    traces_dir: Path = TRACES_DIR


def get_settings() -> Settings:
    """Build settings from defaults, overlaid with ``MAP_*`` env vars."""

    s = Settings(
        provider=os.getenv("MAP_PROVIDER", "mock"),
        base_url=os.getenv("MAP_BASE_URL"),
        api_key=os.getenv("MAP_API_KEY"),
        model=os.getenv("MAP_MODEL", "local-model"),
        max_hops=_env_int("MAP_MAX_HOPS", 8),
        max_reflection_rounds=_env_int("MAP_MAX_REFLECTION_ROUNDS", 2),
        retrieval_top_k=_env_int("MAP_RETRIEVAL_TOP_K", 3),
        enable_pii_redaction=_env_bool("MAP_PII_REDACTION", True),
        enable_injection_scan=_env_bool("MAP_INJECTION_SCAN", True),
        auto_approve_hitl=_env_bool("MAP_AUTO_APPROVE_HITL", False),
    )
    s.traces_dir.mkdir(parents=True, exist_ok=True)
    return s
