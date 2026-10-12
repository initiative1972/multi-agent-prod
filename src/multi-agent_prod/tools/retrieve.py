"""Grounding retrieval over the synthetic policy corpus.

Deterministic token-overlap scoring (no embeddings, no network) so grounding
is reproducible in CI. The design slot for a real hybrid retriever is obvious:
swap the scoring function; the interface and the grounded-or-refuse contract
around it do not change.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from multi_agent_prod.config import get_settings
from multi_agent_prod.state import Evidence

_ID_RE = re.compile(r"\[([A-Z]+-\d+)\]")
_WORD_RE = re.compile(r"[a-z0-9]+")

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "for", "is", "are", "in", "on",
    "with", "that", "this", "it", "as", "be", "by", "at", "we", "can", "i",
    "about", "do", "does", "please", "me", "my", "you", "your", "our", "us",
    # Generic comms verbs/nouns that must not create spurious grounding.
    "write", "draft", "note", "message", "customer", "short", "saver", "savers",
    "send", "want", "need", "nudge", "program", "programme", "campaign", "copy",
    "email", "them", "their", "they", "would", "like", "some", "any", "get",
}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 2}


@lru_cache(maxsize=1)
def _load_corpus() -> tuple[dict, ...]:
    corpus_dir = Path(get_settings().corpus_dir)
    docs: list[dict] = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        first = raw.splitlines()[0] if raw.splitlines() else ""
        match = _ID_RE.search(first)
        doc_id = match.group(1) if match else path.stem
        title = first.lstrip("# ").strip()
        body = "\n".join(raw.splitlines()[1:]).strip()
        docs.append(
            {
                "id": doc_id,
                "title": title,
                "body": body,
                "tokens": _tokens(f"{title} {body}"),
            }
        )
    return tuple(docs)


def _excerpt(body: str, limit: int = 180) -> str:
    text = " ".join(body.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"


def retrieve(query: str, top_k: int | None = None) -> list[Evidence]:
    """Return up to ``top_k`` grounded Evidence items, best first.

    Score = overlapping tokens / query tokens (Jaccard-ish, bounded 0..1).
    Deterministic and order-stable.
    """
    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k
    q = _tokens(query)
    if not q:
        return []

    scored: list[Evidence] = []
    for doc in _load_corpus():
        overlap = len(q & doc["tokens"])
        if overlap == 0:
            continue
        score = round(overlap / len(q), 4)
        scored.append(
            Evidence(
                source_id=doc["id"],
                title=doc["title"],
                excerpt=_excerpt(doc["body"]),
                score=score,
            )
        )

    scored.sort(key=lambda e: (-e.score, e.source_id))
    return scored[:top_k]
