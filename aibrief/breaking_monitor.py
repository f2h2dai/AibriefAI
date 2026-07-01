from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


STATE_PATH = Path("data/breaking_state.json")
PUBLIC_STATUS_PATH = Path("web/data/breaking_status.json")
COMMAND_CENTER_URL = "https://aibriefai.onrender.com/"
DEFAULT_BIRDCLAW_EXPORT_PATH = Path("private/birdclaw-export.json")
DEFAULT_CADENCE_MINUTES = 15
DEFAULT_MAX_LLM_REQUESTS = 1
DEFAULT_MAX_CANDIDATES = 20
DEFAULT_MIN_CONFIDENCE = 0.90
DEFAULT_MIN_X_RELEVANCE = 2
DEFAULT_X_INTEL_QUERY = (
    '"Grok AI" OR "Grok Gov" OR "Grok Gov Model" OR "Project Maven" '
    'OR "AI targeting" OR "AI target selection" OR "military AI" OR "defense AI" '
    'OR "battlefield AI" OR "autonomous weapons" OR "AI weapons" '
    'OR "Pentagon AI" OR "DoD AI" OR "Grok missiles" OR "Grok targets" '
    'OR "2000 targets" OR "2,000 targets" OR "96 hours" '
    'OR "MizarVision" OR "Meentropy" OR "AI-tagged satellite" '
    'OR "AI tagged satellite" OR "geospatial intelligence" '
    'OR "Prince Sultan Air Base" OR "stealth fighters" OR "warships" '
    'OR "frontier AI" OR "AI agents" OR "OpenAI" OR "Anthropic" '
    'OR "Gemini" OR "Grok" OR "xAI" OR "NVIDIA" OR "AI data center" '
    'OR "الذكاء الاصطناعي" OR "ذكاء اصطناعي" OR "غروك" '
    'OR "جيميناي" OR "البنتاغون" OR "إيران" OR "ايران"'
)
DEFAULT_AI_INTEL_NEWS_QUERIES = [
    '"Grok AI" Pentagon Iran 2000 targets 96 hours',
    '"Grok Gov Model" "Project Maven"',
    '"MizarVision" AI satellite Iran "Prince Sultan Air Base"',
    '"AI targeting" Pentagon Iran',
    '"military AI" "Project Maven"',
    '"geospatial intelligence" AI "Middle East"',
]
DEFAULT_X_INFLUENCERS = [
    "karpathy",
    "sama",
    "gdb",
    "jeffdean",
    "ilyasut",
    "ylecun",
    "demishassabis",
    "andrewyng",
    "elonmusk",
    "fchollet",
    "miramurati",
    "drjimfan",
    "geoffreyhinton",
    "drfeifei",
    "officiallogank",
    "_akhaliq",
    "patrickc",
    "hardmaru",
    "dwarkesh_sp",
    "polynoamial",
    "lilianweng",
    "johnschulman2",
    "clementdelangue",
    "jackclarksf",
    "soumithchintala",
    "alexandr_wang",
    "jeremyphoward",
    "garrytan",
    "thom_wolf",
    "ch402",
    "oriolvinyalsml",
    "janleike",
    "davidsholz",
    "miles_brundage",
    "id_aa_carmack",
    "aravsrinivas",
    "_jasonwei",
    "sundarpichai",
    "sarahookr",
    "swyx",
    "saranormous",
    "scobleizer",
    "lexfridman",
    "ericjang11",
    "emollick",
    "chrmanning",
    "simonw",
    "woj_zaremba",
    "emostaque",
    "amasad",
    "goodside",
    "alecrad",
    "danielgross",
    "chelseabfinn",
    "srush_nlp",
    "markchen90",
    "bcherny",
    "natolambert",
    "_sholtodouglas",
    "pabbeel",
    "dylan522p",
    "percyliang",
    "steipete",
    "arankomatsuzaki",
    "amandaaskell",
    "darioamodei",
    "svlevine",
    "rauchg",
    "levie",
    "satyanadella",
    "reidhoffman",
    "willdepue",
    "sriramk",
    "liamfedus",
    "suchenzang",
    "teknium",
    "sleepinyourhat",
    "nandodf",
    "RichardSocher",
    "martin_casado",
    "suhail",
    "sebastienbubeck",
    "ibab",
    "davidsacks",
    "millionint",
    "mustafasuleyman",
    "levelsio",
    "benthompson",
    "shaneguml",
    "chrszegedy",
    "nearcyan",
    "deedydas",
    "rasbt",
    "arohan",
    "eshear",
    "chhillee",
    "collision",
    "tim_dettmers",
    "kchonyc",
    "chamath",
]

AI_WAR_EXACT_PATTERNS = [
    "grok ai",
    "grok helped",
    "grok missiles",
    "grok targets",
    "grok gov",
    "grok gov model",
    "project maven",
    "maven intelligent system",
    "ai targeting",
    "ai target selection",
    "artificial intelligence targeting",
    "algorithmic targeting",
    "computer vision targeting",
    "military ai",
    "defense ai",
    "defence ai",
    "battlefield ai",
    "autonomous weapons",
    "autonomous weapon",
    "ai weapons",
    "ai weapon",
    "pentagon ai",
    "dod ai",
    "department of defense ai",
    "ai in war",
    "grok military",
    "grok pentagon",
    "grok iran",
    "xai pentagon",
    "mizarvision",
    "meentropy",
    "ai-tagged satellite",
    "ai tagged satellite",
    "ai satellite imagery",
    "geospatial intelligence",
    "geospatial analysis",
    "autonomously map",
    "prince sultan air base",
    "stealth fighters",
    "warships",
    "2000 targets",
    "2,000 targets",
    "2000 missiles",
    "2,000 missiles",
    "96 hours",
]

AI_WAR_AI_MARKERS = [
    "artificial intelligence",
    "frontier ai",
    "machine learning",
    "computer vision",
    "model",
    "models",
    "agent",
    "agents",
    "ai-tagged",
    "geospatial",
    "satellite imagery",
    "remote sensing",
    "large language model",
    "llm",
    "openai",
    "anthropic",
    "gemini",
    "grok",
    "xai",
    "nvidia",
    "gpu",
    "maven",
    "autonomous",
    "algorithmic",
    "الذكاء الاصطناعي",
    "ذكاء اصطناعي",
    "غروك",
    "جيميناي",
]

AI_WAR_MILITARY_MARKERS = [
    "military",
    "defense",
    "defence",
    "pentagon",
    "dod",
    "department of defense",
    "munitions",
    "munition",
    "missile",
    "missiles",
    "targeting",
    "target selection",
    "targets",
    "battlefield",
    "weapon",
    "weapons",
    "drone",
    "drones",
    "strike",
    "airstrike",
    "operation",
    "project maven",
    "iran",
    "irgc",
    "air base",
    "airbase",
    "military assets",
    "military deployments",
    "stealth fighter",
    "stealth fighters",
    "warship",
    "warships",
    "u.s. forces",
    "us forces",
    "عسكري",
    "عسكرية",
    "دفاع",
    "الدفاع",
    "البنتاغون",
    "ايران",
    "إيران",
    "صاروخ",
    "صواريخ",
    "استهداف",
    "هدف",
    "اهداف",
    "أهداف",
    "درون",
    "طائرة مسيرة",
    "طائرات مسيرة",
]

X_INTEL_EVENT_MARKERS = [
    "breaking",
    "just in",
    "exclusive",
    "confirmed",
    "reported",
    "report",
    "says",
    "statement",
    "official",
    "leaked",
    "used",
    "deployed",
    "launch",
    "released",
    "contract",
    "government",
    "military",
    "targeting",
    "satellite",
    "missile",
    "munitions",
    "war",
    "iran",
    "عاجل",
    "تقرير",
    "مصادر",
    "أكد",
    "اعلن",
    "أعلن",
    "استخدم",
    "استخدام",
    "نشر",
    "استهداف",
]

HIGH_IMPACT_PATTERNS = {
    "military or intelligence AI deployment": [
        "military",
        "defense",
        "intelligence",
        "munitions",
        "project maven",
        "maven intelligent system",
        "grok gov",
        "grok gov model",
        "pentagon",
        "dod",
        "department of defense",
        "u.s. military",
        "us military",
        "war with iran",
        "operations against iran",
        "operation epic fury",
        "battlefield",
        "weapons",
        "drone",
        "target selection",
        "ai targeting",
        "kill chain",
    ],
    "frontier-model safety or security incident": [
        "frontier model",
        "model safety",
        "safety incident",
        "jailbreak",
        "model leak",
        "weights leaked",
        "misuse",
    ],
    "major government restriction or landmark regulation": [
        "landmark ai law",
        "ai act",
        "government restriction",
        "executive order",
        "regulation",
        "regulator",
    ],
    "major breach or model compromise": [
        "breach",
        "compromise",
        "exfiltrated",
        "credential leak",
        "security incident",
        "stolen model",
    ],
    "shutdown, ban, injunction or contract termination": [
        "shutdown",
        "ban",
        "banned",
        "injunction",
        "contract termination",
        "terminated contract",
        "suspended",
    ],
    "leadership upheaval at a frontier AI organization": [
        "resigned",
        "ousted",
        "removed",
        "board",
        "ceo",
        "chief scientist",
        "leadership crisis",
    ],
    "major autonomous-system deployment": [
        "autonomous system",
        "robotaxi",
        "autonomous drone",
        "self-driving",
        "deployed autonomous",
    ],
    "critical AI infrastructure disruption": [
        "gpu outage",
        "data center outage",
        "cloud outage",
        "inference outage",
        "critical infrastructure",
    ],
}

CONSEQUENCE_PATTERNS = {
    "confirmed deployment": ["confirmed deployment", "deployed", "launched across", "operational"],
    "military targeting or munition deployment": [
        "targeting",
        "targets",
        "target selection",
        "munitions",
        "strike",
        "strikes",
        "airstrike",
        "airstrikes",
        "military operations",
        "support operations",
        "operation epic fury",
        "custom version",
        "official statement",
    ],
    "official filing": ["official filing", "sec filing", "court filing", "filed in court"],
    "government order": ["government order", "ordered", "directive", "sanctioned"],
    "court decision": ["court decision", "injunction", "ruling", "judge ordered"],
    "breach disclosure": ["breach disclosure", "disclosed breach", "confirmed breach"],
    "shutdown": ["shutdown", "shut down", "taken offline"],
    "contract termination": ["contract termination", "terminated contract", "contract canceled"],
    "casualties or physical consequences": ["casualties", "injured", "killed", "physical damage"],
    "material market or infrastructure consequence": [
        "material impact",
        "market halt",
        "trading halt",
        "outage",
        "supply disruption",
    ],
    "emergency response": ["emergency response", "incident response", "evacuation"],
}

ROUTINE_PATTERNS = [
    "benchmark",
    "leaderboard",
    "star milestone",
    "stars on github",
    "product changelog",
    "release notes",
    "tutorial",
    "prompt engineering thread",
    "opinion",
    "takeaways",
]

AUTHORITATIVE_HOSTS = [
    ".gov",
    ".mil",
    "court",
    "justice.gov",
    "sec.gov",
    "europa.eu",
    "whitehouse.gov",
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "ai.google",
    "microsoft.com",
    "meta.com",
    "x.ai",
]

KNOWN_ENTITIES = [
    "OpenAI",
    "Anthropic",
    "Google",
    "DeepMind",
    "Gemini",
    "Grok",
    "Grok Gov",
    "Grok Gov Model",
    "xAI",
    "Iran",
    "Operation Epic Fury",
    "DoD",
    "U.S. military",
    "Meta",
    "Microsoft",
    "NVIDIA",
    "Mistral",
    "Project Maven",
    "European Union",
    "EU",
    "Pentagon",
    "Department of Defense",
]

STOPWORDS = {
    "about",
    "after",
    "against",
    "and",
    "from",
    "into",
    "over",
    "that",
    "the",
    "this",
    "with",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truthy(value, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if not normalized:
        return default
    return normalized not in {"0", "false", "no", "off"}


def canonicalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or "").strip())
    if not parsed.netloc:
        return ""
    host = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+$", "", parsed.path or "/")
    return urllib.parse.urlunparse((parsed.scheme.lower() or "https", host, path, "", "", ""))


def source_host(url: str) -> str:
    return urllib.parse.urlparse(canonicalize_url(url)).netloc


def stable_id(*parts: str) -> str:
    raw = "|".join(normalize_text(part).lower() for part in parts if part)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def find_hits(text: str, pattern_map: dict[str, list[str]]) -> list[str]:
    lowered = text.lower()
    hits = []
    for label, patterns in pattern_map.items():
        if any(pattern in lowered for pattern in patterns):
            hits.append(label)
    return hits


def routine_only(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in ROUTINE_PATTERNS)


def is_authoritative(url: str) -> bool:
    host = source_host(url)
    return any(marker in host for marker in AUTHORITATIVE_HOSTS)


def named_entities(text: str) -> list[str]:
    found = []
    lowered = text.lower()
    for entity in KNOWN_ENTITIES:
        if entity.lower() in lowered:
            found.append(entity.lower())

    for match in re.findall(r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3}", text):
        normalized = match.strip().lower()
        if normalized and normalized not in STOPWORDS and normalized not in found:
            found.append(normalized)

    return sorted(found)[:8]


def event_verbs(text: str) -> list[str]:
    lowered = text.lower()
    verbs = []
    for patterns in CONSEQUENCE_PATTERNS.values():
        for pattern in patterns:
            if pattern in lowered:
                verbs.append(pattern)
    return sorted(set(verbs))[:8]


def title_terms(title: str) -> str:
    words = [
        word
        for word in re.findall(r"[a-z0-9]+", title.lower())
        if len(word) > 2 and word not in STOPWORDS
    ]
    return "-".join(words[:10])


def candidate_from_raw(raw: dict) -> dict:
    title = normalize_text(raw.get("title", ""))
    content = normalize_text(raw.get("content") or raw.get("summary") or raw.get("description") or "")
    url = canonicalize_url(raw.get("url", ""))
    source = normalize_text(raw.get("source", "unknown")).lower() or "unknown"
    published_at = normalize_text(raw.get("published_at") or raw.get("createdAt") or raw.get("updatedAt") or "")
    text = f"{title} {content}"
    domain_hits = find_hits(text, HIGH_IMPACT_PATTERNS)
    action_hits = find_hits(text, CONSEQUENCE_PATTERNS)
    velocity = int(raw.get("velocity") or raw.get("points") or raw.get("score") or 0)

    return {
        "candidate_id": raw.get("candidate_id") or stable_id(source, url, title),
        "source": source,
        "title": title,
        "content": content,
        "url": url,
        "published_at": published_at,
        "velocity": velocity,
        "source_count": int(raw.get("source_count") or 1),
        "authoritative": bool(raw.get("authoritative")) or is_authoritative(url),
        "domain_hits": domain_hits,
        "action_hits": action_hits,
        "entities": named_entities(text),
        "event_verbs": event_verbs(text),
    }


def story_fingerprint(candidate: dict) -> str:
    event_date = (candidate.get("published_at") or isoformat(utc_now()))[:10]
    entities = ",".join(candidate.get("entities") or [])
    verbs = ",".join(candidate.get("event_verbs") or [])
    terms = title_terms(candidate.get("title", ""))
    host = source_host(candidate.get("url", ""))
    raw = f"{entities}|{verbs}|{event_date}|{terms}|{host}"
    return "story-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def merge_cluster(existing: dict, candidate: dict) -> dict:
    urls = sorted(set(existing.get("source_urls", [])) | {candidate.get("url", "")})
    sources = sorted(set(existing.get("sources", [])) | {candidate.get("source", "unknown")})
    existing["source_urls"] = [url for url in urls if url]
    existing["sources"] = sources
    existing["source_count"] = max(int(existing.get("source_count", 1)), len(sources))
    existing["velocity"] = max(int(existing.get("velocity", 0)), int(candidate.get("velocity", 0)))
    existing["authoritative"] = bool(existing.get("authoritative")) or bool(candidate.get("authoritative"))
    existing["domain_hits"] = sorted(set(existing.get("domain_hits", [])) | set(candidate.get("domain_hits", [])))
    existing["action_hits"] = sorted(set(existing.get("action_hits", [])) | set(candidate.get("action_hits", [])))
    return existing


def cluster_story_candidates(raw_candidates: list[dict]) -> list[dict]:
    clustered: dict[str, dict] = {}
    for raw in raw_candidates:
        candidate = candidate_from_raw(raw)
        fingerprint = story_fingerprint(candidate)
        candidate["story_fingerprint"] = fingerprint
        candidate["source_urls"] = [candidate["url"]] if candidate.get("url") else []
        candidate["sources"] = [candidate.get("source", "unknown")]
        if fingerprint in clustered:
            clustered[fingerprint] = merge_cluster(clustered[fingerprint], candidate)
        else:
            clustered[fingerprint] = candidate
    return list(clustered.values())


def stage1_score(candidate: dict) -> int:
    score = 0
    score += 30 if candidate.get("domain_hits") else 0
    score += 30 if candidate.get("action_hits") else 0
    score += min(25, int(candidate.get("velocity", 0)) // 4)
    score += 15 if int(candidate.get("source_count", 1)) > 1 else 0
    score += 15 if candidate.get("authoritative") else 0
    return score


def survives_stage1(candidate: dict) -> bool:
    text = f"{candidate.get('title', '')} {candidate.get('content', '')}"
    if routine_only(text) and not candidate.get("action_hits"):
        return False
    if not candidate.get("domain_hits"):
        return False
    if not candidate.get("action_hits"):
        return False
    has_velocity_or_corroboration = (
        int(candidate.get("velocity", 0)) >= 30
        or int(candidate.get("source_count", 1)) > 1
        or bool(candidate.get("authoritative"))
    )
    return has_velocity_or_corroboration


def prioritize_candidates(candidates: list[dict]) -> list[dict]:
    return sorted(
        candidates,
        key=lambda candidate: (
            stage1_score(candidate),
            int(candidate.get("source_count", 1)),
            int(candidate.get("velocity", 0)),
        ),
        reverse=True,
    )


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"version": 1, "updated_at": "", "alerted": {}, "pending": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "version": 1,
        "updated_at": data.get("updated_at", ""),
        "alerted": data.get("alerted", {}),
        "pending": data.get("pending", {}),
    }


def save_state(state: dict, path: Path = STATE_PATH, now: datetime | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["version"] = 1
    state["updated_at"] = isoformat(now or utc_now())
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def latest_alert_entry(state: dict) -> dict | None:
    entries = list(state.get("alerted", {}).values())
    if not entries:
        return None
    return sorted(entries, key=lambda entry: entry.get("alerted_at", ""), reverse=True)[0]


def public_feed_entries(state: dict, limit: int = 12) -> list[dict]:
    entries = []
    for fingerprint, entry in state.get("alerted", {}).items():
        source_urls = entry.get("source_urls") or []
        entries.append(
            {
                "id": fingerprint,
                "title": entry.get("title", ""),
                "shown_at": entry.get("alerted_at", ""),
                "source_url": source_urls[0] if source_urls else "",
                "source": public_source_name(entry.get("source", "")),
                "score": entry.get("score", 0),
                "confidence": entry.get("confidence", 0),
                "status": entry.get("notification_status", "x-intel"),
                "reason": entry.get("reason", ""),
            }
        )
    return sorted(entries, key=lambda item: item.get("shown_at", ""), reverse=True)[:limit]


def public_pending_entries(state: dict, limit: int = 6) -> list[dict]:
    entries = []
    for fingerprint, entry in state.get("pending", {}).items():
        candidate = entry.get("candidate") if isinstance(entry.get("candidate"), dict) else entry
        source_urls = candidate.get("source_urls") or entry.get("source_urls") or []
        entries.append(
            {
                "id": fingerprint,
                "title": candidate.get("title", entry.get("title", "")),
                "shown_at": entry.get("last_seen_at", ""),
                "source_url": source_urls[0] if source_urls else candidate.get("url", ""),
                "source": public_source_name(candidate.get("source", entry.get("source", ""))),
                "score": candidate.get("stage1_score", entry.get("score", 0)),
                "confidence": candidate.get("confidence", 0),
                "status": "x-intel"
                if entry.get("status") == "awaiting_classification"
                else entry.get("status", "x-intel"),
                "reason": entry.get("reason")
                or candidate.get("content")
                or "Public X signal about AI use in military, defense, targeting, or intelligence operations.",
            }
        )
    return sorted(entries, key=lambda item: item.get("shown_at", ""), reverse=True)[:limit]


def public_status_reason(reason: str) -> str:
    text = normalize_text(reason)
    if text in {"missing Gemini key", "Gemini URL error"}:
        return "Public X intel mode is active."
    return text or "Public X signal about AI use in military, defense, targeting, or intelligence operations."


def public_source_name(source: str) -> str:
    normalized = normalize_text(source).lower()
    if normalized in {"birdclaw", "twitter", "x/twitter"}:
        return "x"
    return normalized or "x"


def public_last_run(summary: dict | None) -> dict:
    if not summary:
        return {}
    public = dict(summary)
    public.pop("classified", None)
    public.pop("classification_reason", None)
    return public


def public_breaking_status(state: dict, summary: dict | None = None) -> dict:
    latest = latest_alert_entry(state)
    pending = state.get("pending", {})
    alerted = state.get("alerted", {})
    status = "clear"
    pending_entries = public_pending_entries(state)
    if any(entry.get("status") == "approved" for entry in pending.values()):
        status = "retry-pending"
    elif pending:
        status = "x-intel"
    if latest:
        status = "x-intel"

    return {
        "version": 1,
        "updated_at": state.get("updated_at", ""),
        "status": status,
        "cadence_minutes": DEFAULT_CADENCE_MINUTES,
        "alerted_count": len(alerted),
        "pending_count": len(pending),
        "feed": public_feed_entries(state),
        "pending_feed": pending_entries,
        "last_alert": {
            "title": latest.get("title", "") if latest else "",
            "alerted_at": latest.get("alerted_at", "") if latest else "",
            "source_url": (latest.get("source_urls") or [""])[0] if latest else "",
            "confidence": latest.get("confidence", 0) if latest else 0,
        },
        "last_run": public_last_run(summary),
    }


def write_public_status(
    state: dict,
    summary: dict | None = None,
    path: Path = PUBLIC_STATUS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(public_breaking_status(state, summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prune_alerted(state: dict, now: datetime | None = None) -> None:
    cutoff = (now or utc_now()) - timedelta(days=30)
    retained = {}
    for fingerprint, entry in state.get("alerted", {}).items():
        value = entry.get("alerted_at") or entry.get("last_seen_at") or ""
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            timestamp = now or utc_now()
        if timestamp >= cutoff:
            retained[fingerprint] = entry
    state["alerted"] = retained


def public_candidate(candidate: dict) -> dict:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "story_fingerprint": candidate.get("story_fingerprint"),
        "title": candidate.get("title"),
        "content": candidate.get("content"),
        "source": candidate.get("source"),
        "source_urls": candidate.get("source_urls", []),
        "url": candidate.get("url"),
        "published_at": candidate.get("published_at"),
        "velocity": candidate.get("velocity", 0),
        "source_count": candidate.get("source_count", 1),
        "authoritative": candidate.get("authoritative", False),
        "confidence": candidate.get("confidence"),
        "alert": candidate.get("alert"),
        "reason": candidate.get("reason"),
        "stage1_score": stage1_score(candidate),
    }


def ai_war_relevant(candidate: dict) -> bool:
    return x_intel_relevance_score(candidate) >= DEFAULT_MIN_X_RELEVANCE


def x_intel_relevance_score(candidate: dict) -> int:
    text = normalize_text(
        " ".join(
            str(candidate.get(key, ""))
            for key in ("title", "content", "reason", "alert")
        )
    ).lower()
    if not text:
        return 0
    score = 0
    if any(pattern in text for pattern in AI_WAR_EXACT_PATTERNS):
        score += 4
    ai_hit = bool(re.search(r"\bai\b", text)) or any(marker in text for marker in AI_WAR_AI_MARKERS)
    military_hit = any(marker in text for marker in AI_WAR_MILITARY_MARKERS)
    event_hit = any(marker in text for marker in X_INTEL_EVENT_MARKERS)
    if ai_hit:
        score += 2
    if military_hit:
        score += 1
    if event_hit and (ai_hit or score >= 4):
        score += 1
    return score


def is_x_intel_candidate(candidate: dict, env: dict[str, str]) -> bool:
    source = str(candidate.get("source", "")).lower()
    urls = " ".join(candidate.get("source_urls") or [candidate.get("url", "")]).lower()
    is_x_source = source in {"birdclaw", "twitter", "x", "x/twitter"} or "x.com/" in urls or "twitter.com/" in urls
    min_relevance = max(1, safe_int(env.get("BREAKING_MIN_X_RELEVANCE"), DEFAULT_MIN_X_RELEVANCE))
    return is_x_source and x_intel_relevance_score(candidate) >= min_relevance


def is_news_fallback_candidate(candidate: dict, env: dict[str, str]) -> bool:
    if not truthy(env.get("BREAKING_ALLOW_NEWS_FALLBACK"), True):
        return False
    source = str(candidate.get("source", "")).lower()
    is_news_source = source in {"news", "google-news", "public-news", "rss"}
    min_relevance = max(1, safe_int(env.get("BREAKING_MIN_X_RELEVANCE"), DEFAULT_MIN_X_RELEVANCE))
    return is_news_source and x_intel_relevance_score(candidate) >= min_relevance


def is_website_intel_candidate(candidate: dict, env: dict[str, str]) -> bool:
    return is_x_intel_candidate(candidate, env) or is_news_fallback_candidate(candidate, env)


def x_intel_reason(candidate: dict) -> str:
    content = normalize_text(candidate.get("content", ""))
    if content:
        return content[:280]
    return "Public X signal about AI use in military, defense, targeting, or intelligence operations."


def prune_irrelevant_x_intel(state: dict, env: dict[str, str]) -> None:
    if env.get("BREAKING_SOURCE_FOCUS", "").strip().lower() not in {"x", "twitter"}:
        return
    for bucket_name in ("alerted", "pending"):
        bucket = state.get(bucket_name, {})
        for fingerprint, entry in list(bucket.items()):
            candidate = entry.get("candidate") if isinstance(entry.get("candidate"), dict) else entry
            if not is_website_intel_candidate(candidate, env):
                del bucket[fingerprint]


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    if cleaned.startswith("{"):
        return json.loads(cleaned)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def gemini_prompt(candidates: list[dict]) -> str:
    payload = [
        {
            "candidate_id": candidate["candidate_id"],
            "title": candidate.get("title"),
            "content": candidate.get("content"),
            "sources": candidate.get("source_urls", []),
            "stage1_score": stage1_score(candidate),
            "domain_hits": candidate.get("domain_hits", []),
            "action_hits": candidate.get("action_hits", []),
        }
        for candidate in candidates
    ]
    return (
        "Classify AIbrief breaking AI stories. Return strict JSON only. "
        "Approve only rare high-impact stories with real-world consequence, "
        "corroboration, or an authoritative primary source. Do not treat supplied "
        "examples as verified unless evidence is in the candidate.\n\n"
        "Output schema: {\"results\":[{\"candidate_id\":\"stable-id\","
        "\"breaking\":true,\"confidence\":0.0,\"reason\":\"one sentence\","
        "\"alert\":\"short notification sentence\"}]}\n\n"
        + json.dumps({"candidates": payload}, ensure_ascii=False)
    )


def validate_classifications(payload: dict, candidate_ids: set[str]) -> dict[str, dict]:
    valid: dict[str, dict] = {}
    results = payload.get("results")
    if not isinstance(results, list):
        return valid
    for item in results:
        if not isinstance(item, dict):
            continue
        candidate_id = item.get("candidate_id")
        if candidate_id not in candidate_ids:
            continue
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            continue
        valid[candidate_id] = {
            "candidate_id": candidate_id,
            "breaking": item.get("breaking") is True,
            "confidence": confidence,
            "reason": normalize_text(item.get("reason", ""))[:240],
            "alert": normalize_text(item.get("alert", ""))[:180],
        }
    return valid


def classify_with_gemini(candidates: list[dict], env: dict[str, str]) -> tuple[dict[str, dict], str]:
    api_key = env.get("GEMINI_API_KEY", "").strip()
    model = env.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    max_requests = int(env.get("BREAKING_MAX_LLM_REQUESTS_PER_RUN", str(DEFAULT_MAX_LLM_REQUESTS)))
    if not api_key:
        return {}, "missing Gemini key"
    if max_requests < 1:
        return {}, "LLM request budget exhausted"
    if not candidates:
        return {}, "no candidates"

    body = {
        "contents": [{"parts": [{"text": gemini_prompt(candidates)}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return {}, "Gemini 429 rate limited"
        return {}, f"Gemini HTTP {exc.code}"
    except urllib.error.URLError:
        return {}, "Gemini URL error"
    except Exception as exc:
        return {}, f"Gemini {type(exc).__name__}"

    try:
        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        parsed = extract_json(text)
    except Exception:
        return {}, "malformed Gemini output"
    return validate_classifications(parsed, {candidate["candidate_id"] for candidate in candidates}), "classified"


def send_breaking_notification(story: dict, env: dict[str, str]) -> tuple[bool, str]:
    topic = env.get("NTFY_TOPIC_BREAKING", "").strip()
    if not topic:
        return False, "breaking notification topic missing"

    click_url = story.get("url") or (story.get("source_urls") or [COMMAND_CENTER_URL])[0] or COMMAND_CENTER_URL
    body = "\n".join(
        [
            story.get("alert") or story.get("title") or "Breaking AI signal",
            "",
            "Why it matters: " + (story.get("reason") or "High-confidence breaking AI signal."),
            "",
            "Open source or command center",
        ]
    )
    req = urllib.request.Request(
        f"https://ntfy.sh/{urllib.parse.quote(topic, safe='')}",
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Title": "\U0001f6a8 AIbrief Breaking",
            "Priority": "high",
            "Tags": "warning,rotating_light",
            "Click": click_url,
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response.read(1000)
        return True, "sent"
    except urllib.error.HTTPError as exc:
        return False, f"ntfy HTTP {exc.code}"
    except urllib.error.URLError:
        return False, "ntfy URL error"
    except Exception as exc:
        return False, f"ntfy {type(exc).__name__}"


def retry_pending_notifications(state: dict, env: dict[str, str], notify_func, now: datetime) -> list[dict]:
    retried = []
    for fingerprint, entry in list(state.get("pending", {}).items()):
        if entry.get("status") != "approved":
            continue
        success, reason = notify_func(entry, env)
        entry["notification_status"] = reason
        entry["last_seen_at"] = isoformat(now)
        if success:
            state["alerted"][fingerprint] = {
                "alerted_at": isoformat(now),
                "last_seen_at": isoformat(now),
                "title": entry.get("title", ""),
                "source_urls": entry.get("source_urls", []),
                "confidence": entry.get("confidence", 0),
                "notification_status": "sent",
            }
            del state["pending"][fingerprint]
        retried.append({"fingerprint": fingerprint, "sent": success, "reason": reason})
    return retried


def publish_pending_website_only(state: dict, now: datetime) -> list[dict]:
    published = []
    for fingerprint, entry in list(state.get("pending", {}).items()):
        candidate = entry.get("candidate") if isinstance(entry.get("candidate"), dict) else entry
        source_urls = candidate.get("source_urls") or entry.get("source_urls") or []
        state["alerted"][fingerprint] = {
            "alerted_at": isoformat(now),
            "last_seen_at": isoformat(now),
            "title": candidate.get("title", entry.get("title", "")),
            "content": candidate.get("content", entry.get("content", "")),
            "source": public_source_name(candidate.get("source", entry.get("source", ""))),
            "source_urls": source_urls,
            "score": candidate.get("stage1_score", entry.get("score", 0)),
            "confidence": entry.get("confidence", 0),
            "notification_status": "x-intel",
            "reason": entry.get("reason") or x_intel_reason(candidate),
        }
        del state["pending"][fingerprint]
        published.append({"fingerprint": fingerprint, "sent": False, "reason": "x-intel"})
    return published


def publish_candidate_website_only(state: dict, candidate: dict, now: datetime) -> None:
    fingerprint = candidate["story_fingerprint"]
    state["alerted"][fingerprint] = {
        "alerted_at": isoformat(now),
        "last_seen_at": isoformat(now),
        "title": candidate.get("title", ""),
        "content": candidate.get("content", ""),
        "source": public_source_name(candidate.get("source", "")),
        "source_urls": candidate.get("source_urls", []),
        "score": stage1_score(candidate),
        "confidence": 0,
        "notification_status": "x-intel",
        "reason": x_intel_reason(candidate),
    }
    state.get("pending", {}).pop(fingerprint, None)


def collect_hackernews(limit: int = 20) -> list[dict]:
    url = "https://hn.algolia.com/api/v1/search_by_date?query=AI%20OR%20LLM%20OR%20OpenAI%20OR%20Grok&tags=story&hitsPerPage=" + str(limit)
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    results = []
    for hit in payload.get("hits", []):
        results.append(
            {
                "source": "hackernews",
                "title": hit.get("title") or hit.get("story_title") or "",
                "content": hit.get("story_text") or "",
                "url": hit.get("url") or hit.get("story_url") or "",
                "published_at": hit.get("created_at") or "",
                "velocity": int(hit.get("points") or hit.get("num_comments") or 0),
            }
        )
    return results


def collect_arxiv(limit: int = 10) -> list[dict]:
    url = "https://export.arxiv.org/api/query?search_query=all:AI+OR+all:LLM&sortBy=submittedDate&sortOrder=descending&max_results=" + str(limit)
    with urllib.request.urlopen(url, timeout=20) as response:
        root = ET.fromstring(response.read())
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results = []
    for entry in root.findall("atom:entry", ns):
        title = normalize_text(entry.findtext("atom:title", default="", namespaces=ns))
        summary = normalize_text(entry.findtext("atom:summary", default="", namespaces=ns))
        link = ""
        for link_node in entry.findall("atom:link", ns):
            if link_node.attrib.get("rel") == "alternate":
                link = link_node.attrib.get("href", "")
                break
        results.append(
            {
                "source": "arxiv",
                "title": title,
                "content": summary,
                "url": link,
                "published_at": entry.findtext("atom:published", default="", namespaces=ns),
                "velocity": 0,
            }
        )
    return results


def collect_local_signals(
    path: Path = Path("web/data/signals.json"),
    source_focus: str = "",
) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    signals = payload if isinstance(payload, list) else payload.get("signals", [])
    focus = source_focus.strip().lower()
    if focus in {"x", "twitter"}:
        signals = [
            signal
            for signal in signals
            if str(signal.get("source", "")).lower() in {"twitter", "x", "x/twitter"}
            or "x.com/" in str(signal.get("url", "")).lower()
            or "twitter.com/" in str(signal.get("url", "")).lower()
        ]
    return [
        {
            "source": signal.get("source", "local"),
            "title": signal.get("title", ""),
            "content": signal.get("content") or signal.get("brief_en") or "",
            "url": signal.get("url", ""),
            "published_at": signal.get("updatedAt") or signal.get("createdAt") or "",
            "velocity": int(signal.get("score") or 0),
        }
        for signal in signals
    ]


def birdclaw_export_paths(env: dict[str, str]) -> list[Path]:
    raw = env.get("BIRDCLAW_EXPORT_PATH", str(DEFAULT_BIRDCLAW_EXPORT_PATH))
    return [Path(item.strip()) for item in re.split(r"[;\n]+", raw) if item.strip()]


def read_json_or_jsonl(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def birdclaw_record_text(record: dict) -> str:
    for key in ("text", "full_text", "content", "body", "tweet_text", "title", "summary"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_text(value)
    return ""


def birdclaw_handle(record: dict) -> str:
    for key in ("username", "screen_name", "handle", "author_username", "author_screen_name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lstrip("@")
    for key in ("author", "user", "profile"):
        value = record.get(key)
        if not isinstance(value, dict):
            continue
        for nested_key in ("username", "screen_name", "handle"):
            nested = value.get(nested_key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip().lstrip("@")
    return ""


def birdclaw_tweet_id(record: dict) -> str:
    for key in ("tweet_id", "id_str", "id", "rest_id", "status_id"):
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if re.fullmatch(r"\d{8,}", text):
            return text
    return ""


def birdclaw_record_url(record: dict) -> str:
    for key in ("url", "permalink", "link", "tweet_url"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            url = value.strip()
            if "x.com/" in url or "twitter.com/" in url:
                return url
    handle = birdclaw_handle(record)
    tweet_id = birdclaw_tweet_id(record)
    if handle and tweet_id:
        return f"https://x.com/{handle}/status/{tweet_id}"
    return ""


def is_private_birdclaw_record(record: dict) -> bool:
    marker_text = " ".join(
        str(record.get(key, "")).lower()
        for key in ("kind", "type", "source", "collection", "table", "surface")
    )
    return any(marker in marker_text for marker in ("dm", "direct message", "direct_message", "directmessage"))


def looks_like_public_birdclaw_tweet(record: dict) -> bool:
    if is_private_birdclaw_record(record):
        return False
    text = birdclaw_record_text(record)
    if not text:
        return False
    return bool(birdclaw_record_url(record))


def extract_birdclaw_records(payload) -> list[dict]:
    records: list[dict] = []
    if isinstance(payload, list):
        for item in payload:
            records.extend(extract_birdclaw_records(item))
        return records
    if not isinstance(payload, dict):
        return records
    if looks_like_public_birdclaw_tweet(payload):
        records.append(payload)
    for key, value in payload.items():
        if key.lower() in {"dm", "dms", "directmessages", "direct_messages", "direct-messages"}:
            continue
        if isinstance(value, (list, dict)):
            records.extend(extract_birdclaw_records(value))
    return records


def normalize_birdclaw_record(record: dict) -> dict | None:
    text = birdclaw_record_text(record)
    url = birdclaw_record_url(record)
    if not text or not url:
        return None
    velocity = max(
        safe_int(record.get("score"), 40),
        safe_int(record.get("like_count")),
        safe_int(record.get("likes")),
        safe_int(record.get("retweet_count")),
        safe_int(record.get("reply_count")),
        safe_int(record.get("quote_count")),
        safe_int(record.get("bookmark_count")),
    )
    return {
        "source": "birdclaw",
        "title": text[:160],
        "content": text,
        "url": url,
        "published_at": record.get("created_at") or record.get("createdAt") or record.get("date") or "",
        "velocity": velocity,
    }


def collect_birdclaw_export(env: dict[str, str], limit: int = 20) -> list[dict]:
    collected = []
    seen = set()
    for path in birdclaw_export_paths(env):
        if not path.exists():
            continue
        try:
            payload = read_json_or_jsonl(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"level": "warning", "collector": "birdclaw", "error": type(exc).__name__}))
            continue
        for record in extract_birdclaw_records(payload):
            normalized = normalize_birdclaw_record(record)
            if not normalized:
                continue
            key = normalized.get("url") or normalized.get("title")
            if key in seen:
                continue
            seen.add(key)
            collected.append(normalized)
            if len(collected) >= limit:
                return collected
    return collected


def x_influencer_handles(env: dict[str, str]) -> list[str]:
    raw = env.get("X_INFLUENCERS", "").strip()
    items = re.split(r"[\s,;]+", raw) if raw else DEFAULT_X_INFLUENCERS
    max_handles = safe_int(env.get("BREAKING_MAX_X_HANDLES"), len(DEFAULT_X_INFLUENCERS))
    handles = []
    seen = set()
    for item in items:
        handle = item.strip().lstrip("@")
        key = handle.lower()
        if handle and key not in seen:
            seen.add(key)
            handles.append(handle)
    return handles[:max(1, max_handles)]


def x_search_queries(env: dict[str, str]) -> list[str]:
    terms = env.get("BREAKING_X_QUERY", DEFAULT_X_INTEL_QUERY).strip()
    handles = x_influencer_handles(env)
    if not handles:
        return [terms]
    batch_size = max(1, safe_int(env.get("BREAKING_X_HANDLE_BATCH_SIZE"), 10))
    queries = []
    for index in range(0, len(handles), batch_size):
        batch = handles[index:index + batch_size]
        if len(batch) == 1:
            queries.append(f"from:{batch[0]} ({terms})")
            continue
        handle_filter = " OR ".join(f"from:{handle}" for handle in batch)
        queries.append(f"({handle_filter}) ({terms})")
    return queries


def x_search_commands(query: str) -> list[list[str]]:
    return [
        ["twitter", "search", query],
        ["opencli", "twitter", "search", query],
        ["bird", "search", query],
    ]


def normalize_x_record(record: dict, handle: str = "") -> dict | None:
    text = normalize_text(
        record.get("text")
        or record.get("full_text")
        or record.get("content")
        or record.get("title")
        or record.get("description")
        or ""
    )
    if not text:
        return None
    url = (
        record.get("url")
        or record.get("permalink")
        or record.get("link")
        or record.get("tweet_url")
        or ""
    )
    if not url and handle and record.get("id"):
        url = f"https://x.com/{handle}/status/{record.get('id')}"
    return {
        "source": "twitter",
        "title": text[:160],
        "content": text,
        "url": url,
        "published_at": record.get("created_at") or record.get("date") or "",
        "velocity": int(record.get("score") or record.get("likes") or record.get("like_count") or 40),
    }


def extract_json_records(payload) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "tweets", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return [payload]


def parse_x_cli_output(stdout: str, handle: str = "") -> list[dict]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        payload = None
    if payload is not None:
        return [
            normalized
            for record in extract_json_records(payload)
            for normalized in [normalize_x_record(record, handle)]
            if normalized
        ]

    records = []
    for line in stdout.splitlines():
        text = normalize_text(line)
        if not text:
            continue
        url_match = re.search(r"https?://(?:x\.com|twitter\.com)/[^\s)]+", text)
        records.append(
            {
                "source": "twitter",
                "title": text[:160],
                "content": text,
                "url": url_match.group(0) if url_match else "",
                "published_at": "",
                "velocity": 40,
            }
        )
    return records


def x_cli_env(env: dict[str, str]) -> dict[str, str]:
    command_env = os.environ.copy()
    command_env.update({key: value for key, value in env.items() if isinstance(value, str)})
    cookie = command_env.get("TWITTER_COOKIE", "").strip()
    if cookie:
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("auth_token="):
                command_env["TWITTER_AUTH_TOKEN"] = part[len("auth_token="):]
                command_env["AUTH_TOKEN"] = part[len("auth_token="):]
            elif part.startswith("ct0="):
                command_env["TWITTER_CT0"] = part[len("ct0="):]
                command_env["CT0"] = part[len("ct0="):]
    return command_env


def collect_x_cli(env: dict[str, str], limit: int = 20) -> list[dict]:
    collected = []
    command_env = x_cli_env(env)
    for query in x_search_queries(env):
        for command in x_search_commands(query):
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=45,
                    check=False,
                    env=command_env,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
            if completed.returncode != 0:
                continue
            handle_matches = re.findall(r"from:([A-Za-z0-9_]+)", query)
            handle = handle_matches[0] if len(handle_matches) == 1 else ""
            parsed = parse_x_cli_output(completed.stdout, handle)
            if parsed:
                collected.extend(parsed)
                break
        if len(collected) >= limit:
            break
    return collected[:limit]


def ai_intel_news_queries(env: dict[str, str]) -> list[str]:
    raw = env.get("BREAKING_NEWS_FALLBACK_QUERIES", "").strip()
    if not raw:
        return DEFAULT_AI_INTEL_NEWS_QUERIES
    queries = [item.strip() for item in re.split(r"\s*\|\|\s*", raw) if item.strip()]
    return queries or DEFAULT_AI_INTEL_NEWS_QUERIES


def collect_public_ai_intel_news(env: dict[str, str], limit: int = 20) -> list[dict]:
    if not truthy(env.get("BREAKING_ALLOW_NEWS_FALLBACK"), True):
        return []
    collected = []
    seen = set()
    per_query_limit = max(1, safe_int(env.get("BREAKING_NEWS_FALLBACK_PER_QUERY"), 5))
    for query in ai_intel_news_queries(env):
        encoded = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        request = urllib.request.Request(url, headers={"User-Agent": "AibriefAI/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = response.read(1_000_000)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            print(json.dumps({"level": "warning", "collector": "google-news", "error": type(exc).__name__}))
            continue
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            print(json.dumps({"level": "warning", "collector": "google-news", "error": type(exc).__name__}))
            continue
        added_for_query = 0
        for item in root.findall(".//item"):
            title = normalize_text(item.findtext("title", ""))
            link = normalize_text(item.findtext("link", ""))
            published_at = normalize_text(item.findtext("pubDate", ""))
            source_name = normalize_text(item.findtext("source", ""))
            if not title or not link:
                continue
            key = link or title.lower()
            if key in seen:
                continue
            seen.add(key)
            content = normalize_text(" ".join(part for part in (title, source_name, query) if part))
            collected.append(
                {
                    "source": "google-news",
                    "title": title[:160],
                    "content": content,
                    "url": link,
                    "published_at": published_at,
                    "velocity": 60,
                }
            )
            added_for_query += 1
            if len(collected) >= limit:
                return collected
            if added_for_query >= per_query_limit:
                break
    return collected


def collect_candidates(env: dict[str, str] | None = None) -> list[dict]:
    env = env or os.environ
    source_focus = env.get("BREAKING_SOURCE_FOCUS", "").strip().lower()
    candidates: list[dict] = []
    if source_focus in {"x", "twitter"}:
        candidates.extend(collect_birdclaw_export(env))
        candidates.extend(collect_x_cli(env))
        candidates.extend(collect_local_signals(source_focus=source_focus))
        if candidates:
            return candidates
    for collector in (collect_hackernews, collect_arxiv):
        try:
            candidates.extend(collector())
        except Exception as exc:
            print(json.dumps({"level": "warning", "collector": collector.__name__, "error": type(exc).__name__}))
    candidates.extend(collect_local_signals(source_focus=source_focus))
    return candidates


def should_keep_x_under_review(candidate: dict, env: dict[str, str], notify_mode: str) -> bool:
    if notify_mode != "website":
        return False
    keep = str(env.get("BREAKING_KEEP_X_REVIEW", "true")).strip().lower()
    if keep in {"0", "false", "no", "off"}:
        return False
    source_focus = env.get("BREAKING_SOURCE_FOCUS", "").strip().lower()
    source = str(candidate.get("source", "")).lower()
    urls = " ".join(candidate.get("source_urls") or [candidate.get("url", "")]).lower()
    return (
        source_focus in {"x", "twitter"}
        or source in {"birdclaw", "twitter", "x", "x/twitter"}
        or "x.com/" in urls
        or "twitter.com/" in urls
    )


def projected_monthly_runner_usage(cadence_minutes: int, run_seconds: float) -> dict:
    runs_per_month = (30 * 24 * 60) / max(cadence_minutes, 1)
    minutes_per_run = run_seconds / 60
    return {
        "cadence_minutes": cadence_minutes,
        "measured_seconds": round(run_seconds, 3),
        "projected_runs_per_30d": round(runs_per_month),
        "projected_minutes_per_30d": round(runs_per_month * minutes_per_run, 2),
    }


def run_monitor_cycle(
    *,
    raw_candidates: list[dict] | None = None,
    state_path: Path = STATE_PATH,
    public_status_path: Path = PUBLIC_STATUS_PATH,
    env: dict[str, str] | None = None,
    classify_func=None,
    notify_func=None,
    now: datetime | None = None,
) -> dict:
    started = time.monotonic()
    now = now or utc_now()
    env = env or os.environ
    classify_func = classify_func or classify_with_gemini
    notify_func = notify_func or send_breaking_notification
    max_candidates = int(env.get("BREAKING_MAX_CANDIDATES_PER_BATCH", str(DEFAULT_MAX_CANDIDATES)))
    min_confidence = float(env.get("BREAKING_MIN_CONFIDENCE", str(DEFAULT_MIN_CONFIDENCE)))
    cadence = int(env.get("BREAKING_CADENCE_MINUTES", str(DEFAULT_CADENCE_MINUTES)))
    notify_mode = env.get("BREAKING_NOTIFY_MODE", "website").strip().lower()

    state = load_state(state_path)
    prune_alerted(state, now)
    if notify_mode == "website":
        prune_irrelevant_x_intel(state, env)
    if notify_mode == "ntfy":
        retried = retry_pending_notifications(state, env, notify_func, now)
    else:
        retried = publish_pending_website_only(state, now)

    pending_reconsider = [
        entry.get("candidate")
        for entry in state.get("pending", {}).values()
        if isinstance(entry.get("candidate"), dict)
    ]
    news_fallback_collected = 0
    collected = raw_candidates if raw_candidates is not None else collect_candidates(env)
    clustered = cluster_story_candidates(pending_reconsider + collected)
    if notify_mode == "website":
        source_focus = env.get("BREAKING_SOURCE_FOCUS", "").strip().lower()
        survivors = [
            candidate
            for candidate in clustered
            if is_website_intel_candidate(candidate, env)
            or (source_focus not in {"x", "twitter"} and survives_stage1(candidate))
        ]
        if source_focus in {"x", "twitter"} and not survivors and raw_candidates is None:
            fallback = collect_public_ai_intel_news(env, limit=max_candidates)
            if fallback:
                news_fallback_collected = len(fallback)
                collected = collected + fallback
                clustered = cluster_story_candidates(pending_reconsider + collected)
                survivors = [
                    candidate
                    for candidate in clustered
                    if is_website_intel_candidate(candidate, env)
                    or (source_focus not in {"x", "twitter"} and survives_stage1(candidate))
                ]
    else:
        survivors = [candidate for candidate in clustered if survives_stage1(candidate)]

    fresh = [
        candidate
        for candidate in prioritize_candidates(survivors)
        if candidate["story_fingerprint"] not in state.get("alerted", {})
        and state.get("pending", {}).get(candidate["story_fingerprint"], {}).get("status") != "approved"
    ]
    batch = fresh[:max_candidates]
    overflow = fresh[max_candidates:]

    if notify_mode == "website":
        alerted_now = []
        for candidate in batch:
            publish_candidate_website_only(state, candidate, now)
            alerted_now.append(candidate["story_fingerprint"])
        elapsed = time.monotonic() - started
        summary = {
            "collected": len(collected),
            "clustered": len(clustered),
            "stage1_survivors": len(survivors),
            "x_intel_published": len(alerted_now),
            "news_fallback_collected": news_fallback_collected,
            "alerted_now": len(alerted_now),
            "pending_now": 0,
            "retried": retried,
            "overflow_pending": len(overflow),
            "runner_usage_projection": projected_monthly_runner_usage(cadence, elapsed),
        }
        save_state(state, state_path, now)
        write_public_status(state, summary, public_status_path)
        return summary

    for candidate in overflow:
        state["pending"][candidate["story_fingerprint"]] = {
            "status": "awaiting_classification",
            "candidate": public_candidate(candidate),
            "title": candidate.get("title", ""),
            "source_urls": candidate.get("source_urls", []),
            "last_seen_at": isoformat(now),
        }

    classifications, classification_reason = classify_func(batch, env)
    alerted_now = []
    pending_now = []
    malformed_or_rejected = 0
    by_id = {candidate["candidate_id"]: candidate for candidate in batch}
    classifier_unavailable = bool(batch) and not classifications and classification_reason != "classified"

    if classifier_unavailable:
        for candidate in batch:
            fingerprint = candidate["story_fingerprint"]
            state["pending"][fingerprint] = {
                "status": "awaiting_classification",
                "candidate": public_candidate(candidate),
                "title": candidate.get("title", ""),
                "source_urls": candidate.get("source_urls", []),
                "classification_reason": classification_reason,
                "last_seen_at": isoformat(now),
            }
            pending_now.append(fingerprint)

    for candidate_id, classification in classifications.items():
        candidate = by_id.get(candidate_id)
        if not candidate:
            malformed_or_rejected += 1
            continue
        fingerprint = candidate["story_fingerprint"]
        if not classification.get("breaking") or float(classification.get("confidence", 0)) < min_confidence:
            if should_keep_x_under_review(candidate, env, notify_mode):
                state["pending"][fingerprint] = {
                    "status": "awaiting_classification",
                    "candidate": public_candidate(candidate),
                    "title": candidate.get("title", ""),
                    "source_urls": candidate.get("source_urls", []),
                    "classification_reason": classification.get("reason") or "Not confirmed breaking yet.",
                    "last_seen_at": isoformat(now),
                }
                pending_now.append(fingerprint)
                continue
            state.get("pending", {}).pop(fingerprint, None)
            continue

        story = {
            **public_candidate(candidate),
            "alert": classification.get("alert") or candidate.get("title", ""),
            "reason": classification.get("reason", ""),
            "confidence": classification.get("confidence", 0),
        }
        if notify_mode == "ntfy":
            success, notification_reason = notify_func(story, env)
        else:
            success, notification_reason = True, "website-only"
        if success:
            state["alerted"][fingerprint] = {
                "alerted_at": isoformat(now),
                "last_seen_at": isoformat(now),
                "title": story.get("title", ""),
                "source_urls": story.get("source_urls", []),
                "confidence": story.get("confidence", 0),
                "notification_status": notification_reason,
                "reason": story.get("reason", ""),
            }
            state.get("pending", {}).pop(fingerprint, None)
            alerted_now.append(fingerprint)
        else:
            state["pending"][fingerprint] = {
                **story,
                "status": "approved",
                "notification_status": notification_reason,
                "last_seen_at": isoformat(now),
            }
            pending_now.append(fingerprint)

    if not classifier_unavailable:
        classified_ids = set(classifications.keys())
        for candidate in batch:
            if candidate["candidate_id"] not in classified_ids:
                malformed_or_rejected += 1

    elapsed = time.monotonic() - started
    summary = {
        "collected": len(collected),
        "clustered": len(clustered),
        "stage1_survivors": len(survivors),
        "classified": len(classifications),
        "classification_reason": classification_reason,
        "malformed_or_rejected": malformed_or_rejected,
        "alerted_now": len(alerted_now),
        "pending_now": len(pending_now),
        "retried": retried,
        "overflow_pending": len(overflow),
        "runner_usage_projection": projected_monthly_runner_usage(cadence, elapsed),
    }
    save_state(state, state_path, now)
    write_public_status(state, summary, public_status_path)
    return summary


def main() -> int:
    summary = run_monitor_cycle()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
