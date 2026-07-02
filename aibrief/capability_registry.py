from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_MAX_CAPABILITIES = 4
REQUIRED_FIELDS = {"id", "name", "type", "summary", "keywords", "triggers", "inputs", "outputs", "context"}
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-]*", re.IGNORECASE)

TASK_SYNONYMS = {
    "x": {"twitter", "tweet", "tweets", "post", "posts"},
    "twitter": {"x", "tweet", "tweets", "post", "posts"},
    "birdclaw": {"bird", "x", "twitter", "export"},
    "deploy": {"deployment", "render", "website", "hosting"},
    "deployment": {"deploy", "render", "website", "hosting"},
    "notification": {"notify", "ntfy", "digest", "alert"},
    "notify": {"notification", "ntfy", "digest", "alert"},
    "secret": {"secrets", "token", "cookie", "key"},
    "secrets": {"secret", "token", "cookie", "key"},
    "workflow": {"actions", "github", "cron", "schedule"},
    "actions": {"workflow", "github", "cron", "schedule"},
    "fresh": {"freshness", "stale", "health"},
    "stale": {"freshness", "fresh", "health"},
}


@dataclass(frozen=True)
class CapabilityMatch:
    capability: dict
    score: int
    matched_terms: tuple[str, ...]

    def as_context_item(self) -> dict:
        return {
            "id": self.capability["id"],
            "name": self.capability["name"],
            "type": self.capability["type"],
            "summary": self.capability["summary"],
            "inputs": self.capability["inputs"],
            "outputs": self.capability["outputs"],
            "context": self.capability["context"],
            "match_score": self.score,
            "matched_terms": list(self.matched_terms),
        }


def default_catalog_path() -> Path:
    return resources.files("aibrief").joinpath("capability_catalog.json")


def load_capability_catalog(path: str | Path | None = None) -> list[dict]:
    if path is None:
        with default_catalog_path().open("r", encoding="utf-8") as handle:
            catalog = json.load(handle)
    else:
        catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_capability_catalog(catalog)
    return catalog


def validate_capability_catalog(catalog: object) -> None:
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("capability catalog must be a non-empty list")
    seen_ids: set[str] = set()
    for index, item in enumerate(catalog):
        if not isinstance(item, dict):
            raise ValueError(f"capability #{index} must be an object")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"capability #{index} missing fields: {sorted(missing)}")
        capability_id = str(item["id"]).strip()
        if not capability_id:
            raise ValueError(f"capability #{index} has empty id")
        if capability_id in seen_ids:
            raise ValueError(f"duplicate capability id: {capability_id}")
        seen_ids.add(capability_id)
        for field in ("keywords", "triggers", "inputs", "outputs"):
            if not isinstance(item[field], list) or not all(isinstance(value, str) for value in item[field]):
                raise ValueError(f"capability {capability_id} field {field} must be a list of strings")
        for field in ("name", "type", "summary", "context"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"capability {capability_id} field {field} must be a non-empty string")


def tokenize(text: str) -> set[str]:
    tokens = {match.group(0).lower() for match in TOKEN_RE.finditer(text)}
    expanded = set(tokens)
    for token in tokens:
        expanded.update(TASK_SYNONYMS.get(token, set()))
    return expanded


def capability_terms(capability: dict) -> set[str]:
    text_parts: list[str] = [
        capability["id"],
        capability["name"],
        capability["type"],
        capability["summary"],
        capability["context"],
    ]
    text_parts.extend(capability.get("keywords", []))
    text_parts.extend(capability.get("triggers", []))
    return tokenize(" ".join(text_parts))


def trigger_score(task_text: str, capability: dict) -> tuple[int, set[str]]:
    score = 0
    matched: set[str] = set()
    lowered = task_text.lower()
    for trigger in capability.get("triggers", []):
        normalized = trigger.strip().lower()
        if normalized and normalized in lowered:
            score += 12
            matched.update(tokenize(normalized))
    return score, matched


def keyword_score(task_terms: set[str], capability: dict) -> tuple[int, set[str]]:
    keyword_terms = tokenize(" ".join(capability.get("keywords", [])))
    trigger_terms = tokenize(" ".join(capability.get("triggers", [])))
    general_terms = capability_terms(capability)
    matched_keywords = task_terms & keyword_terms
    matched_triggers = task_terms & trigger_terms
    matched_general = task_terms & general_terms
    score = (len(matched_keywords) * 4) + (len(matched_triggers) * 3) + len(matched_general - matched_keywords - matched_triggers)
    return score, matched_keywords | matched_triggers | matched_general


def rank_capabilities(
    task: str,
    catalog: Sequence[dict] | None = None,
    *,
    max_capabilities: int = DEFAULT_MAX_CAPABILITIES,
    min_score: int = 2,
) -> list[CapabilityMatch]:
    catalog = list(catalog) if catalog is not None else load_capability_catalog()
    validate_capability_catalog(catalog)
    task_text = task.strip()
    task_terms = tokenize(task_text)
    matches: list[CapabilityMatch] = []
    for capability in catalog:
        phrase_score, phrase_terms = trigger_score(task_text, capability)
        token_score, token_terms = keyword_score(task_terms, capability)
        score = phrase_score + token_score
        if score >= min_score:
            matches.append(
                CapabilityMatch(
                    capability=capability,
                    score=score,
                    matched_terms=tuple(sorted(phrase_terms | token_terms)),
                )
            )
    matches.sort(key=lambda item: (-item.score, item.capability["id"]))
    return matches[: max(1, max_capabilities)]


def render_context_payload(matches: Iterable[CapabilityMatch | dict]) -> str:
    items = []
    for item in matches:
        if isinstance(item, CapabilityMatch):
            items.append(item.as_context_item())
        else:
            items.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["type"],
                    "summary": item["summary"],
                    "inputs": item["inputs"],
                    "outputs": item["outputs"],
                    "context": item["context"],
                }
            )
    return json.dumps({"capabilities": items}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def select_capability_context(
    task: str,
    catalog: Sequence[dict] | None = None,
    *,
    max_capabilities: int = DEFAULT_MAX_CAPABILITIES,
    min_score: int = 2,
) -> dict:
    catalog = list(catalog) if catalog is not None else load_capability_catalog()
    selected = rank_capabilities(task, catalog, max_capabilities=max_capabilities, min_score=min_score)
    payload = render_context_payload(selected)
    all_payload = render_context_payload(catalog)
    return {
        "task": task,
        "selected_count": len(selected),
        "catalog_count": len(catalog),
        "selected_capabilities": [match.as_context_item() for match in selected],
        "payload": payload,
        "payload_bytes": len(payload.encode("utf-8")),
        "all_payload_bytes": len(all_payload.encode("utf-8")),
    }
