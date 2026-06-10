from __future__ import annotations

from aibrief.graph.state import Signal
from aibrief.utils.text import stable_id, utc_now
from aibrief.utils.validation import validate_limit

SEED_ITEMS = [
    {
        "source": "arxiv",
        "title": "Agent workflow benchmarks expose planning failures in long-running tasks",
        "content": "A research summary reports that AI agents need checkpointing, memory, evaluation, and recovery when tasks span multiple steps.",
        "url": "https://arxiv.org/",
    },
    {
        "source": "github",
        "title": "Open-source RAG toolkit adds hybrid ranking and evaluation traces",
        "content": "The project adds ranker comparison, retrieval diagnostics, and dataset-level evaluation reports for production RAG systems.",
        "url": "https://github.com/",
    },
    {
        "source": "rss",
        "title": "Enterprise AI teams shift from demos to governed agent operations",
        "content": "Organizations are moving from isolated LLM prompts toward monitored workflows, cost control, and approval steps.",
        "url": "https://example.com/enterprise-ai",
    },
    {
        "source": "hackernews",
        "title": "Developers debate whether agents need persistent memory by default",
        "content": "Discussion focuses on memory corruption, audit trails, reproducibility, and sandboxed execution.",
        "url": "https://news.ycombinator.com/",
    },
    {
        "source": "x_influencer",
        "title": "New agent pattern: reviewer agents before publisher agents",
        "content": "A common production pattern places critique, risk review, and final approval before any public output.",
        "url": "https://x.com/",
    },
    {
        "source": "rss",
        "title": "Arabic AI content pipelines need RTL validation and bilingual quality checks",
        "content": "Bilingual publishing systems require direction control, terminology consistency, and review workflows.",
        "url": "https://example.com/arabic-ai",
    },
]


def load_seed_signals(topic: str = "ai-agents", limit: int = 10) -> list[Signal]:
    safe_limit = validate_limit(limit)
    signals: list[Signal] = []
    for item in SEED_ITEMS[:safe_limit]:
        signals.append(
            Signal(
                id=stable_id("seed", item["source"], item["title"]),
                source=item["source"],
                title=item["title"],
                content=item["content"],
                url=item["url"],
                topic=topic,
                createdAt=utc_now(),
                evidenceUrls=[item["url"]],
            )
        )
    return signals
