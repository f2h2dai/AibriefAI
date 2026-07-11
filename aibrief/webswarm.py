from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterable


DEFAULT_MAX_QUERY_TERMS = 28
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-]*", re.IGNORECASE)


@dataclass(frozen=True)
class SearchNode:
    id: str
    objective: str
    mode: str
    depth: int
    query_terms: tuple[str, ...] = ()
    evidence_terms: tuple[str, ...] = ()
    reuse_key: str = ""
    children: tuple["SearchNode", ...] = field(default_factory=tuple)

    def walk(self) -> Iterable["SearchNode"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "mode": self.mode,
            "depth": self.depth,
            "query_terms": list(self.query_terms),
            "evidence_terms": list(self.evidence_terms),
            "reuse_key": self.reuse_key,
            "children": [child.to_dict() for child in self.children],
        }


def truthy(value, default: bool = True) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if not normalized:
        return default
    return normalized not in {"0", "false", "no", "off"}


def safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", str(term or "").strip().strip('"')).lower()


def dedupe_terms(terms: Iterable[str]) -> list[str]:
    deduped = []
    seen = set()
    for term in terms:
        cleaned = re.sub(r"\s+", " ", str(term or "").strip())
        key = normalize_term(cleaned)
        if not cleaned or key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped


def quoted(term: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(term or "").strip().strip('"'))
    if not cleaned:
        return ""
    if re.search(r"\s", cleaned) or "-" in cleaned:
        return f'"{cleaned}"'
    return cleaned


def tokenize(text: str) -> set[str]:
    return {match.group(0).lower() for match in TOKEN_RE.finditer(text or "")}


def probe_web_organization(task: str) -> dict:
    terms = tokenize(task)
    modes = ["x_intel"]
    if terms & {"war", "military", "defense", "defence", "pentagon", "maven", "grok", "iran"}:
        modes.append("defense_ai")
    if terms & {"satellite", "geospatial", "mizarvision", "imagery"}:
        modes.append("geospatial_ai")
    if terms & {"openai", "anthropic", "gemini", "grok", "xai", "agents"}:
        modes.append("frontier_ai")
    if terms & {"news", "report", "confirmed", "corroboration", "source"}:
        modes.append("public_corroboration")
    return {
        "task_terms": sorted(terms),
        "modes": list(dict.fromkeys(modes)),
        "needs_recursive_depth": len(modes) > 1,
    }


def build_ai_brief_webswarm_plan(
    objective: str = "Find useful public X intel about AI use in war, defense, targeting, and strategic AI operations.",
    *,
    source_focus: str = "x",
    max_depth: int = 2,
) -> SearchNode:
    probe = probe_web_organization(objective)
    depth = max(1, min(max_depth, 3))

    x_children = (
        SearchNode(
            id="grok_project_maven",
            objective="Find public X posts linking Grok, Grok Gov, Project Maven, Pentagon, Iran, targeting, missiles, or munitions.",
            mode="x_intel",
            depth=2,
            query_terms=(
                "Grok AI",
                "Grok Gov",
                "Grok Gov Model",
                "Project Maven",
                "Maven intelligent system",
                "Operation Epic Fury",
                "2,000 targets",
                "2000 targets",
                "96 hours",
                "Pentagon AI targeting",
            ),
            evidence_terms=("Grok", "Project Maven", "Pentagon", "Iran", "targeting", "munitions", "missiles"),
            reuse_key="public-x-ai-war",
        ),
        SearchNode(
            id="mizarvision_geoint",
            objective="Find public X posts about AI-tagged satellite imagery, geospatial intelligence, and military asset mapping.",
            mode="x_intel",
            depth=2,
            query_terms=(
                "MizarVision",
                "Meentropy",
                "AI-tagged satellite",
                "AI tagged satellite",
                "commercial satellite imagery",
                "geospatial intelligence",
                "real-time military assets",
                "Prince Sultan Air Base",
                "stealth fighters",
                "warships",
            ),
            evidence_terms=("MizarVision", "satellite imagery", "geospatial", "military assets", "air base"),
            reuse_key="public-x-ai-war",
        ),
        SearchNode(
            id="autonomous_targeting",
            objective="Find public X posts about autonomous targeting, AI kill chains, drones, weapons, and battlefield deployment.",
            mode="x_intel",
            depth=2,
            query_terms=(
                "AI target selection",
                "AI targeting",
                "autonomous targeting",
                "AI kill chain",
                "battlefield AI",
                "defense AI",
                "military AI",
                "autonomous weapons",
                "AI weapons",
                "DoD AI",
            ),
            evidence_terms=("targeting", "kill chain", "battlefield", "weapons", "DoD", "defense"),
            reuse_key="public-x-ai-war",
        ),
        SearchNode(
            id="arabic_ai_war_intel",
            objective="Find Arabic public X posts about AI, Grok, Pentagon, Iran, military targeting, and drones.",
            mode="x_intel",
            depth=2,
            query_terms=(
                "الذكاء الاصطناعي",
                "ذكاء اصطناعي",
                "غروك",
                "البنتاغون",
                "إيران",
                "استهداف",
                "صواريخ",
                "أهداف عسكرية",
                "طائرات مسيرة",
            ),
            evidence_terms=("غروك", "البنتاغون", "إيران", "استهداف", "صواريخ"),
            reuse_key="public-x-ai-war",
        ),
    )
    if depth < 2:
        x_children = ()

    x_node = SearchNode(
        id="x_intel",
        objective="Collect useful public X posts first; do not wait for model classification before publishing relevant public X intel to the website.",
        mode="x_intel",
        depth=1,
        query_terms=(
            "Grok AI",
            "Project Maven",
            "AI targeting",
            "military AI",
            "defense AI",
            "Pentagon AI",
            "MizarVision",
            "الذكاء الاصطناعي",
            "غروك",
            "البنتاغون",
            "إيران",
        ),
        evidence_terms=("x.com", "twitter.com", "public post", "source URL", "AI", "military"),
        reuse_key="public-x-ai-war",
        children=x_children,
    )

    corroboration_node = SearchNode(
        id="public_corroboration",
        objective="Use public news/RSS only as corroborating expansion when direct X collection is empty or thin.",
        mode="public_corroboration",
        depth=1,
        query_terms=(
            "Grok AI Pentagon Iran",
            "Grok Gov Model Project Maven",
            "MizarVision AI satellite Iran",
            "AI targeting Pentagon",
            "military AI Project Maven",
        ),
        evidence_terms=("public report", "source", "official statement", "published_at"),
        reuse_key="public-rss-corroboration",
    )

    children = [x_node]
    if source_focus.strip().lower() not in {"x", "twitter"} or "public_corroboration" in probe["modes"]:
        children.append(corroboration_node)
    elif source_focus.strip().lower() in {"x", "twitter"}:
        children.append(corroboration_node)

    return SearchNode(
        id="aibrief_commander",
        objective=objective,
        mode="recursive_delegation",
        depth=0,
        query_terms=(),
        evidence_terms=("objective", "search mode", "evidence", "results"),
        reuse_key="aibrief-webswarm",
        children=tuple(children),
    )


def webswarm_enabled(env: dict[str, str]) -> bool:
    return truthy(env.get("BREAKING_ENABLE_WEBSWARM"), True)


def x_intel_query_terms(plan: SearchNode | None = None, *, max_terms: int = DEFAULT_MAX_QUERY_TERMS) -> list[str]:
    plan = plan or build_ai_brief_webswarm_plan()
    terms = []
    for node in plan.walk():
        if node.mode == "x_intel":
            terms.extend(quoted(term) for term in node.query_terms)
    return dedupe_terms(terms)[:max(1, max_terms)]


def expand_x_query(seed_query: str, env: dict[str, str] | None = None) -> str:
    env = env or {}
    if not webswarm_enabled(env):
        return seed_query
    max_terms = safe_int(env.get("BREAKING_WEBSWARM_MAX_QUERY_TERMS"), DEFAULT_MAX_QUERY_TERMS)
    plan = build_ai_brief_webswarm_plan(source_focus=env.get("BREAKING_SOURCE_FOCUS", "x"))
    existing = {normalize_term(term) for term in re.split(r"\s+OR\s+", seed_query or "", flags=re.IGNORECASE)}
    additions = [
        term
        for term in x_intel_query_terms(plan, max_terms=max_terms)
        if normalize_term(term) not in existing
    ]
    if not seed_query.strip():
        return " OR ".join(additions)
    if not additions:
        return seed_query
    return seed_query.strip() + " OR " + " OR ".join(additions)


def expand_news_queries(queries: list[str], env: dict[str, str] | None = None) -> list[str]:
    env = env or {}
    if not webswarm_enabled(env):
        return queries
    plan = build_ai_brief_webswarm_plan(source_focus=env.get("BREAKING_SOURCE_FOCUS", "x"))
    additions = []
    for node in plan.walk():
        if node.mode in {"x_intel", "public_corroboration"} and node.depth >= 2:
            additions.append(" ".join(term.strip('"') for term in node.query_terms[:4]))
    max_queries = safe_int(env.get("BREAKING_WEBSWARM_MAX_NEWS_QUERIES"), 10)
    return dedupe_terms([*queries, *additions])[:max(1, max_queries)]


def node_match_score(candidate: dict, node: SearchNode) -> tuple[int, list[str]]:
    text = " ".join(
        str(candidate.get(key, ""))
        for key in ("title", "content", "reason", "alert", "url", "source")
    ).lower()
    if not text:
        return 0, []
    matched = []
    score = 0
    for term in (*node.query_terms, *node.evidence_terms):
        key = normalize_term(term)
        if key and key in text:
            matched.append(term)
            score += 2 if term in node.query_terms else 1
    return score, dedupe_terms(matched)


def annotate_candidates(candidates: list[dict], plan: SearchNode | None = None) -> list[dict]:
    plan = plan or build_ai_brief_webswarm_plan()
    searchable_nodes = [node for node in plan.walk() if node.depth > 0]
    annotated = []
    for candidate in candidates:
        best_node = None
        best_score = 0
        best_terms: list[str] = []
        for node in searchable_nodes:
            score, terms = node_match_score(candidate, node)
            if score > best_score:
                best_node = node
                best_score = score
                best_terms = terms
        item = dict(candidate)
        if best_node and best_score > 0:
            item["webswarm_node"] = best_node.id
            item["webswarm_mode"] = best_node.mode
            item["webswarm_evidence_terms"] = best_terms[:8]
        annotated.append(item)
    return annotated


def plan_public_summary(env: dict[str, str] | None = None) -> dict:
    env = env or {}
    enabled = webswarm_enabled(env)
    if not enabled:
        return {"enabled": False}
    plan = build_ai_brief_webswarm_plan(source_focus=env.get("BREAKING_SOURCE_FOCUS", "x"))
    nodes = list(plan.walk())
    modes = sorted({node.mode for node in nodes})
    return {
        "enabled": True,
        "root": plan.id,
        "node_count": len(nodes),
        "max_depth": max(node.depth for node in nodes),
        "modes": modes,
        "reuse_keys": sorted({node.reuse_key for node in nodes if node.reuse_key}),
        "x_query_terms": len(x_intel_query_terms(plan)),
    }


def render_plan(plan: SearchNode | None = None) -> str:
    plan = plan or build_ai_brief_webswarm_plan()
    return json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
