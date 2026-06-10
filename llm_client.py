from __future__ import annotations

from aibrief.graph.state import Signal
from aibrief.utils.text import stable_id, utc_now
from aibrief.utils.validation import validate_limit

COMMUNITY_ITEMS = [
    {
        "source": "reddit",
        "title": "Practitioners say agent systems need explicit checkpoint recovery",
        "content": "A community thread says long-running agents fail less when every tool phase writes resumable checkpoints and a visible decision log.",
        "url": "https://reddit.com/",
        "engagement": 1840,
        "bestTake": "If the agent cannot resume, it is not a workflow. It is a demo.",
    },
    {
        "source": "x_influencer",
        "title": "AI builders are moving from prompt tricks to operating systems for agents",
        "content": "Influencer discussion points toward durable skills, shared memory, and task routers rather than one-off prompts.",
        "url": "https://x.com/",
        "engagement": 12600,
        "bestTake": "Prompts are becoming config files for teams of agents.",
    },
    {
        "source": "youtube",
        "title": "Developer walkthrough shows agent review loops before publishing output",
        "content": "A technical video explains a pipeline with researcher, critic, risk reviewer, and final editor roles before a brief is published.",
        "url": "https://youtube.com/",
        "engagement": 83000,
        "bestTake": "The critic agent is where toy demos become operational systems.",
    },
    {
        "source": "hackernews",
        "title": "HN debate: agent memory improves productivity but creates audit risk",
        "content": "Developers argue for scoped memory, immutable logs, and reproducible runs when agents automate engineering work.",
        "url": "https://news.ycombinator.com/",
        "engagement": 912,
        "bestTake": "Memory without provenance is just a bug with confidence.",
    },
    {
        "source": "github",
        "title": "Open source skill framework adds command contracts and test fixtures",
        "content": "A repository introduces skill-level contracts, fixtures, and regression tests so agents follow the intended workflow instead of improvising.",
        "url": "https://github.com/",
        "engagement": 25800,
        "bestTake": "The skill file is the product spec and the guardrail.",
    },
    {
        "source": "polymarket",
        "title": "Prediction markets are used as confidence signals for AI industry events",
        "content": "Market odds provide a separate signal stream that can support or challenge social and editorial narratives.",
        "url": "https://polymarket.com/",
        "engagement": 66000,
        "bestTake": "Money-weighted disagreement is a useful anti-hype input.",
    },
    {
        "source": "web",
        "title": "Enterprise AI coverage shifts toward governance and cost controls",
        "content": "Recent web coverage focuses on model spend, evaluation, approval gates, and data controls for production agent systems.",
        "url": "https://example.com/ai-governance",
        "engagement": 420,
        "bestTake": "The budget line is becoming the architecture diagram.",
    },
    {
        "source": "rss",
        "title": "Arabic AI publishing teams need bilingual workflow validation",
        "content": "Content pipelines need English and Arabic brief generation, RTL checks, terminology review, and source traceability.",
        "url": "https://example.com/arabic-ai-workflow",
        "engagement": 380,
        "bestTake": "Bilingual output is not translation. It is editorial operations.",
    },
]


def load_last30days_signals(topic: str = "ai-agents", limit: int = 10) -> list[Signal]:
    """Seeded Last30Days-style community feed.

    This keeps Aibrief runnable without API keys while preserving the architecture:
    many social/news/dev sources, engagement-aware ranking, and sourced briefs.
    """
    safe_limit = validate_limit(limit)
    signals: list[Signal] = []
    for rank, item in enumerate(COMMUNITY_ITEMS[:safe_limit], start=1):
        signals.append(
            Signal(
                id=stable_id("last30days", item["source"], item["title"]),
                source=item["source"],
                title=item["title"],
                content=item["content"],
                url=item["url"],
                topic=topic,
                createdAt=utc_now(),
                engagement=int(item["engagement"]),
                sourceRank=rank,
                bestTake=item["bestTake"],
                timeWindow="last 30 days",
                evidenceCount=1,
                evidenceUrls=[item["url"]],
            )
        )
    return signals
