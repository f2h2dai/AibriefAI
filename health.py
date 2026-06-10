from __future__ import annotations

import logging
import os
import socket
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urlparse

from aibrief.graph.state import Signal
from aibrief.utils.text import clean_text, stable_id, utc_now
from aibrief.utils.validation import safe_url, validate_limit

LOGGER = logging.getLogger(__name__)
DEFAULT_FEEDS = [
    "https://export.arxiv.org/rss/cs.AI",
    "https://hnrss.org/frontpage",
]
MAX_RSS_BYTES = 2_000_000
MAX_XML_CHARS = 2_500_000


class FeedFetchError(RuntimeError):
    """Raised when a feed cannot be fetched or parsed safely."""


def _source_from_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if "arxiv" in host:
        return "arxiv"
    if "ycombinator" in host or "hnrss" in host:
        return "hackernews"
    return "rss"


def _allow_local_feeds() -> bool:
    return os.getenv("AIBRIEF_ALLOW_LOCAL_FEEDS", "").strip().lower() in {"1", "true", "yes", "on"}


def fetch_url(url: str, timeout: int = 10, max_bytes: int = MAX_RSS_BYTES) -> str:
    """Fetch a small HTTPS feed with a size cap and a stable user agent."""
    safe = safe_url(url, require_https=True, allow_localhost=_allow_local_feeds())
    if not safe:
        raise FeedFetchError("unsupported, non-HTTPS, credentialed, private, or malformed feed URL")
    req = urllib.request.Request(
        safe,
        headers={
            "User-Agent": "Aibrief/0.3 (+https://example.invalid/aibrief)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        content_length = res.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise FeedFetchError("feed response exceeds maximum size")
        payload = res.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise FeedFetchError("feed response exceeded maximum size")
        return payload.decode("utf-8", errors="replace")


def _find_text(item: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        value = item.findtext(name)
        if value:
            return value
    for child in list(item):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and child.text:
            return child.text
    return ""


def _extract_link(item: ET.Element) -> str:
    link = _find_text(item, ("link",))
    if link:
        return link
    for child in list(item):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local == "link":
            href = child.attrib.get("href")
            if href:
                return href
    return ""


def parse_rss(xml_text: str, source: str, limit: int) -> list[Signal]:
    """Parse RSS/Atom XML into Signals with XML safety checks."""
    if len(xml_text) > MAX_XML_CHARS:
        raise FeedFetchError("feed XML exceeds maximum parse size")
    upper = xml_text[:4096].upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise FeedFetchError("unsafe XML declaration rejected")
    limit = validate_limit(limit)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise FeedFetchError(f"invalid XML feed: {exc}") from exc

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    signals: list[Signal] = []
    for item in items[:limit]:
        title = clean_text(_find_text(item, ("title",)) or "Untitled")
        link = clean_text(_extract_link(item))
        desc = clean_text(_find_text(item, ("description", "summary", "content")) or title)
        safe_link = safe_url(link)
        if not title or not safe_link:
            continue
        signals.append(
            Signal(
                id=stable_id(source, title, safe_link),
                source=source,
                title=title,
                content=desc,
                url=safe_link,
                topic="AI Intelligence",
                createdAt=utc_now(),
                evidenceUrls=[safe_link],
            )
        )
    return signals


def fetch_rss_signals(feeds: Iterable[str] | None = None, limit_per_feed: int = 5) -> list[Signal]:
    """Fetch optional live RSS feeds; failures are logged and seed data can fill gaps."""
    signals: list[Signal] = []
    limit = validate_limit(limit_per_feed)
    for feed in list(feeds or DEFAULT_FEEDS):
        safe_feed = safe_url(feed, require_https=True, allow_localhost=_allow_local_feeds())
        if not safe_feed:
            LOGGER.warning("skipping unsafe feed URL: %s", feed)
            continue
        source = _source_from_url(safe_feed)
        try:
            xml_text = fetch_url(safe_feed)
            signals.extend(parse_rss(xml_text, source=source, limit=limit))
        except (FeedFetchError, urllib.error.URLError, socket.timeout, TimeoutError, ValueError) as exc:
            LOGGER.warning("skipping feed %s: %s", safe_feed, exc)
            continue
    return signals
