from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from aibrief.utils.validation import strip_control_chars

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)?")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "are", "is", "of", "to", "in", "on",
    "a", "an", "by", "as", "or", "ai", "llm", "new", "adds", "need", "needs", "systems",
}


def stable_id(*parts: str, prefix: str = "sig") -> str:
    raw = "|".join(strip_control_chars(part) for part in parts).encode("utf-8", errors="ignore")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: str | None) -> str:
    value = strip_control_chars(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    if re.fullmatch(r"[a-z0-9\s_-]+", keyword.lower()):
        return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def count_keywords(text: str, weights: dict[str, int]) -> int:
    """Score weighted keywords once each using token boundaries where possible."""
    clean = clean_text(text).lower()
    total = 0
    for key, weight in weights.items():
        if keyword_pattern(key).search(clean):
            total += int(weight)
    return total


def classify_topic(text: str) -> str:
    t = clean_text(text).lower()
    rules = [
        ("Security", ["security", "vulnerability", "risk", "audit", "soc", "threat"]),
        ("RAG", ["rag", "retrieval", "vector", "embedding", "index"]),
        ("Data", ["database", "analytics", "warehouse", "sql", "pipeline"]),
        ("Models", ["llm", "model", "benchmark", "multimodal", "reasoning"]),
        ("Open Source", ["github", "open source", "release", "repo"]),
        ("Agents", ["agent", "agents", "workflow", "tool", "planner"]),
    ]
    for topic, needles in rules:
        if any(keyword_pattern(n).search(t) for n in needles):
            return topic
    return "AI Intelligence"


def text_signature(text: str, limit: int = 5) -> str:
    """Build a short deterministic signature for lightweight clustering."""
    words = [w.lower() for w in _WORD_RE.findall(clean_text(text))]
    selected: list[str] = []
    for word in words:
        if word in _STOPWORDS or len(word) < 3 or word in selected:
            continue
        selected.append(word)
        if len(selected) >= limit:
            break
    return "-".join(selected) or stable_id(text)[:12]


def summarize(text: str, max_chars: int = 260) -> str:
    text = clean_text(text)
    max_chars = max(20, int(max_chars))
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def ltr_isolate(text: str) -> str:
    """Keep embedded English titles readable inside Arabic RTL text."""
    return f"\u2066{clean_text(text)}\u2069"


def arabic_brief(title: str, score: int, topic: str) -> str:
    # Template-based Arabic brief; avoids fake translation claims.
    safe_title = ltr_isolate(title)
    safe_topic = clean_text(topic)
    return (
        f"إشارة ضمن مجال {safe_topic}. العنوان: {safe_title}. "
        f"درجة الأهمية {int(score)}/100. الإجراء المقترح: مراجعة المصدر، تحديد الأثر، ثم إضافته إلى موجز الإدارة إذا تجاوز العتبة."
    )
