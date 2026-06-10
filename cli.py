from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from aibrief.utils.validation import safe_url, strip_control_chars

VALID_STATUSES = {"pending", "scored", "verified", "enriched", "held"}
MAX_FIELD_CHARS = 8_000
MAX_LIST_ITEMS = 25


def _bounded(value: str | None, limit: int = MAX_FIELD_CHARS) -> str:
    clean = strip_control_chars(value)
    return clean[:limit]


@dataclass
class Signal:
    id: str
    source: str
    title: str
    content: str
    url: str
    topic: str
    createdAt: str
    score: int = 0
    status: str = "pending"
    confidenceScore: float = 0.0
    verificationReason: str = ""
    opportunity: str = ""
    skepticism: str = ""
    riskNotes: str = ""
    threadEn: str = ""
    threadAr: str = ""
    relatedIds: list[str] = field(default_factory=list)

    engagement: int = 0
    sourceRank: int = 0
    clusterId: str = ""
    bestTake: str = ""
    timeWindow: str = "last 30 days"
    evidenceCount: int = 1
    evidenceUrls: list[str] = field(default_factory=list)
    riskFlags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = _bounded(self.id, 120)
        self.source = _bounded(self.source, 80).lower() or "seed"
        self.title = _bounded(self.title, 500) or "Untitled signal"
        self.content = _bounded(self.content)
        self.url = safe_url(self.url)
        self.topic = _bounded(self.topic, 160) or "AI Intelligence"
        self.createdAt = _bounded(self.createdAt, 80)
        self.status = self.status if self.status in VALID_STATUSES else "pending"
        self.score = max(0, min(100, int(self.score or 0)))
        self.confidenceScore = max(0.0, min(1.0, float(self.confidenceScore or 0.0)))
        self.engagement = max(0, int(self.engagement or 0))
        self.sourceRank = max(0, int(self.sourceRank or 0))
        self.evidenceCount = max(1, int(self.evidenceCount or 1))
        self.evidenceUrls = [url for url in [safe_url(u) for u in self.evidenceUrls[:MAX_LIST_ITEMS]] if url]
        if self.url and self.url not in self.evidenceUrls:
            self.evidenceUrls.append(self.url)
        self.relatedIds = [_bounded(x, 120) for x in self.relatedIds[:MAX_LIST_ITEMS] if _bounded(x, 120)]
        self.riskFlags = [_bounded(x, 80) for x in self.riskFlags[:MAX_LIST_ITEMS] if _bounded(x, 80)]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AibriefState:
    run_id: str
    topic: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signals: list[Signal] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    query_plan: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)

    def add_error(self, component: str, message: str) -> None:
        self.errors.append({"component": _bounded(component, 120), "message": _bounded(message, 1000)})

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "topic": self.topic,
            "started_at": self.started_at,
            "query_plan": self.query_plan,
            "signals": [signal.to_dict() for signal in self.signals],
            "decisions": self.decisions,
            "metrics": self.metrics,
            "errors": self.errors,
        }
