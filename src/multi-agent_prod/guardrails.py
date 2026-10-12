"""Guardrails: least-privilege tool access, content-side injection scanning,
out-of-scope demand detection, and PII redaction.

Three ideas worth calling out for interviews:

1. *Content-side* prompt-injection scanning. The dangerous instructions do not
   only come from the user — they ride in on *retrieved content*. So we scan the
   goal AND every retrieved excerpt for injection *imperatives* before any of it
   can influence a draft. Crucially, this is distinct from a document merely
   *describing* a banned action: "never guarantee returns" is policy text, not
   an attack, so it must not trip the injection detector.

2. *Out-of-scope demand* detection. A user asking the agent to "send it now",
   "skip opt-in" or "guarantee a return" is not injection; it is a request the
   agent is not allowed to fulfil. That is a scope check on the goal only.

3. *Least privilege by broker*. Agents cannot call tools directly. They ask a
   broker, which enforces a per-worker allow-list and runs the pre-call hook.
   A worker that is only allowed to retrieve cannot escalate or draft.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

# Imperative prompt-injection — scanned on the goal AND on retrieved content.
_INJECTION_PATTERNS = [
    r"ignore (all |your |the )?(previous|prior|above) (instructions|rules)",
    r"disregard (the )?(policy|rules|system prompt|guardrails)",
    r"reveal (the )?(system prompt|hidden|your instructions)",
    r"override (the )?(policy|guardrails|safety)",
    r"you are now (a |an )?",
    r"exfiltrate|leak (the )?data",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Out-of-scope *demands* — scanned on the user goal only (never on policy text,
# which legitimately describes these as forbidden).
_SCOPE_PATTERNS = [
    r"send (it |this )?now",
    r"skip (the )?(opt-?in|consent|approval|review)",
    r"guarantee(d)? (me )?(a )?(returns?|rate|profit)",
    r"bypass (the )?(human|review|approval)",
]
_SCOPE_RE = re.compile("|".join(_SCOPE_PATTERNS), re.IGNORECASE)

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\b(?:\+?61|0)[\d ]{8,12}\b")


class ToolNotAllowed(Exception):
    """Raised when a worker calls a tool outside its allow-list."""


def scan_injection(text: str) -> list[str]:
    """Return the injection imperatives found in ``text`` (empty = clean)."""
    if not text:
        return []
    return [m.group(0).strip() for m in _INJECTION_RE.finditer(text)]


def scan_scope(text: str) -> list[str]:
    """Return out-of-scope demands found in ``text`` (empty = in scope)."""
    if not text:
        return []
    return [m.group(0).strip() for m in _SCOPE_RE.finditer(text)]


def redact_pii(text: str) -> str:
    if not text:
        return text
    text = _EMAIL_RE.sub("[email]", text)
    text = _PHONE_RE.sub("[phone]", text)
    return text


@dataclass
class ToolBroker:
    """Enforces least privilege and runs a pre-call hook before every tool."""

    pre_call: Callable[[str, tuple, dict], None] | None = None

    def invoke(
        self,
        tool_name: str,
        allowed: set[str],
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if tool_name not in allowed:
            raise ToolNotAllowed(
                f"tool '{tool_name}' is not in this worker's allow-list {sorted(allowed)}"
            )
        if self.pre_call is not None:
            self.pre_call(tool_name, args, kwargs)
        return fn(*args, **kwargs)
