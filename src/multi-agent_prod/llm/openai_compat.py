"""Self-hosted backend client (OpenAI-compatible: vLLM / TGI).

This is the *live layer*. It is intentionally thin and lazy-imports ``httpx``
so the core, tests and CI never need it. Point ``MAP_BASE_URL`` at your own
vLLM / TGI server (see sibling repo ``llm-serving-bench`` for how to stand one
up and size it) and set ``MAP_PROVIDER=openai_compat``.

    MAP_PROVIDER=openai_compat
    MAP_BASE_URL=http://localhost:8000/v1
    MAP_MODEL=meta-llama/Llama-3.1-8B-Instruct
    MAP_API_KEY=not-needed-for-local   # most self-hosted servers ignore this

Honesty note: the trajectories, patterns and evals in this repo were designed
and verified against the deterministic mock. Running them against a live
self-hosted model is a configuration change, not a code change — but numbers
produced that way depend on your hardware and weights.
"""

from __future__ import annotations

from multi_agent_prod.config import Settings


class OpenAICompatLLM:
    def __init__(self, settings: Settings) -> None:
        if not settings.base_url:
            raise ValueError("MAP_BASE_URL is required for provider=openai_compat")
        self.settings = settings
        self.name = f"openai_compat:{settings.model}"

    def complete(self, system: str, user: str) -> str:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - live layer only
            raise RuntimeError(
                "Install the live extra: pip install -r requirements-live.txt"
            ) from exc

        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        resp = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.settings.request_timeout_s,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"] or ""
