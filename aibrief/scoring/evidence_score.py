"""Evidence helpers that never fetch or invent corroboration."""

from __future__ import annotations

from urllib.parse import urlparse


PRIMARY_SOURCE_HOSTS = {
    "arxiv.org",
    "github.com",
    "x.com",
    "twitter.com",
}
PRIMARY_SOURCE_TYPES = {"arxiv", "github", "official", "twitter", "x"}


def unique_evidence_urls(signal: dict) -> list[str]:
    values = []
    values.extend(signal.get("evidence_urls") or [])
    values.extend(signal.get("source_urls") or [])
    if signal.get("url"):
        values.append(signal["url"])

    urls: list[str] = []
    for value in values:
        url = str(value or "").strip()
        if url.startswith(("https://", "http://")) and url not in urls:
            urls.append(url)
    return urls


def infer_primary_source_url(signal: dict) -> str | None:
    explicit = str(signal.get("primary_source_url") or "").strip()
    if explicit:
        return explicit

    source = str(signal.get("source") or "").strip().lower()
    url = str(signal.get("url") or "").strip()
    if not url:
        return None

    host = (urlparse(url).hostname or "").lower()
    if source in PRIMARY_SOURCE_TYPES or host in PRIMARY_SOURCE_HOSTS:
        return url
    return None


def evidence_inputs(signal: dict) -> tuple[int, str | None, float]:
    urls = unique_evidence_urls(signal)
    explicit_count = signal.get("evidence_count")
    count = max(len(urls), int(explicit_count or 0))
    primary_url = infer_primary_source_url(signal)
    score = min(100.0, count * 40.0 + (20.0 if primary_url else 0.0))
    return count, primary_url, score
