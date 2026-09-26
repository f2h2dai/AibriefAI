"""Publication policy. Collector/model fields never grant editorial verification."""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

POLICY_VERSION = 1
REVIEW_PATH = Path(__file__).resolve().parents[1] / "config" / "editorial_reviews.json"


def safe_url(value):
    try:
        url = urlsplit(str(value or ""))
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            return ""
        host = url.hostname.lower().removeprefix("www.")
        if host in {"twitter.com", "x.com"}:
            host = "x.com"
            match = re.fullmatch(r"/[^/]+/status(?:es)?/(\d+)/?", url.path)
            if match:
                return f"https://x.com/i/status/{match[1]}"
        return urlunsplit((url.scheme, url.netloc.lower(), url.path.rstrip("/"), url.query, ""))
    except ValueError:
        return ""


def claim_key(signal):
    # Bind reviews to the exact claim wording AND original URL, never entity similarity.
    title = " ".join(str(signal.get("title") or signal.get("text") or "").split())
    url = safe_url(signal.get("url") or signal.get("source_url") or signal.get("primary_source_url"))
    return hashlib.sha256((url + "\n" + title).encode()).hexdigest()


def load_reviews():
    """Only this separately reviewed local file is trusted, never source payloads."""
    try:
        data = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (TypeError, ValueError):
        return None


def freshness(event_time, observation_time, now, max_age_hours=48):
    event, observed, current = map(parse_time, (event_time, observation_time, now))
    if not event or not observed or not current:
        return "unknown"
    if (event - current).total_seconds() > 600 or (observed - current).total_seconds() > 600 or (event - observed).total_seconds() > 600:
        return "invalid"
    return "stale" if max((current - event).total_seconds(), (current - observed).total_seconds()) > max_age_hours * 3600 else "fresh"


def is_saudi(signal):
    text = " ".join(str(signal.get(k) or "") for k in (
        "title", "content", "text", "reason", "brief_en", "brief_ar", "country", "region", "topic", "market"))
    return bool(re.search(r"\b(saudi|ksa|riyadh|jeddah|neom)\b|السعودي|الرياض|جدة|نيوم", text, re.I))


def source_tier(signal):
    try:
        url = urlsplit(str(signal.get("url") or signal.get("source_url") or ""))
        host = (url.hostname or "").lower().removeprefix("www.")
        if host in {"x.com", "twitter.com"}:
            return "commentary" if url.path.lower().startswith("/grok/") or signal.get("is_reply") or signal.get("in_reply_to_status_id") else "social"
        if host.endswith((".gov", ".gov.sa", ".edu")):
            return "institution"
        return "original" if host in {"reuters.com", "apnews.com", "arxiv.org"} else "unknown"
    except ValueError:
        return "unknown"


def normalize_signal(signal, *, reviews=(), observed_at=None):
    result = dict(signal)
    key = claim_key(signal)
    original = safe_url(signal.get("url") or signal.get("source_url") or signal.get("primary_source_url"))
    urls = [original]
    for field in ("source_urls", "evidence_urls"):
        if isinstance(signal.get(field), list):
            urls.extend(safe_url(url) for url in signal[field])
    urls = list(dict.fromkeys(url for url in urls if url))
    observed = signal.get("observed_at") or signal.get("shown_at") or signal.get("seen_at") or observed_at
    event = signal.get("event_time") or signal.get("source_published_at") or signal.get("sourcePublishedAt") or signal.get("published_at") or signal.get("createdAt")
    records, groups, primary = [], set(), False
    for url in urls:
        review = next((r for r in reviews if isinstance(r, dict) and r.get("claim_key") == key and safe_url(r.get("url")) == url), {})
        group = str(review.get("independence_group") or "").strip()
        reviewed = bool(review.get("reviewer") and parse_time(review.get("reviewed_at")))
        correction = safe_url(review.get("correction_url")) or None
        supports = reviewed and review.get("supports_claim") is True and bool(group) and not correction
        if supports:
            groups.add(group)
            primary |= review.get("primary") is True
        records.append({"original_url": url, "publisher": urlsplit(url).hostname,
                        "observation_time": observed if url == original else review.get("observation_time"),
                        "event_time": event if url == original else review.get("event_time"),
                        "confirmation_state": "reviewed_support" if supports else "unverified",
                        "independence_group": group if supports else None,
                        "reviewer": review.get("reviewer") if reviewed else None,
                        "primary": bool(supports and review.get("primary") is True),
                        "correction_url": correction})
    status = ("verified" if primary else "corroborated") if len(groups) >= 2 else "unverified"
    result.update(claim_key=key, evidence=records, evidence_status=status,
                  evidence_policy_version=POLICY_VERSION, observed_at=observed,
                  event_time=event, saudi_relevant=is_saudi(signal), source_tier=source_tier(signal))
    result["freshness"] = freshness(event, observed, observed_at or observed)
    # Preserve workflow status (held/approved/etc.) separately from claim status.
    try:
        score = float(signal.get("relevance_score", signal.get("score", 0)) or 0)
    except (TypeError, ValueError):
        score = 0
    score = score if math.isfinite(score) else 0
    cap = {"commentary": 20, "social": 60, "unknown": 75}.get(result["source_tier"], 100)
    result["relevance_score"] = score
    result["score"] = min(max(score, 0), cap)
    return result
